from __future__ import annotations

import csv
from pathlib import Path

from catalogwatch.normalize import CSV_COLUMNS, money, row_key, to_rows, write_csv
from catalogwatch.sources import Catalog, Product, Variant


def make_catalog() -> Catalog:
    return Catalog(
        store="https://shop.example.com",
        source="shopify",
        fetched_at="2026-09-21T15:00:00+00:00",
        products=(
            Product(
                product_id="1",
                handle="trail-runner-2",
                title="Trail Runner 2",
                vendor="Northbound",
                product_type="Shoes",
                tags=("trail", "running"),
                url="https://shop.example.com/products/trail-runner-2",
                image_url="https://cdn.example-shop.com/a.jpg",
                updated_at="2026-09-18T09:02:00-07:00",
                variants=(
                    Variant("10", "NB-TR2-42", "42 / Black", "42", "Black", "", "129.00", "149.00", True, ""),
                    Variant("11", "NB-TR2-43", "43 / Black", "43", "Black", "", "129", "", False, "3"),
                ),
            ),
        ),
    )


def test_one_row_per_variant_with_fixed_columns():
    rows = to_rows(make_catalog())
    assert len(rows) == 2
    assert tuple(rows[0].keys()) == CSV_COLUMNS
    assert rows[0]["store"] == "https://shop.example.com"
    assert rows[0]["source"] == "shopify"
    assert rows[0]["handle"] == "trail-runner-2"
    assert rows[0]["tags"] == "trail|running"
    assert rows[0]["sku"] == "NB-TR2-42"
    assert rows[0]["price"] == "129.00"
    assert rows[0]["available"] == "true"
    assert rows[0]["product_url"] == "https://shop.example.com/products/trail-runner-2"


def test_prices_are_normalised_to_two_decimals():
    rows = to_rows(make_catalog())
    assert rows[1]["price"] == "129.00"
    assert rows[1]["compare_at_price"] == ""
    assert rows[1]["inventory_quantity"] == "3"
    assert rows[1]["available"] == "false"


def test_row_key_prefers_handle_and_sku():
    rows = to_rows(make_catalog())
    assert row_key(rows[0]) == "trail-runner-2::NB-TR2-42"
    assert row_key({"handle": "x", "sku": "", "variant_id": "99"}) == "x::variant:99"
    assert row_key({"handle": "", "sku": "", "variant_id": ""}) == "unknown"


def test_money_handles_messy_input():
    assert money("129.00") == "129.00"
    assert money("129") == "129.00"
    assert money("1,299.00") == "1299.00"
    assert money("€ 19,99") == "19.99"
    assert money("") == ""
    assert money(None) == ""
    assert money("call for price") == "call for price"


def test_write_csv_roundtrip(tmp_path: Path):
    rows = to_rows(make_catalog())
    out = tmp_path / "catalog.csv"
    assert write_csv(rows, out) == 2
    with out.open(newline="", encoding="utf-8") as handle:
        parsed = list(csv.DictReader(handle))
    assert len(parsed) == 2
    assert parsed[1]["available"] == "false"
    assert list(parsed[0].keys()) == list(CSV_COLUMNS)


def test_write_csv_with_no_rows_still_writes_header(tmp_path: Path):
    out = tmp_path / "empty.csv"
    assert write_csv([], out) == 0
    assert out.read_text(encoding="utf-8").strip() == ",".join(CSV_COLUMNS)
