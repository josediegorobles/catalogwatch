from __future__ import annotations

import sqlite3
from pathlib import Path

from catalogwatch.history import connect, history_rows, record_snapshot, store_stats


def row(handle: str, sku: str, price: str, available: str = "true", title: str = "Thing") -> dict:
    return {
        "store": "https://shop.example.com",
        "handle": handle,
        "sku": sku,
        "title": title,
        "variant_title": "Default",
        "price": price,
        "compare_at_price": "",
        "available": available,
        "product_url": f"https://shop.example.com/products/{handle}",
        "image_url": "",
        "updated_at": "",
    }


def test_first_snapshot_is_recorded_as_added(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    counts = record_snapshot(
        conn,
        "https://shop.example.com",
        [row("a", "A1", "10.00"), row("b", "B1", "20.00")],
        "2026-09-21T07:00:00+00:00",
    )

    assert counts == {"added": 2, "changed": 0, "unchanged": 0, "removed": 0}
    assert [entry["change_type"] for entry in history_rows(conn, "https://shop.example.com")] == ["added", "added"]


def test_identical_snapshot_writes_no_history(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    rows = [row("a", "A1", "10.00")]
    record_snapshot(conn, "https://shop.example.com", rows, "2026-09-21T07:00:00+00:00")
    counts = record_snapshot(conn, "https://shop.example.com", rows, "2026-09-22T07:00:00+00:00")

    assert counts == {"added": 0, "changed": 0, "unchanged": 1, "removed": 0}
    assert len(history_rows(conn, "https://shop.example.com")) == 1


def test_price_and_stock_changes_are_appended(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    record_snapshot(conn, "https://shop.example.com", [row("a", "A1", "10.00")], "2026-09-21T07:00:00+00:00")
    counts = record_snapshot(
        conn, "https://shop.example.com", [row("a", "A1", "9.00", "false")], "2026-09-22T07:00:00+00:00"
    )

    assert counts["changed"] == 1
    entries = history_rows(conn, "https://shop.example.com")
    assert [(e["change_type"], e["price"], e["available"]) for e in entries] == [
        ("added", "10.00", "true"),
        ("price_changed", "9.00", "false"),
    ]


def test_removed_products_are_logged_and_forgotten(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    record_snapshot(
        conn,
        "https://shop.example.com",
        [row("a", "A1", "10.00"), row("b", "B1", "20.00")],
        "2026-09-21T07:00:00+00:00",
    )
    counts = record_snapshot(conn, "https://shop.example.com", [row("a", "A1", "10.00")], "2026-09-22T07:00:00+00:00")

    assert counts == {"added": 0, "changed": 0, "unchanged": 1, "removed": 1}
    assert [e["change_type"] for e in history_rows(conn, "https://shop.example.com", sku="B1")] == ["added", "removed"]

    # if it comes back it is a new "added", not a duplicate product row
    record_snapshot(conn, "https://shop.example.com", [row("b", "B1", "20.00")], "2026-09-23T07:00:00+00:00")
    assert [e["change_type"] for e in history_rows(conn, "https://shop.example.com", sku="B1")] == [
        "added",
        "removed",
        "added",
    ]


def test_history_is_kept_per_store(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    other = dict(row("a", "A1", "10.00"), store="https://other.example.com")
    record_snapshot(conn, "https://shop.example.com", [row("a", "A1", "10.00")], "2026-09-21T07:00:00+00:00")
    record_snapshot(conn, "https://other.example.com", [other], "2026-09-21T07:00:00+00:00")

    assert len(history_rows(conn, "https://shop.example.com")) == 1
    assert len(history_rows(conn, "https://other.example.com")) == 1
    assert len(history_rows(conn)) == 2


def test_store_stats_summarise_the_fleet(tmp_path: Path):
    conn = connect(tmp_path / "history.sqlite")
    record_snapshot(conn, "https://shop.example.com", [row("a", "A1", "10.00")], "2026-09-21T07:00:00+00:00")
    record_snapshot(conn, "https://shop.example.com", [row("a", "A1", "9.00")], "2026-09-22T07:00:00+00:00")

    stats = store_stats(conn)
    assert len(stats) == 1
    assert stats[0]["store"] == "https://shop.example.com"
    assert stats[0]["skus"] == 1
    assert stats[0]["changes"] == 2
    assert stats[0]["first_seen"] == "2026-09-21T07:00:00+00:00"
    assert stats[0]["last_seen"] == "2026-09-22T07:00:00+00:00"


def test_connect_is_idempotent(tmp_path: Path):
    path = tmp_path / "history.sqlite"
    connect(path).close()
    conn = connect(path)
    assert isinstance(conn, sqlite3.Connection)
    assert record_snapshot(conn, "https://shop.example.com", [], "2026-09-21T07:00:00+00:00")["added"] == 0
