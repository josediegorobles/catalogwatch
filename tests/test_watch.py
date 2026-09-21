from __future__ import annotations

import json
from pathlib import Path

from catalogwatch.watch import diff_rows, load_snapshot, save_snapshot, snapshot_path


def row(handle: str, sku: str, price: str, available: str = "true") -> dict:
    return {
        "handle": handle,
        "sku": sku,
        "variant_id": f"{handle}-{sku}",
        "title": handle.replace("-", " ").title(),
        "price": price,
        "available": available,
    }


def test_detects_added_removed_price_and_stock_changes():
    previous = [row("a", "A1", "10.00"), row("b", "B1", "20.00"), row("c", "C1", "30.00", "true")]
    current = [row("a", "A1", "9.50"), row("b", "B1", "20.00"), row("c", "C1", "30.00", "false"), row("d", "D1", "5.00")]

    changes = diff_rows(previous, current)
    by_type = {change["change_type"]: change for change in changes}
    assert set(by_type) == {"added", "price_changed", "stock_changed"}
    assert by_type["price_changed"]["old_value"] == "10.00"
    assert by_type["price_changed"]["new_value"] == "9.50"
    assert by_type["price_changed"]["key"] == "a::A1"
    assert by_type["stock_changed"]["new_value"] == "false"
    assert by_type["added"]["new_value"] == "5.00"


def test_removed_rows_are_reported():
    changes = diff_rows([row("a", "A1", "10.00")], [])
    assert len(changes) == 1
    assert changes[0]["change_type"] == "removed"
    assert changes[0]["old_value"] == "10.00"


def test_identical_catalogs_produce_no_changes():
    snapshot = [row("a", "A1", "10.00"), row("b", "B1", "20.00")]
    assert diff_rows(snapshot, snapshot) == []


def test_change_order_is_deterministic():
    previous = [row("b", "B1", "20.00"), row("a", "A1", "10.00")]
    current = [row("c", "C1", "1.00"), row("b", "B1", "21.00")]
    changes = diff_rows(previous, current)
    assert [(c["change_type"], c["key"]) for c in changes] == sorted(
        [(c["change_type"], c["key"]) for c in changes]
    )


def test_snapshot_roundtrip_and_path(tmp_path: Path):
    path = snapshot_path(tmp_path, "https://shop.example.com")
    assert path.parent == tmp_path
    assert path.name == "shop-example-com.json"

    rows = [row("a", "A1", "10.00")]
    save_snapshot(path, rows)
    assert load_snapshot(path) == rows
    assert json.loads(path.read_text(encoding="utf-8"))[0]["sku"] == "A1"


def test_missing_snapshot_reads_as_empty(tmp_path: Path):
    assert load_snapshot(tmp_path / "nope.json") == []
