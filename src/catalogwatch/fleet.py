"""Fleet runner: crawl a list of stores, append their changes to the history database."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from .history import current_rows, record_snapshot
from .http import FetchError, Fetcher
from .normalize import to_rows
from .sources import SourceError, fetch_catalog
from .watch import diff_rows

OnStore = Callable[[str, int, list[dict[str, str]], str | None], None]


def load_stores(path: Path) -> list[str]:
    stores: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        text = line.split("#", 1)[0].strip()
        if text:
            stores.append(text)
    return stores


def run_fleet(
    stores: Sequence[str],
    fetcher: Fetcher,
    conn: Any,
    *,
    source: str = "auto",
    max_pages: int = 1,
    observed_at: str | None = None,
    on_store: OnStore | None = None,
) -> dict[str, Any]:
    """One pass over the fleet. A store that fails is reported and skipped, never fatal."""
    moment = observed_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    result: dict[str, Any] = {
        "observed_at": moment,
        "stores_ok": 0,
        "stores_failed": 0,
        "changes": 0,
        "errors": [],
        "per_store": {},
    }

    for store in stores:
        try:
            catalog = fetch_catalog(store, fetcher, source=source, max_pages=max_pages)
            rows = to_rows(catalog)
            changes = diff_rows(current_rows(conn, catalog.store), rows)
            counts = record_snapshot(conn, catalog.store, rows, moment)
        except (SourceError, FetchError) as exc:
            result["stores_failed"] += 1
            result["errors"].append((store, str(exc)))
            if on_store is not None:
                on_store(store, 0, [], str(exc))
            continue

        result["stores_ok"] += 1
        result["changes"] += len(changes)
        result["per_store"][store] = {"rows": len(rows), "changes": changes, "counts": counts}
        if on_store is not None:
            on_store(store, len(rows), changes, None)

    if result["stores_ok"] == 0 and stores:
        raise RuntimeError(f"no store could be read ({len(result['errors'])} errors)")
    return result
