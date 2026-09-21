# Changelog

## 1.1.0 — 2026-09-21

- `fleet`: crawl a list of stores in one pass into a single SQLite history database, with per-store
  change reports and an optional Telegram summary. A failing store is reported, never fatal.
- `history`: SQLite store with the current state of every SKU and one row per observed change.
  Measured on two real stores: 4,208 SKUs / 4,211 history rows in 3.5 MB; a second pass writes zero
  rows. Raw snapshots are deliberately not kept (~1.5 MB per 250-product feed per day).
- 53 offline tests.

## 1.0.0 — 2026-09-21

- `fetch`: full Shopify (`/products.json`), WooCommerce (Store API) and generic JSON-LD catalog
  export to CSV, one row per variant.
- `watch`: snapshot per store, SKU-level diff (`added`, `removed`, `price_changed`,
  `stock_changed`) written to CSV, optional Telegram alert with `--dry-run`.
- HTTP layer with timeouts, identifiable User-Agent, exponential backoff, `Retry-After` support
  and a politeness delay between pages.
- `doctor` command, Dockerfile and docker-compose, `.env.example`.
- Public source with a commercial licence (free for non-commercial use, 39 EUR for commercial use).
- Public source with a commercial licence (free for non-commercial use, 39 EUR for commercial use).
- 41 offline tests (fixtures frozen from real store payloads) plus live verification against a
  public Shopify store: 250 products / 2,525 rows in 1.0 s, and a real `price_changed` detection.
