"""CSV shaping: one row per variant, stable column order, normalised prices."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .sources import Catalog

CSV_COLUMNS = (
    "store",
    "source",
    "fetched_at",
    "product_id",
    "handle",
    "title",
    "vendor",
    "product_type",
    "tags",
    "product_url",
    "image_url",
    "updated_at",
    "variant_id",
    "variant_title",
    "sku",
    "option1",
    "option2",
    "option3",
    "price",
    "compare_at_price",
    "available",
    "inventory_quantity",
)

CHANGE_COLUMNS = (
    "change_type",
    "key",
    "sku",
    "title",
    "field",
    "old_value",
    "new_value",
)

_THOUSANDS_PATTERN = re.compile(r"^\d{1,3}(,\d{3})+$")


def money(value: Any) -> str:
    """Normalise a price to two decimals. Unparseable values are returned stripped, never guessed."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""

    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return text

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", "") if _THOUSANDS_PATTERN.match(cleaned) else cleaned.replace(",", ".")

    try:
        return f"{float(cleaned):.2f}"
    except ValueError:
        return text


def row_key(row: Mapping[str, Any]) -> str:
    handle = str(row.get("handle") or "").strip()
    sku = str(row.get("sku") or "").strip()
    if handle and sku:
        return f"{handle}::{sku}"
    variant_id = str(row.get("variant_id") or "").strip()
    if handle and variant_id:
        return f"{handle}::variant:{variant_id}"
    if handle:
        return handle
    if variant_id:
        return f"variant:{variant_id}"
    return "unknown"


def to_rows(catalog: Catalog) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for product in catalog.products:
        for variant in product.variants:
            rows.append(
                {
                    "store": catalog.store,
                    "source": catalog.source,
                    "fetched_at": catalog.fetched_at,
                    "product_id": product.product_id,
                    "handle": product.handle,
                    "title": product.title,
                    "vendor": product.vendor,
                    "product_type": product.product_type,
                    "tags": "|".join(product.tags),
                    "product_url": product.url,
                    "image_url": product.image_url,
                    "updated_at": product.updated_at,
                    "variant_id": variant.variant_id,
                    "variant_title": variant.title,
                    "sku": variant.sku,
                    "option1": variant.option1,
                    "option2": variant.option2,
                    "option3": variant.option3,
                    "price": money(variant.price),
                    "compare_at_price": money(variant.compare_at_price),
                    "available": "true" if variant.available else "false",
                    "inventory_quantity": variant.inventory_quantity,
                }
            )
    return rows


def write_csv(rows: Sequence[Mapping[str, Any]], path: Path) -> int:
    """Write a catalog export (one row per variant)."""
    return _write(rows, path, CSV_COLUMNS)


def write_changes_csv(rows: Sequence[Mapping[str, Any]], path: Path) -> int:
    """Write a change report produced by watch.diff_rows."""
    return _write(rows, path, CHANGE_COLUMNS)


def _write(rows: Sequence[Mapping[str, Any]], path: Path, columns: Sequence[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return len(rows)
