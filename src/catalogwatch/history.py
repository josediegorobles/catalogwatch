"""SQLite history: the price/stock time series that no one else can reconstruct.

Raw snapshots are thrown away (a 250-product feed is ~1.5 MB; 300 stores a day would be ~450 MB).
What is kept is one row per observed change plus the current state of every SKU.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    store TEXT NOT NULL,
    handle TEXT NOT NULL,
    sku TEXT NOT NULL,
    variant_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    variant_title TEXT NOT NULL DEFAULT '',
    price TEXT NOT NULL DEFAULT '',
    compare_at_price TEXT NOT NULL DEFAULT '',
    available TEXT NOT NULL DEFAULT '',
    product_url TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT '',
    last_seen TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (store, handle, sku)
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    handle TEXT NOT NULL,
    sku TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    price TEXT NOT NULL DEFAULT '',
    available TEXT NOT NULL DEFAULT '',
    change_type TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_sku ON price_history (store, handle, sku);
CREATE INDEX IF NOT EXISTS idx_history_observed ON price_history (observed_at);
"""

PRODUCT_FIELDS = (
    "variant_id",
    "title",
    "variant_title",
    "price",
    "compare_at_price",
    "available",
    "product_url",
    "image_url",
    "updated_at",
)


def connect(path: Path) -> sqlite3.Connection:
    path = Path(path)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _insert_history(
    conn: sqlite3.Connection,
    store: str,
    handle: str,
    sku: str,
    observed_at: str,
    price: str,
    available: str,
    change_type: str,
) -> None:
    conn.execute(
        "INSERT INTO price_history (store, handle, sku, observed_at, price, available, change_type)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (store, handle, sku, observed_at, price, available, change_type),
    )


def _change_type(existing: Mapping[str, Any], price: str, available: str) -> str | None:
    if str(existing["price"]) != price:
        return "price_changed"
    if str(existing["available"]) != available:
        return "stock_changed"
    return None


def record_snapshot(
    conn: sqlite3.Connection, store: str, rows: Sequence[Mapping[str, Any]], observed_at: str
) -> dict[str, int]:
    """Upsert a store's catalog and append history rows only for what actually changed."""
    counts = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}
    seen: set[tuple[str, str]] = set()

    for row in rows:
        handle = str(row.get("handle") or "")
        sku = str(row.get("sku") or "")
        seen.add((handle, sku))
        values = [str(row.get(field) or "") for field in PRODUCT_FIELDS]
        existing = conn.execute(
            "SELECT price, available FROM products WHERE store = ? AND handle = ? AND sku = ?",
            (store, handle, sku),
        ).fetchone()

        if existing is None:
            placeholders = ", ".join("?" for _ in range(len(PRODUCT_FIELDS)))
            conn.execute(
                f"INSERT INTO products (store, handle, sku, {', '.join(PRODUCT_FIELDS)}, last_seen)"
                f" VALUES (?, ?, ?, {placeholders}, ?)",
                (store, handle, sku, *values, observed_at),
            )
            _insert_history(conn, store, handle, sku, observed_at, values[3], values[5], "added")
            counts["added"] += 1
            continue

        change_type = _change_type(existing, values[3], values[5])
        assignments = ", ".join(f"{field} = ?" for field in PRODUCT_FIELDS)
        conn.execute(
            f"UPDATE products SET {assignments}, last_seen = ? WHERE store = ? AND handle = ? AND sku = ?",
            (*values, observed_at, store, handle, sku),
        )
        if change_type is None:
            counts["unchanged"] += 1
        else:
            _insert_history(conn, store, handle, sku, observed_at, values[3], values[5], change_type)
            counts["changed"] += 1

    known = conn.execute("SELECT handle, sku FROM products WHERE store = ?", (store,)).fetchall()
    for entry in known:
        key = (entry["handle"], entry["sku"])
        if key in seen:
            continue
        conn.execute("DELETE FROM products WHERE store = ? AND handle = ? AND sku = ?", (store, key[0], key[1]))
        _insert_history(conn, store, key[0], key[1], observed_at, "", "", "removed")
        counts["removed"] += 1

    conn.commit()
    return counts


def current_rows(conn: sqlite3.Connection, store: str) -> list[dict[str, str]]:
    """The last known state of a store, shaped like catalog rows so it can be diffed."""
    rows = conn.execute("SELECT * FROM products WHERE store = ?", (store,)).fetchall()
    return [dict(row) for row in rows]


def history_rows(
    conn: sqlite3.Connection, store: str | None = None, handle: str | None = None, sku: str | None = None
) -> list[dict[str, Any]]:
    query = "SELECT * FROM price_history"
    clauses: list[str] = []
    params: list[str] = []
    for column, value in (("store", store), ("handle", handle), ("sku", sku)):
        if value is not None:
            clauses.append(f"{column} = ?")
            params.append(value)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id"
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def store_stats(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    query = """
        SELECT p.store AS store,
               COUNT(*) AS skus,
               (SELECT COUNT(*) FROM price_history h WHERE h.store = p.store) AS changes,
               (SELECT MIN(observed_at) FROM price_history h WHERE h.store = p.store) AS first_seen,
               (SELECT MAX(observed_at) FROM price_history h WHERE h.store = p.store) AS last_seen
        FROM products p
        GROUP BY p.store
        ORDER BY p.store
    """
    stats = [dict(row) for row in conn.execute(query).fetchall()]
    if stats:
        return stats
    return [
        dict(row)
        for row in conn.execute(
            "SELECT store, 0 AS skus, COUNT(*) AS changes, MIN(observed_at) AS first_seen, MAX(observed_at) AS last_seen"
            " FROM price_history GROUP BY store ORDER BY store"
        ).fetchall()
    ]
