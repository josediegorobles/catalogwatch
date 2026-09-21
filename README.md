# CatalogWatch

Export any **Shopify** or **WooCommerce** catalog to CSV in one command, then get a **SKU-level
report of what changed** (price drops, restocks, new and removed products) with an optional
Telegram alert.

No browser, no selectors, no per-product fees, no API keys. CatalogWatch reads the public catalog
endpoint the store already publishes, so nothing breaks when the store changes its theme.

Measured on a real store: **250 products / 2,525 variant rows in 1.0 s**, 500 products in 2.1 s.

```bash
catalogwatch fetch --store https://competitor.com --out catalog.csv
catalogwatch watch --store https://competitor.com --out changes.csv --telegram
```

---

## Install in 3 steps (no Docker)

```bash
# 1. create an isolated environment and install
python3 -m venv .venv && .venv/bin/pip install -e .

# 2. copy the configuration template (works out of the box; Telegram is optional)
cp .env.example .env

# 3. run it
.venv/bin/catalogwatch fetch --store https://competitor.com --out catalog.csv
```

## Install in 3 steps (Docker)

```bash
# 1. build the image
cp .env.example .env && docker compose build

# 2. fetch a catalog (results land in ./out)
docker compose run --rm catalogwatch fetch --store https://competitor.com --out out/catalog.csv

# 3. watch for changes (snapshots land in ./state)
docker compose run --rm catalogwatch watch --store https://competitor.com --out out/changes.csv
```

---

## Commands

### `catalogwatch fetch` — full catalog to CSV

| Flag | Default | Meaning |
| --- | --- | --- |
| `--store` | required | Store URL, e.g. `https://competitor.com` |
| `--out` | `catalog.csv` | Output CSV path |
| `--source` | `auto` | `auto`, `shopify`, `woo` or `jsonld` |
| `--max-pages` | `50` | Safety cap on paginated requests |
| `--expand-variations` | off | Fetch WooCommerce variable products variant by variant |

### `catalogwatch watch` — what changed since last run

| Flag | Default | Meaning |
| --- | --- | --- |
| `--out` | `changes.csv` | Change report path |
| `--state-dir` | `state` | Where snapshots are kept (one JSON per store) |
| `--telegram` | off | Send the report to Telegram |
| `--dry-run` | off | Print the Telegram message instead of sending it |
| `--notify-empty` | off | Also notify when nothing changed |
| `--quiet` | off | Print nothing on success |

### `catalogwatch doctor`

Prints Python/httpx versions and whether Telegram is configured.

Exit codes: `0` success, `1` fetch/source error, `2` configuration or usage error.

---

## CSV columns

`store, source, fetched_at, product_id, handle, title, vendor, product_type, tags, product_url,
image_url, updated_at, variant_id, variant_title, sku, option1, option2, option3, price,
compare_at_price, available, inventory_quantity`

One row per variant, stable column order, prices normalised to two decimals, `tags` joined with
`|`. The change report uses a different, smaller schema:
`change_type, key, sku, title, field, old_value, new_value` where `change_type` is one of `added`,
`removed`, `price_changed`, `stock_changed`.

Rows are keyed by `handle::sku` (falling back to `handle::variant:<id>`), so a diff survives
renames of product titles and price-only edits.

---

## Scheduling it

Cron, once a day at 07:00:

```cron
0 7 * * * cd /path/to/catalogwatch && .venv/bin/catalogwatch watch --store https://competitor.com --out out/changes.csv --telegram
```

macOS LaunchAgent and systemd equivalents work the same way: run `watch`, keep `state/` and read
`changes.csv` (or the Telegram message).

---

## Telegram setup (optional, 60 seconds)

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. Send any message to your new bot, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id`.
3. Put both values in `.env` as `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
4. Test without sending anything: `catalogwatch watch --store <url> --telegram --dry-run`.

---

## Configuration (`.env`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `CATALOGWATCH_USER_AGENT` | `catalogwatch/1.0 (+https://catalogwatch.dev)` | Sent on every request |
| `CATALOGWATCH_REQUEST_TIMEOUT` | `20` | Seconds per request |
| `CATALOGWATCH_MAX_RETRIES` | `3` | Retries on 429/5xx and network errors, with exponential backoff |
| `CATALOGWATCH_RETRY_BASE_DELAY` | `1.0` | Backoff base in seconds (`Retry-After` wins when present) |
| `CATALOGWATCH_PAGE_DELAY` | `0.3` | Politeness delay between paginated requests |
| `TELEGRAM_BOT_TOKEN` | – | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | – | Chat or channel id |

---

## What it does not do

- **Auth-gated or unpublished catalogs.** It reads what the store publishes publicly. A store that
  disabled `/products.json` and does not expose the WooCommerce Store API falls back to JSON-LD on
  the listing page, which returns fewer fields (no variant options, no stock quantity).
- **Prices on every currency.** One currency per store, as published.
- **Duplicate keys.** If the same `handle::sku` appears twice, both rows are exported but the diff
  treats them as one row and prints a warning on stderr.
- **Any per-store scraping contract.** Public product data is generally fine to read, but the store's
  terms and `robots.txt` remain your responsibility, and CatalogWatch sends a polite, identifiable
  User-Agent with a delay between pages.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `no supported catalog found` | The store exposes neither endpoint; run `--source jsonld` explicitly and check the store URL |
| `HTTP 403` | The store blocks datacentre IPs. Run it from your own machine or a residential connection |
| Fewer products than expected | Shopify caps `/products.json`; increase `--max-pages` |
| WooCommerce variable products collapsed | Add `--expand-variations` |
| Telegram silent | `--telegram --dry-run` first; check token/chat id and that you sent a message to the bot |

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # dev extras: pytest + ruff
make test    # pytest, no network
make lint    # ruff check + format check
make demo    # live run against a public store
```

The suite is 41 offline tests with fixtures frozen from real store payloads. Live verification
(2026-09-21): `allbirds.com` 250 products / 2,525 rows in 1.0 s, `gymshark.com` 500 products /
3,310 rows in 2.1 s, and a real `price_changed` row detected after a snapshot edit.

## Licence

Commercial licence, one business, unlimited stores and runs. See `LICENSE.txt`.
