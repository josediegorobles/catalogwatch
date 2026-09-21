from __future__ import annotations

from pathlib import Path

import pytest

from catalogwatch.config import load_settings
from catalogwatch.fleet import load_stores, run_fleet
from catalogwatch.history import connect, history_rows
from catalogwatch.http import Fetcher

from fakes import FakeClient, FakeResponse

OK = "https://shop.example.com"
BLOCKED = "https://blocked.example.com"


def product(price: str = "10.00", sku: str = "A1") -> dict:
    return {
        "products": [
            {
                "id": 1,
                "title": "Thing",
                "handle": "thing",
                "vendor": "V",
                "product_type": "T",
                "tags": [],
                "updated_at": "",
                "images": [],
                "variants": [
                    {
                        "id": 10,
                        "title": "Default",
                        "option1": "Default",
                        "option2": None,
                        "option3": None,
                        "sku": sku,
                        "price": price,
                        "compare_at_price": None,
                        "available": True,
                    }
                ],
            }
        ]
    }


def make_fetcher(pages_by_host: dict[str, dict]) -> Fetcher:
    lookup = {key.split("//")[-1].rstrip("/"): value for key, value in pages_by_host.items()}

    def route(url: str, params: dict | None = None) -> FakeResponse:
        host = url.split("/")[2]
        if host not in lookup:
            return FakeResponse(403, text="Forbidden")
        page = int((params or {}).get("page", 1))
        return FakeResponse(200, json_data=lookup[host] if page == 1 else {"products": []})

    return Fetcher(load_settings(env={}), client=FakeClient(route), sleep=lambda _: None, rand=lambda: 0.0)


def test_load_stores_ignores_comments_and_blanks(tmp_path: Path):
    path = tmp_path / "stores.txt"
    path.write_text(
        "# niche: nutrition\nhttps://a.example.com\n\n  https://b.example.com  \n# https://commented.example.com\n",
        encoding="utf-8",
    )
    assert load_stores(path) == ["https://a.example.com", "https://b.example.com"]


def test_run_fleet_records_history_and_survives_a_blocked_store(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    fetcher = make_fetcher({OK: product()})  # BLOCKED is not routed, so it answers 403

    result = run_fleet([OK, BLOCKED], fetcher, conn, observed_at="2026-09-21T07:00:00+00:00")

    assert result["stores_ok"] == 1
    assert result["stores_failed"] == 1
    assert result["changes"] == 1
    assert result["errors"][0][0] == BLOCKED
    assert len(history_rows(conn, OK)) == 1


def test_run_fleet_second_pass_reports_no_changes(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    fetcher = make_fetcher({OK: product()})

    first = run_fleet([OK], fetcher, conn, observed_at="2026-09-21T07:00:00+00:00")
    second = run_fleet([OK], fetcher, conn, observed_at="2026-09-22T07:00:00+00:00")

    assert first["changes"] == 1
    assert second["changes"] == 0
    assert second["stores_ok"] == 1


def test_run_fleet_reports_price_changes_per_store(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    run_fleet([OK], make_fetcher({OK: product("10.00")}), conn, observed_at="2026-09-21T07:00:00+00:00")
    result = run_fleet([OK], make_fetcher({OK: product("8.00")}), conn, observed_at="2026-09-22T07:00:00+00:00")

    assert result["changes"] == 1
    assert result["per_store"][OK]["changes"][0]["change_type"] == "price_changed"
    assert result["per_store"][OK]["changes"][0]["new_value"] == "8.00"


def test_run_fleet_raises_when_nothing_can_be_read(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    with pytest.raises(RuntimeError):
        run_fleet([BLOCKED], make_fetcher({}), conn, observed_at="2026-09-21T07:00:00+00:00")
