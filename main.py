#!/usr/bin/env python3
"""AI Digest — entry point.

Fetches the latest issues of The Rundown AI, TLDR AI, Superhuman AI, and
The Neuron, builds a curated digest via Claude, and emails it to the
configured recipient. A local copy is saved to ~/.ai-digest/digests/.

Usage:
    python3 main.py              # full run: fetch → digest → email
    python3 main.py --dry-run    # skip sending email; writes HTML to stdout
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from src.config import load_config, ConfigError, CONFIG_DIR
from src.fetchers import fetch_rundown_ai, fetch_tldr_ai, fetch_superhuman_ai, fetch_neuron_ai
from src.digest import build_digest
from src.email_template import render_html, render_plain_text
from src.mailer import send_email


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Digest — daily AI news curator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the digest but skip sending email. Writes HTML to stdout.",
    )
    args = parser.parse_args()

    logger.info("AI News Digest — %s", date.today().strftime("%B %d, %Y"))

    try:
        config = load_config()
    except ConfigError as exc:
        logger.error("%s", exc)
        return 1

    newsletters = {
        "The Rundown AI": fetch_rundown_ai(),
        "TLDR AI":        fetch_tldr_ai(),
        "Superhuman AI":  fetch_superhuman_ai(),
        "The Neuron":     fetch_neuron_ai(),
    }

    successful = sum(1 for v in newsletters.values() if v and len(v) > 100)
    if successful < 2:
        logger.error(
            "Only fetched %d/4 newsletters — not enough content to build a digest.",
            successful,
        )
        return 1
    logger.info("Fetched %d/4 newsletters.", successful)

    digest = build_digest(config, newsletters)
    if not digest:
        logger.error("Failed to build digest.")
        return 1

    today_str  = date.today().strftime("%B %d, %Y")
    html_body  = render_html(digest, today_str)
    plain_body = render_plain_text(digest, today_str)

    # Always save a local copy.
    digest_dir = CONFIG_DIR / "digests"
    digest_dir.mkdir(parents=True, exist_ok=True)
    iso = date.today().isoformat()
    (digest_dir / f"{iso}.txt").write_text(plain_body)
    (digest_dir / f"{iso}.html").write_text(html_body)
    logger.info("Saved digest to %s", digest_dir)

    if args.dry_run:
        logger.info("Dry run — skipping email. HTML written to stdout.")
        print(html_body)
        return 0

    subject = f"AI Digest — {today_str}"
    send_email(config, subject, html_body, plain_body)

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
