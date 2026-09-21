"""Command line interface: `catalogwatch fetch` and `catalogwatch watch`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Sequence

from . import __version__
from .config import Settings, load_settings
from .http import FetchError, Fetcher
from .normalize import to_rows, write_changes_csv, write_csv
from .sources import SOURCES, SourceError, fetch_catalog
from .telegram import TelegramError, format_alert, send_alert
from .watch import diff_rows, load_snapshot, save_snapshot, snapshot_path

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="catalogwatch",
        description="Export a Shopify/WooCommerce catalog to CSV and report SKU-level changes.",
    )
    parser.add_argument("--version", action="version", version=f"catalogwatch {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="export the full catalog to a CSV file")
    fetch.add_argument("--store", required=True, help="store URL, e.g. https://shop.example.com")
    fetch.add_argument("--out", default="catalog.csv", help="output CSV path (default: catalog.csv)")
    fetch.add_argument("--source", default="auto", help=f"one of: {', '.join(SOURCES)} (default: auto)")
    fetch.add_argument("--max-pages", type=int, default=50, help="safety cap on paginated requests")
    fetch.add_argument("--expand-variations", action="store_true", help="expand WooCommerce variable products")
    fetch.add_argument("--env-file", default=None, help="path to a .env file (default: ./.env)")

    watch = subparsers.add_parser("watch", help="compare the catalog with the previous run")
    watch.add_argument("--store", required=True, help="store URL, e.g. https://shop.example.com")
    watch.add_argument("--out", default="changes.csv", help="change report path (default: changes.csv)")
    watch.add_argument("--state-dir", default="state", help="where snapshots are kept (default: state)")
    watch.add_argument("--source", default="auto", help=f"one of: {', '.join(SOURCES)} (default: auto)")
    watch.add_argument("--max-pages", type=int, default=50, help="safety cap on paginated requests")
    watch.add_argument("--expand-variations", action="store_true", help="expand WooCommerce variable products")
    watch.add_argument("--telegram", action="store_true", help="send the report to Telegram")
    watch.add_argument("--dry-run", action="store_true", help="print the Telegram message instead of sending it")
    watch.add_argument("--notify-empty", action="store_true", help="also notify when nothing changed")
    watch.add_argument("--quiet", action="store_true", help="print nothing on success")
    watch.add_argument("--env-file", default=None, help="path to a .env file (default: ./.env)")

    subparsers.add_parser("doctor", help="show environment and configuration status")
    return parser


def _settings(args: argparse.Namespace) -> Settings:
    env_file = Path(args.env_file) if getattr(args, "env_file", None) else None
    return load_settings(env_file=env_file)


def _cmd_fetch(args: argparse.Namespace, fetcher: Fetcher) -> int:
    catalog = fetch_catalog(
        args.store,
        fetcher,
        source=args.source,
        max_pages=args.max_pages,
        expand_variations=args.expand_variations,
    )
    rows = to_rows(catalog)
    write_csv(rows, Path(args.out))
    print(f"Fetched {len(rows)} rows from {len(catalog.products)} products (source: {catalog.source}) -> {args.out}")
    return EXIT_OK


def _cmd_watch(args: argparse.Namespace, settings: Settings, fetcher: Fetcher) -> int:
    catalog = fetch_catalog(
        args.store,
        fetcher,
        source=args.source,
        max_pages=args.max_pages,
        expand_variations=args.expand_variations,
    )
    rows = to_rows(catalog)
    state = snapshot_path(Path(args.state_dir), catalog.store)
    changes = diff_rows(load_snapshot(state), rows)
    write_changes_csv(changes, Path(args.out))
    save_snapshot(state, rows)

    if not args.quiet:
        print(f"{len(changes)} change(s) since last run -> {args.out} (snapshot: {state})")

    if args.telegram and (changes or args.notify_empty):
        sent = send_alert(format_alert(catalog.store, changes), settings, fetcher, dry_run=args.dry_run)
        if sent and not args.quiet:
            print("Telegram alert sent.")
    return EXIT_OK


def _cmd_doctor(settings: Settings) -> int:
    import platform

    import httpx

    print(f"python: {platform.python_version()}")
    print(f"httpx: {httpx.__version__}")
    print(f"user-agent: {settings.user_agent}")
    print(
        f"telegram: {'configured' if settings.telegram_bot_token and settings.telegram_chat_id else 'not configured'}"
    )
    return EXIT_OK


def main(argv: Sequence[str] | None = None, fetcher_factory: Callable[[], Fetcher] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source = getattr(args, "source", "auto")
    if source not in SOURCES:
        print(f"error: unknown source '{source}' (expected one of: {', '.join(SOURCES)})", file=sys.stderr)
        return EXIT_USAGE

    settings = _settings(args)
    fetcher = fetcher_factory() if fetcher_factory is not None else Fetcher(settings)
    try:
        if args.command == "fetch":
            return _cmd_fetch(args, fetcher)
        if args.command == "watch":
            return _cmd_watch(args, settings, fetcher)
        return _cmd_doctor(settings)
    except (SourceError, FetchError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except TelegramError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    finally:
        if fetcher_factory is None:
            fetcher.close()
