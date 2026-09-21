"""Configuration: defaults, .env parsing and environment overrides.

Precedence: real environment > .env file > built-in defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

USER_AGENT = "catalogwatch/1.0 (+https://github.com/josediegorobles/catalogwatch)"


@dataclass(frozen=True)
class Settings:
    user_agent: str = USER_AGENT
    request_timeout: float = 20.0
    max_retries: int = 3
    retry_base_delay: float = 1.0
    page_delay: float = 0.3
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


def load_dotenv(path: Path) -> dict[str, str]:
    """Minimal KEY=VALUE reader. Blank lines, comments and malformed lines are ignored."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _number(source: Mapping[str, str], key: str, cast: Callable[[str], float], default: float) -> float:
    raw = source.get(key)
    if raw is None or raw == "":
        return default
    try:
        return cast(raw)
    except (TypeError, ValueError):
        return default


def load_settings(env: Mapping[str, str] | None = None, env_file: Path | None = None) -> Settings:
    """Build Settings from an explicit mapping, the process environment and/or a .env file."""
    explicit_env = env is not None
    merged: dict[str, str] = dict(os.environ) if env is None else dict(env)

    if env_file is None and not explicit_env:
        candidate = Path(".env")
        env_file = candidate if candidate.is_file() else None
    if env_file is not None:
        for key, value in load_dotenv(env_file).items():
            merged.setdefault(key, value)

    def text(key: str) -> str | None:
        value = merged.get(key)
        return value if value else None

    return Settings(
        user_agent=text("CATALOGWATCH_USER_AGENT") or USER_AGENT,
        request_timeout=_number(merged, "CATALOGWATCH_REQUEST_TIMEOUT", float, 20.0),
        max_retries=int(_number(merged, "CATALOGWATCH_MAX_RETRIES", float, 3)),
        retry_base_delay=_number(merged, "CATALOGWATCH_RETRY_BASE_DELAY", float, 1.0),
        page_delay=_number(merged, "CATALOGWATCH_PAGE_DELAY", float, 0.3),
        telegram_bot_token=text("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=text("TELEGRAM_CHAT_ID"),
    )
