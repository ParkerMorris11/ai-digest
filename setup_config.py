#!/usr/bin/env python3
"""Interactive configuration setup for AI Digest.

Prompts for required credentials and preferences, then writes them to
~/.ai-digest/config.json.
"""

import sys
from dataclasses import fields

from src.config import Config, save_config, CONFIG_FILE, _DEFAULT_NICHE


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    """Prompt the user for a value, optionally masking input for secrets."""
    if secret:
        import getpass
        suffix = " (hidden): " if not default else f" [keep existing] (hidden): "
        value = getpass.getpass(f"  {label}{suffix}")
    else:
        suffix = ": " if not default else f" [{default}]: "
        value = input(f"  {label}{suffix}").strip()

    return value if value else default


def main() -> int:
    print("\nAI Digest — Configuration Setup")
    print("=" * 40)
    print(f"Settings will be saved to: {CONFIG_FILE}\n")

    # Load any existing values so the user can press Enter to keep them.
    existing: dict = {}
    if CONFIG_FILE.exists():
        import json
        with open(CONFIG_FILE) as fh:
            existing = json.load(fh)
        print("Existing configuration found. Press Enter to keep current values.\n")

    anthropic_api_key = _prompt(
        "Anthropic API key",
        default=existing.get("anthropic_api_key", ""),
        secret=True,
    )
    if not anthropic_api_key:
        print("\nError: Anthropic API key is required.")
        return 1

    gmail_address = _prompt(
        "Gmail address",
        default=existing.get("gmail_address", ""),
    )
    if not gmail_address:
        print("\nError: Gmail address is required.")
        return 1

    gmail_app_password = _prompt(
        "Gmail App Password",
        default=existing.get("gmail_app_password", ""),
        secret=True,
    )
    if not gmail_app_password:
        print("\nError: Gmail App Password is required.")
        return 1

    recipient_email = _prompt(
        "Recipient email",
        default=existing.get("recipient_email", gmail_address),
    )
    if not recipient_email:
        print("\nError: Recipient email is required.")
        return 1

    print(
        "\n  Consulting niche description\n"
        "  (Describe your practice so Claude knows what's relevant)\n"
        f"  Default: {_DEFAULT_NICHE}"
    )
    consulting_niche = _prompt(
        "Niche",
        default=existing.get("consulting_niche", _DEFAULT_NICHE),
    )

    config = Config(
        anthropic_api_key=anthropic_api_key,
        gmail_address=gmail_address,
        gmail_app_password=gmail_app_password,
        recipient_email=recipient_email,
        consulting_niche=consulting_niche,
    )
    save_config(config)

    print(f"\nConfiguration saved to {CONFIG_FILE}")
    print("Run `python3 main.py` to generate your first digest.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
