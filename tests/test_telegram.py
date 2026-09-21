from __future__ import annotations

import pytest

from catalogwatch.config import load_settings
from catalogwatch.http import Fetcher
from catalogwatch.telegram import TelegramError, format_alert, send_alert

from fakes import FakeClient, FakeResponse


def change(change_type: str, key: str, old: str, new: str) -> dict:
    return {
        "change_type": change_type,
        "key": key,
        "sku": key.split("::")[-1],
        "title": key.split("::")[0],
        "field": "price",
        "old_value": old,
        "new_value": new,
    }


def test_format_alert_summarises_changes():
    diffs = [
        change("price_changed", "tee::T1", "22.00", "19.00"),
        change("stock_changed", "mug::M1", "true", "false"),
        change("added", "cap::C1", "", "15.00"),
    ]
    text = format_alert("https://shop.example.com", diffs)
    assert "shop.example.com" in text
    assert "3" in text
    assert "T1" in text and "19.00" in text
    assert "22.00" in text


def test_format_alert_truncates_long_batches():
    diffs = [change("price_changed", f"p{i}::S{i}", "1.00", "0.90") for i in range(200)]
    text = format_alert("https://shop.example.com", diffs, limit=5)
    assert len(text) < 4000
    assert "S0" in text
    assert "S199" not in text


def test_format_alert_handles_empty_batch():
    text = format_alert("https://shop.example.com", [])
    assert "no changes" in text.lower()


def test_missing_token_raises():
    settings = load_settings(env={})
    fetcher = Fetcher(settings, client=FakeClient([]), sleep=lambda _: None)
    with pytest.raises(TelegramError):
        send_alert("hello", settings, fetcher)


def test_dry_run_never_calls_the_api():
    settings = load_settings(env={"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "c"})
    client = FakeClient([])
    fetcher = Fetcher(settings, client=client, sleep=lambda _: None)
    assert send_alert("hello", settings, fetcher, dry_run=True) is False
    assert client.calls == []


def test_send_alert_posts_to_bot_api():
    settings = load_settings(env={"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_CHAT_ID": "-100"})
    client = FakeClient([FakeResponse(200, json_data={"ok": True})])
    fetcher = Fetcher(settings, client=client, sleep=lambda _: None)

    assert send_alert("hello", settings, fetcher) is True
    call = client.calls[0]
    assert call["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert call["params"]["chat_id"] == "-100"
    assert call["params"]["text"] == "hello"
    assert call["params"]["disable_web_page_preview"] == "true"
