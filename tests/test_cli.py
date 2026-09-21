from __future__ import annotations

import csv
from pathlib import Path

import pytest

from catalogwatch.cli import main
from catalogwatch.config import load_settings
from catalogwatch.http import Fetcher

from fakes import FakeClient, FakeResponse

STORE = "https://shop.example.com"


def shopify_fetcher(pages):
    def route(url, params):
        page = int((params or {}).get("page", 1))
        return FakeResponse(200, json_data=pages.get(page, {"products": []}))

    return Fetcher(load_settings(env={}), client=FakeClient(route), sleep=lambda _: None, rand=lambda: 0.0)


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_fetch_writes_catalog_csv(tmp_path: Path, shopify_page1, shopify_page2, capsys):
    out = tmp_path / "catalog.csv"
    code = main(
        ["fetch", "--store", STORE, "--out", str(out)],
        fetcher_factory=lambda: shopify_fetcher({1: shopify_page1, 2: shopify_page2}),
    )
    assert code == 0
    rows = read_rows(out)
    assert len(rows) == 3
    assert rows[0]["sku"] == "NB-TR2-42-BLK"
    assert "3 rows" in capsys.readouterr().out


def test_watch_first_run_marks_everything_added(tmp_path: Path, shopify_page1, shopify_page2):
    changes = tmp_path / "changes.csv"
    state = tmp_path / "state"
    code = main(
        ["watch", "--store", STORE, "--out", str(changes), "--state-dir", str(state)],
        fetcher_factory=lambda: shopify_fetcher({1: shopify_page1, 2: shopify_page2}),
    )
    assert code == 0
    rows = read_rows(changes)
    assert len(rows) == 3
    assert {row["change_type"] for row in rows} == {"added"}
    assert list(state.glob("*.json"))


def test_watch_second_run_reports_only_real_changes(tmp_path: Path, shopify_page1, shopify_page2):
    changes = tmp_path / "changes.csv"
    state = tmp_path / "state"

    def factory():
        return shopify_fetcher({1: shopify_page1, 2: shopify_page2})

    main(["watch", "--store", STORE, "--out", str(changes), "--state-dir", str(state)], fetcher_factory=factory)
    assert len(read_rows(changes)) == 3

    # same catalog again -> no changes
    main(["watch", "--store", STORE, "--out", str(changes), "--state-dir", str(state)], fetcher_factory=factory)
    assert read_rows(changes) == []

    # price drop on one variant
    cheaper = {1: {"products": [dict(shopify_page1["products"][0])]}, 2: {"products": []}}
    variant = dict(cheaper[1]["products"][0]["variants"][0])
    variant["price"] = "99.00"
    cheaper[1]["products"][0]["variants"] = [variant]
    main(
        ["watch", "--store", STORE, "--out", str(changes), "--state-dir", str(state)],
        fetcher_factory=lambda: shopify_fetcher(cheaper),
    )

    rows = read_rows(changes)
    types = {row["change_type"] for row in rows}
    assert "price_changed" in types
    assert "removed" in types  # the second variant is absent in the trimmed catalog
    price_row = next(row for row in rows if row["change_type"] == "price_changed")
    assert price_row["old_value"] == "129.00"
    assert price_row["new_value"] == "99.00"


def test_watch_telegram_dry_run_prints_and_does_not_send(tmp_path: Path, shopify_page1, shopify_page2, capsys):
    changes = tmp_path / "changes.csv"
    state = tmp_path / "state"
    code = main(
        ["watch", "--store", STORE, "--out", str(changes), "--state-dir", str(state), "--telegram", "--dry-run"],
        fetcher_factory=lambda: shopify_fetcher({1: shopify_page1, 2: shopify_page2}),
    )
    assert code == 0
    assert "dry run" in capsys.readouterr().out.lower()


def test_unknown_source_is_rejected(tmp_path: Path):
    code = main(
        ["fetch", "--store", STORE, "--out", str(tmp_path / "c.csv"), "--source", "myspace"],
        fetcher_factory=lambda: shopify_fetcher({}),
    )
    assert code == 2


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "catalogwatch" in capsys.readouterr().out.lower()
