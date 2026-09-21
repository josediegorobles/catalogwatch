from __future__ import annotations

from pathlib import Path

from catalogwatch.config import load_dotenv, load_settings


def test_defaults_when_env_is_empty():
    settings = load_settings(env={})
    assert settings.max_retries == 3
    assert settings.request_timeout == 20.0
    assert settings.page_delay == 0.3
    assert settings.telegram_bot_token is None
    assert settings.telegram_chat_id is None
    assert "catalogwatch" in settings.user_agent.lower()


def test_env_overrides_defaults():
    settings = load_settings(
        env={
            "CATALOGWATCH_MAX_RETRIES": "5",
            "CATALOGWATCH_REQUEST_TIMEOUT": "7.5",
            "TELEGRAM_BOT_TOKEN": "123:abc",
            "TELEGRAM_CHAT_ID": "-100",
        }
    )
    assert settings.max_retries == 5
    assert settings.request_timeout == 7.5
    assert settings.telegram_bot_token == "123:abc"
    assert settings.telegram_chat_id == "-100"


def test_dotenv_file_is_parsed_and_os_env_wins(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nCATALOGWATCH_PAGE_DELAY=1.25\n\nTELEGRAM_CHAT_ID=from-file\nMALFORMED LINE\n",
        encoding="utf-8",
    )
    parsed = load_dotenv(env_file)
    assert parsed["CATALOGWATCH_PAGE_DELAY"] == "1.25"
    assert parsed["TELEGRAM_CHAT_ID"] == "from-file"
    assert "MALFORMED LINE" not in parsed

    settings = load_settings(env={"TELEGRAM_CHAT_ID": "from-env"}, env_file=env_file)
    assert settings.page_delay == 1.25
    assert settings.telegram_chat_id == "from-env"


def test_invalid_numbers_fall_back_to_defaults():
    settings = load_settings(env={"CATALOGWATCH_MAX_RETRIES": "not-a-number"})
    assert settings.max_retries == 3
