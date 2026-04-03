"""Claude API integration: building and parsing the daily digest.

Supports a two-tier model strategy — defaults to Haiku on most days and
automatically upgrades to Sonnet on configurable "deep-dive" days (Monday by
default).  Each story is tagged for quick visual scanning.
"""

import json
import logging
import re
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Config, _MODEL_SONNET
from .fetchers import SSL_CONTEXT


logger = logging.getLogger(__name__)

_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_MAX_TOKENS = 4096
_NEWSLETTER_CHAR_LIMIT = 8000

# ── Valid tags for per-story classification ────────────────────────────────────

_VALID_TAGS = {
    "tools", "research", "infrastructure", "funding", "policy",
    "product", "strategy", "automation", "open-source", "enterprise",
}

_SYSTEM_PROMPT_TEMPLATE = """\
You are an AI news curator for a professional building an {niche}.

Extract every distinct news story from the newsletters. Deduplicate stories across sources.
Score each story 1–5 on relevance:
  5 = Directly actionable for AI consulting
  4 = Highly relevant (platform updates, enterprise AI, automation)
  3 = Moderately relevant (research with business implications, funding)
  2 = Tangentially relevant (general AI, consumer)
  1 = Low relevance (entertainment, niche research)

Assign 1–2 tags to each story from this list:
  tools, research, infrastructure, funding, policy, product, strategy, automation, open-source, enterprise

You MUST respond with valid JSON only. No text before or after the JSON.

{{
  "top_stories": [
    {{
      "rank": 1,
      "headline": "...",
      "score": 5,
      "tags": ["tools", "enterprise"],
      "why_it_matters": "One sentence on relevance to AI consulting",
      "summary": "2-3 sentence summary",
      "sources": ["The Rundown AI", "Superhuman AI"]
    }}
  ],
  "quick_scan": [
    {{
      "headline": "...",
      "one_liner": "One line summary",
      "score": 2,
      "tags": ["research"],
      "source": "Newsletter name"
    }}
  ],
  "action_items": [
    "Specific action item based on today's news"
  ]
}}

top_stories = stories scored 3–5, ranked by score then impact.
quick_scan  = stories scored 1–2.
action_items = 2–3 specific consulting actions.\
"""


def _select_model(config: Config) -> str:
    """Pick today's model based on the day of the week.

    If today's weekday (Monday=0 … Sunday=6) is in ``config.sonnet_days``,
    use Sonnet; otherwise fall back to ``config.default_model``.
    """
    today_weekday = date.today().weekday()
    if today_weekday in config.sonnet_days:
        model = _MODEL_SONNET
    else:
        model = config.default_model
    logger.info("Model for today (%s): %s", date.today().strftime("%A"), model)
    return model


def _call_claude(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Send a request to the Claude Messages API and return the text response."""
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": _MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    ).encode("utf-8")

    req = Request(
        _CLAUDE_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urlopen(req, timeout=120, context=SSL_CONTEXT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        logger.error("Claude API returned HTTP %s: %s", exc.code, body)
    except (URLError, TimeoutError) as exc:
        logger.error("Claude API request failed: %s", exc)

    return ""


def _parse_json(raw: str) -> dict:
    """Extract and parse a JSON object from *raw*, with a regex fallback."""
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("JSON parse failed; storing raw text in digest.")
            return {"raw_text": raw}
    return {"raw_text": raw} if raw else {}


def _sanitize_tags(tags: list) -> list[str]:
    """Keep only recognized tags; fall back to ['general'] if empty."""
    cleaned = [t.lower().strip() for t in tags if isinstance(t, str)]
    valid = [t for t in cleaned if t in _VALID_TAGS]
    return valid if valid else ["general"]


def build_digest(config: Config, newsletter_contents: dict[str, str]) -> dict:
    """Combine newsletter text, call Claude, and return a structured digest dict.

    Returns an empty dict if there is insufficient source material or if the
    API call fails.
    """
    combined = ""
    for source, content in newsletter_contents.items():
        if content and len(content) > 100:
            combined += f"\n\n=== {source} ===\n{content[:_NEWSLETTER_CHAR_LIMIT]}\n"

    if len(combined) < 200:
        logger.error("Insufficient newsletter content to build a digest.")
        return {}

    model = _select_model(config)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(niche=config.consulting_niche)
    user_prompt = (
        f"Today is {date.today().strftime('%B %d, %Y')}. "
        f"Here are the newsletters:\n{combined}"
    )

    logger.info("Calling Claude (%s) to build digest...", model)
    raw = _call_claude(config.anthropic_api_key, model, system_prompt, user_prompt)
    digest = _parse_json(raw) if raw else {}

    # Sanitize tags on returned stories.
    for story in digest.get("top_stories", []):
        story["tags"] = _sanitize_tags(story.get("tags", []))
    for item in digest.get("quick_scan", []):
        item["tags"] = _sanitize_tags(item.get("tags", []))

    # Store which model was used so the email template can display it.
    if digest and "raw_text" not in digest:
        digest["_model"] = model

    return digest
