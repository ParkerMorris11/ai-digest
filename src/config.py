"""Configuration loading and validation for AI Digest."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


CONFIG_DIR = Path.home() / ".ai-digest"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULT_NICHE = (
    "AI consulting firm helping businesses implement AI tools and strategies, "
    "workflow automation, AI platforms, enterprise AI adoption, and AI strategy consulting"
)

_MODEL_SONNET = "claude-sonnet-4-6"
_MODEL_HAIKU  = "claude-haiku-4-5-20251001"


@dataclass
class Config:
    anthropic_api_key: str
    gmail_address: str
    gmail_app_password: str
    recipient_email: str
    consulting_niche: str = field(default=_DEFAULT_NICHE)
    default_model: str = field(default=_MODEL_HAIKU)
    sonnet_days: list = field(default_factory=lambda: [0])  # 0=Monday


class ConfigError(Exception):
    """Raised when required configuration values are missing."""


def load_config() -> Config:
    """Load configuration from ~/.ai-digest/config.json with env var fallbacks.

    Raises:
        ConfigError: If any required field is absent from both the config file
                     and the environment.
    """
    stored: dict = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as fh:
            stored = json.load(fh)

    def get(key: str, env_var: str, default: str = "") -> str:
        return stored.get(key) or os.environ.get(env_var) or default

    # Parse sonnet_days from config: supports list of ints or comma-separated string.
    raw_sonnet = stored.get("sonnet_days", [0])
    if isinstance(raw_sonnet, str):
        sonnet_days = [int(d.strip()) for d in raw_sonnet.split(",") if d.strip().isdigit()]
    elif isinstance(raw_sonnet, list):
        sonnet_days = [int(d) for d in raw_sonnet]
    else:
        sonnet_days = [0]

    config = Config(
        anthropic_api_key=get("anthropic_api_key", "ANTHROPIC_API_KEY"),
        gmail_address=get("gmail_address", "GMAIL_ADDRESS"),
        gmail_app_password=get("gmail_app_password", "GMAIL_APP_PASSWORD"),
        recipient_email=get("recipient_email", "DIGEST_RECIPIENT"),
        consulting_niche=get("consulting_niche", "DIGEST_NICHE", _DEFAULT_NICHE),
        default_model=get("default_model", "DIGEST_MODEL", _MODEL_HAIKU),
        sonnet_days=sonnet_days,
    )

    missing = [
        field_name
        for field_name, env_var in [
            ("anthropic_api_key", "ANTHROPIC_API_KEY"),
            ("gmail_address", "GMAIL_ADDRESS"),
            ("gmail_app_password", "GMAIL_APP_PASSWORD"),
            ("recipient_email", "DIGEST_RECIPIENT"),
        ]
        if not getattr(config, field_name)
    ]

    if missing:
        lines = "\n".join(f"  - {name}" for name in missing)
        raise ConfigError(
            f"Missing required configuration fields:\n{lines}\n\n"
            f"Set these in {CONFIG_FILE} or as environment variables.\n"
            "Run: python3 setup_config.py to configure interactively."
        )

    return config


def save_config(config: Config) -> None:
    """Persist a Config instance to ~/.ai-digest/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as fh:
        json.dump(
            {
                "anthropic_api_key": config.anthropic_api_key,
                "gmail_address": config.gmail_address,
                "gmail_app_password": config.gmail_app_password,
                "recipient_email": config.recipient_email,
                "consulting_niche": config.consulting_niche,
                "default_model": config.default_model,
                "sonnet_days": config.sonnet_days,
            },
            fh,
            indent=2,
        )
