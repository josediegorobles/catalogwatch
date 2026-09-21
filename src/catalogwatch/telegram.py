"""Optional Telegram delivery for change alerts. No third-party SDK: plain Bot API call."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .config import Settings
from .http import Fetcher

TELEGRAM_API = "https://api.telegram.org"
MAX_MESSAGE_CHARS = 3900


class TelegramError(RuntimeError):
    pass


def format_alert(store: str, changes: Sequence[Mapping[str, Any]], limit: int = 10) -> str:
    if not changes:
        return f"No changes detected for {store}"

    counts = Counter(str(change.get("change_type", "")) for change in changes)
    summary = ", ".join(f"{count} {name}" for name, count in sorted(counts.items()))
    lines = [f"CatalogWatch: {len(changes)} change(s) at {store}", summary, ""]
    for change in changes[:limit]:
        label = change.get("sku") or change.get("key")
        lines.append(
            f"- {change.get('title', '')} ({label}) {change.get('field', '')}: "
            f"{change.get('old_value', '')} -> {change.get('new_value', '')}"
        )
    if len(changes) > limit:
        lines.append(f"... and {len(changes) - limit} more (full list in changes.csv)")
    return "\n".join(lines)[:MAX_MESSAGE_CHARS]


def send_alert(text: str, settings: Settings, fetcher: Fetcher, dry_run: bool = False) -> bool:
    """Send a message to the configured chat. Returns True when Telegram accepted it."""
    if dry_run:
        print(f"[dry run] telegram alert would be sent:\n{text}")
        return False

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise TelegramError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set (see .env.example)")

    url = f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/sendMessage"
    payload = fetcher.get_json(
        url,
        params={
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        },
    )
    if isinstance(payload, dict) and payload.get("ok") is False:
        raise TelegramError(f"Telegram rejected the message: {payload.get('description', 'unknown error')}")
    return True
