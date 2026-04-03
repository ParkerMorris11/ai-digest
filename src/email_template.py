"""HTML and plain-text email rendering for AI Digest.

The HTML template is defined as a single readable skeleton with named
{placeholders}. All dynamic content is assembled into those placeholders before
a single .format() call — no scattered f-string concatenation.

Design principles:
  - Warm off-white background, near-black type, teal as the sole accent
  - Table-based layout for broad email client compatibility
  - Stories separated by thin rules, not cards or colored boxes
  - Generous whitespace; 560 px max width
  - No emoji, no heavy gradients, no dark header bars

v2 additions:
  - Per-story tag pills with a muted color palette
  - Mini table-of-contents at the top linking to sections
  - Model indicator in footer (Haiku vs Sonnet)
"""


# ── Palette and type ──────────────────────────────────────────────────────────

_BG          = "#F7F6F2"
_TEXT        = "#28251D"
_SECONDARY   = "#7A7974"
_MUTED       = "#BAB9B4"
_RULE        = "#D4D1CA"
_RULE_LIGHT  = "#E8E7E3"
_CARD_BG     = "#FBFBF9"
_TEAL        = "#01696F"
_FONT_STACK  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


# ── Tag pill color map ────────────────────────────────────────────────────────
#  Each tag gets a (text-color, background-color) pair — all deliberately muted
#  so they don't overpower the score badge.

_TAG_COLORS = {
    "tools":          ("#4A6741", "#E8F0E5"),
    "research":       ("#5B4A8A", "#EEEAF5"),
    "infrastructure": ("#6B5B3A", "#F2EDE3"),
    "funding":        ("#2A6B5C", "#E0F2ED"),
    "policy":         ("#8A4A4A", "#F5E8E8"),
    "product":        ("#3A5A8A", "#E3EDF5"),
    "strategy":       ("#7A5A2A", "#F5EFE0"),
    "automation":     ("#01696F", "#E3F1F2"),
    "open-source":    ("#5A6A4A", "#ECF0E6"),
    "enterprise":     ("#4A5A6A", "#E6ECF0"),
    "general":        ("#7A7974", "#EFEFED"),
}


# ── HTML skeleton ─────────────────────────────────────────────────────────────

_HTML_SKELETON = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Digest &mdash; {date_string}</title>
</head>
<body style="margin:0; padding:0; background-color:{bg}; font-family:{font_stack}; -webkit-font-smoothing:antialiased;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{bg};">
    <tr>
      <td align="center" style="padding:40px 16px 48px;">

        <!-- Content column -->
        <table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;">

          <!-- ── Masthead ── -->
          <tr>
            <td style="padding:0 0 28px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td valign="bottom">
                    <p style="margin:0 0 10px 0; font-size:11px; font-weight:600; color:{muted}; letter-spacing:2.5px; text-transform:uppercase;">AI Digest</p>
                    <p style="margin:0; font-size:28px; font-weight:700; color:{text}; letter-spacing:-0.5px; line-height:1.2;">{date_string}</p>
                  </td>
                  <td valign="bottom" align="right" style="font-size:12px; color:{muted}; white-space:nowrap; padding-bottom:2px;">
                    {story_count} stories &middot; <span style="color:{teal}; font-weight:600;">{relevant_count} relevant</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 0 24px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="height:1px; background-color:{rule}; font-size:0; line-height:0;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- ── Table of Contents ── -->
          <tr>
            <td style="padding:0 0 28px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background-color:{card_bg}; border:1px solid {rule_light}; border-radius:8px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="font-size:10px; font-weight:700; color:{secondary}; letter-spacing:2px; text-transform:uppercase; padding-bottom:10px;">
                          In This Issue
                        </td>
                      </tr>
                      {toc_rows}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ── Top stories label ── -->
          <tr>
            <td style="padding:0 0 20px 0;">
              <span style="font-size:10px; font-weight:700; color:{secondary}; letter-spacing:2px; text-transform:uppercase;">Top Stories</span>
            </td>
          </tr>

          <!-- ── Top stories ── -->
          <tr>
            <td>
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {top_stories_rows}
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:36px 0 32px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="height:1px; background-color:{rule}; font-size:0; line-height:0;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- ── Quick scan label ── -->
          <tr>
            <td style="padding:0 0 12px 0;">
              <span style="font-size:10px; font-weight:700; color:{secondary}; letter-spacing:2px; text-transform:uppercase;">Quick Scan</span>
            </td>
          </tr>

          <!-- ── Quick scan ── -->
          <tr>
            <td>
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {quick_scan_rows}
              </table>
            </td>
          </tr>

          <!-- Spacer -->
          <tr><td style="height:32px; font-size:0; line-height:0;">&nbsp;</td></tr>

          <!-- ── Action items card ── -->
          <tr>
            <td>
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background-color:{card_bg}; border:1px solid {rule_light}; border-radius:8px;">
                <tr>
                  <td style="padding:24px 28px 20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="padding:0 0 16px 0; font-size:10px; font-weight:700; color:{teal}; letter-spacing:2px; text-transform:uppercase;">
                          Action Items
                        </td>
                      </tr>
                      {action_items_rows}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ── Footer ── -->
          <tr>
            <td style="padding:36px 0 0 0; text-align:center;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="height:1px; background-color:{rule_light}; font-size:0; line-height:0; margin-bottom:20px;">&nbsp;</td></tr>
              </table>
              <p style="margin:16px 0 0; font-size:11px; color:{muted};">
                Curated by Claude{model_label} &middot; Filtered for your consulting practice
              </p>
            </td>
          </tr>

        </table>
        <!-- /content column -->

      </td>
    </tr>
  </table>

</body>
</html>"""


# ── Row fragment templates ────────────────────────────────────────────────────

_TAG_PILL = (
    '<span style="display:inline-block; font-size:10px; font-weight:600; '
    'color:{tag_fg}; background:{tag_bg}; padding:2px 8px; border-radius:3px; '
    'letter-spacing:0.3px; margin-right:5px;">{tag_label}</span>'
)

_STORY_ROW_FIRST = """\
<tr>
  <td style="padding:0 0 24px 0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:0 0 10px 0;">{score_badge} {tag_pills}</td></tr>
      <tr><td style="font-size:17px; font-weight:600; color:{text}; line-height:1.35; padding:0 0 7px 0;">{headline}</td></tr>
      <tr><td style="font-size:13px; color:{teal}; line-height:1.5; padding:0 0 9px 0;">{why_it_matters}</td></tr>
      <tr><td style="font-size:14px; color:{secondary}; line-height:1.65; padding:0 0 8px 0;">{summary}</td></tr>
      <tr><td style="font-size:11px; color:{muted}; letter-spacing:0.2px;">{sources}</td></tr>
    </table>
  </td>
</tr>"""

_STORY_ROW = """\
<tr>
  <td style="padding:24px 0 24px 0; border-top:1px solid {rule_light};">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:0 0 10px 0;">{score_badge} {tag_pills}</td></tr>
      <tr><td style="font-size:17px; font-weight:600; color:{text}; line-height:1.35; padding:0 0 7px 0;">{headline}</td></tr>
      <tr><td style="font-size:13px; color:{teal}; line-height:1.5; padding:0 0 9px 0;">{why_it_matters}</td></tr>
      <tr><td style="font-size:14px; color:{secondary}; line-height:1.65; padding:0 0 8px 0;">{summary}</td></tr>
      <tr><td style="font-size:11px; color:{muted}; letter-spacing:0.2px;">{sources}</td></tr>
    </table>
  </td>
</tr>"""

_QUICK_SCAN_ROW = """\
<tr>
  <td style="padding:10px 0; border-bottom:1px solid {rule_ultralight};">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td style="font-size:13px; line-height:1.55; color:{text};">
          <span style="font-weight:600;">{headline}</span>
          <span style="color:{muted};"> &mdash; </span>
          <span style="color:{secondary};">{one_liner}</span>
          <br>{tag_pills}
        </td>
        <td width="90" align="right" valign="top" style="font-size:11px; color:{muted}; white-space:nowrap; padding-left:14px;">
          {source}
        </td>
      </tr>
    </table>
  </td>
</tr>"""

_ACTION_ROW = """\
<tr>
  <td style="padding:6px 0; font-size:14px; color:{text}; line-height:1.65;">
    <span style="color:{teal}; font-weight:600; margin-right:7px;">&#8250;</span>{item}
  </td>
</tr>"""

_TOC_ROW = """\
<tr>
  <td style="padding:3px 0; font-size:13px; color:{text}; line-height:1.5;">
    <span style="color:{teal}; font-weight:600; margin-right:6px;">&#8250;</span>{headline}
    <span style="color:{muted}; font-size:11px; margin-left:4px;">{score}/5</span>
  </td>
</tr>"""

_SCORE_BADGE = (
    '<span style="display:inline-block; background:{badge_bg}; color:{badge_fg}; '
    'font-size:11px; font-weight:600; padding:2px 9px; border-radius:4px; '
    'letter-spacing:0.3px;">{score}/5</span>'
)

# Score 5 always uses teal; lower scores step through neutral tones.
_BADGE_COLORS = {
    5: ("#FFFFFF", _TEAL),        # white text on teal
    4: (_TEAL,     "#E3F1F2"),    # teal text on pale teal
    3: ("#6B4F2A", "#F5EDE3"),
    2: (_SECONDARY, "#EFEFED"),
    1: (_MUTED,    "#F7F6F2"),
}


# ── Assembly helpers ──────────────────────────────────────────────────────────

def _score_badge(score: int) -> str:
    badge_fg, badge_bg = _BADGE_COLORS.get(score, (_SECONDARY, "#EFEFED"))
    return _SCORE_BADGE.format(
        badge_bg=badge_bg,
        badge_fg=badge_fg,
        score=score,
    )


def _tag_pills(tags: list[str]) -> str:
    """Render a row of small colored pills for story tags."""
    pills = []
    for tag in tags[:2]:  # max 2 tags
        fg, bg = _TAG_COLORS.get(tag, ("#7A7974", "#EFEFED"))
        pills.append(_TAG_PILL.format(tag_fg=fg, tag_bg=bg, tag_label=tag))
    return " ".join(pills)


def _build_toc_rows(stories: list[dict]) -> str:
    """Build a mini table-of-contents from top stories."""
    rows = [
        _TOC_ROW.format(
            headline=story.get("headline", ""),
            score=story.get("score", 3),
            text=_TEXT,
            teal=_TEAL,
            muted=_MUTED,
        )
        for story in stories[:6]  # cap TOC at 6 items
    ]
    return "\n".join(rows)


def _build_top_stories_rows(stories: list[dict]) -> str:
    rows: list[str] = []
    for i, story in enumerate(stories):
        template = _STORY_ROW_FIRST if i == 0 else _STORY_ROW
        rows.append(
            template.format(
                score_badge=_score_badge(story.get("score", 3)),
                tag_pills=_tag_pills(story.get("tags", [])),
                headline=story.get("headline", ""),
                why_it_matters=story.get("why_it_matters", ""),
                summary=story.get("summary", ""),
                sources=" &middot; ".join(story.get("sources", [])),
                text=_TEXT,
                teal=_TEAL,
                secondary=_SECONDARY,
                muted=_MUTED,
                rule_light=_RULE_LIGHT,
            )
        )
    return "\n".join(rows)


def _build_quick_scan_rows(items: list[dict]) -> str:
    rows = [
        _QUICK_SCAN_ROW.format(
            headline=item.get("headline", ""),
            one_liner=item.get("one_liner", ""),
            tag_pills=_tag_pills(item.get("tags", [])),
            source=item.get("source", ""),
            text=_TEXT,
            secondary=_SECONDARY,
            muted=_MUTED,
            rule_ultralight="#F0EFEB",
        )
        for item in items
    ]
    return "\n".join(rows)


def _build_action_rows(items: list[str]) -> str:
    rows = [
        _ACTION_ROW.format(item=item, text=_TEXT, teal=_TEAL)
        for item in items
    ]
    return "\n".join(rows)


def _model_label(digest: dict) -> str:
    """Return a short model label for the footer, or empty string."""
    model = digest.get("_model", "")
    if "sonnet" in model:
        return " (Sonnet)"
    elif "haiku" in model:
        return " (Haiku)"
    return ""


# ── Public API ────────────────────────────────────────────────────────────────

def render_html(digest: dict, date_string: str) -> str:
    """Render *digest* as a formatted HTML email string.

    Falls back to a minimal pre-formatted view when *digest* contains only a
    ``raw_text`` key (i.e. when JSON parsing of the Claude response failed).
    """
    if "raw_text" in digest:
        return (
            f'<html><body style="font-family:{_FONT_STACK}; padding:32px; '
            f'background:{_BG}; color:{_TEXT};">'
            f'<pre style="white-space:pre-wrap; font-family:inherit;">'
            f'{digest["raw_text"]}</pre></body></html>'
        )

    top_stories  = digest.get("top_stories", [])
    quick_scan   = digest.get("quick_scan", [])
    action_items = digest.get("action_items", [])

    story_count    = len(top_stories) + len(quick_scan)
    relevant_count = sum(1 for s in top_stories if s.get("score", 0) >= 4)

    return _HTML_SKELETON.format(
        date_string=date_string,
        story_count=story_count,
        relevant_count=relevant_count,
        toc_rows=_build_toc_rows(top_stories),
        top_stories_rows=_build_top_stories_rows(top_stories),
        quick_scan_rows=_build_quick_scan_rows(quick_scan),
        action_items_rows=_build_action_rows(action_items),
        model_label=_model_label(digest),
        bg=_BG,
        text=_TEXT,
        secondary=_SECONDARY,
        muted=_MUTED,
        teal=_TEAL,
        rule=_RULE,
        rule_light=_RULE_LIGHT,
        card_bg=_CARD_BG,
        font_stack=_FONT_STACK,
    )


def render_plain_text(digest: dict, date_string: str) -> str:
    """Render *digest* as a plain-text email string."""
    if "raw_text" in digest:
        return digest["raw_text"]

    lines = [
        f"AI NEWS DIGEST — {date_string}",
        "Sources: The Rundown AI | Superhuman AI | TLDR AI | The Neuron",
        "=" * 56,
        "",
        "IN THIS ISSUE",
    ]
    for story in digest.get("top_stories", [])[:6]:
        lines.append(f"  › {story.get('headline', '')}  ({story.get('score', '')}/5)")
    lines += ["", "=" * 56, "", "TOP STORIES", ""]

    for story in digest.get("top_stories", []):
        rank    = story.get("rank", "")
        score   = story.get("score", "")
        tags    = ", ".join(story.get("tags", []))
        sources = ", ".join(story.get("sources", []))
        lines += [
            f"[#{rank}] {story.get('headline', '')}  ({score}/5)  [{tags}]",
            f"  > {story.get('why_it_matters', '')}",
            f"  {story.get('summary', '')}",
            f"  — {sources}",
            "",
        ]

    lines += ["-" * 56, "QUICK SCAN", ""]
    for item in digest.get("quick_scan", []):
        tags = ", ".join(item.get("tags", []))
        lines.append(
            f"  - {item.get('headline', '')} — {item.get('one_liner', '')} "
            f"[{tags}] ({item.get('source', '')}, {item.get('score', '')}/5)"
        )

    lines += ["", "-" * 56, "ACTION ITEMS", ""]
    for item in digest.get("action_items", []):
        lines.append(f"  › {item}")

    model = digest.get("_model", "")
    if model:
        short = "Sonnet" if "sonnet" in model else "Haiku" if "haiku" in model else model
        lines += ["", f"— Curated by Claude ({short})"]

    return "\n".join(lines)
