"""Snapshot diffing: what was added, removed, repriced or went out of stock since last run."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .normalize import row_key

WATCHED_FIELDS = (("price", "price_changed"), ("available", "stock_changed"))


def _entry(change_type: str, key: str, row: Mapping[str, Any], field: str, old: str, new: str) -> dict[str, str]:
    return {
        "change_type": change_type,
        "key": key,
        "sku": str(row.get("sku") or ""),
        "title": str(row.get("title") or ""),
        "field": field,
        "old_value": old,
        "new_value": new,
    }


def diff_rows(previous: Sequence[Mapping[str, Any]], current: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Return one row per changed fact, sorted by (change_type, key) for reproducible diffs."""
    before = {row_key(row): row for row in previous}
    after = {row_key(row): row for row in current}
    changes: list[dict[str, str]] = []

    for key in set(before) - set(after):
        row = before[key]
        changes.append(_entry("removed", key, row, "price", str(row.get("price") or ""), ""))
    for key in set(after) - set(before):
        row = after[key]
        changes.append(_entry("added", key, row, "price", "", str(row.get("price") or "")))
    for key in set(before) & set(after):
        old_row, new_row = before[key], after[key]
        for field, change_type in WATCHED_FIELDS:
            old_value = str(old_row.get(field) or "")
            new_value = str(new_row.get(field) or "")
            if old_value != new_value:
                changes.append(_entry(change_type, key, new_row, field, old_value, new_value))

    changes.sort(key=lambda change: (change["change_type"], change["key"]))
    return changes


def duplicate_keys(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Keys that appear more than once. Diffing collapses them, so the caller should warn."""
    counts: Counter[str] = Counter(row_key(row) for row in rows)
    return sorted(key for key, count in counts.items() if count > 1)


def snapshot_path(state_dir: Path, store: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"^https?://", "", store.lower())).strip("-")
    return Path(state_dir) / f"{slug}.json"


def load_snapshot(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []
    return payload if isinstance(payload, list) else []


def save_snapshot(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(rows), ensure_ascii=False, indent=1), encoding="utf-8")
