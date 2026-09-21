# Listing copy — English (Gumroad / Whop / Lemon Squeezy)

**Title (≤60 chars):** Competitor catalog to CSV + price-change alerts

**Subtitle / short description (≤140 chars):** Export any Shopify or WooCommerce catalog to CSV in one command. Get SKU-level price and stock changes on Telegram. No browser, no fees.

**Price:** €39 one-time (VAT included for EU buyers) — buy: <https://buy.stripe.com/8x200lfkEbyffbd3SifrW09>

---

## Full description

**Track 10 competitor catalogs in the time it takes to make coffee.**

CatalogWatch reads the public catalog endpoint every Shopify and WooCommerce store already
publishes, writes it to a clean CSV (one row per variant: SKU, price, compare-at price, stock,
image, URL) and tells you exactly what changed since the last run.

Measured on a live store: **250 products / 2,525 variant rows in 1.0 seconds.** No browser, no
selectors, no per-product fees, no API keys.

```bash
catalogwatch fetch --store https://competitor.com --out catalog.csv
catalogwatch watch --store https://competitor.com --out changes.csv --telegram
```

**What you get**

- A price and stock report keyed by `handle::sku`, so a diff survives title edits:
  `added`, `removed`, `price_changed`, `stock_changed`.
- Optional Telegram alert, with `--dry-run` so you can test it without spamming your chat.
- Automatic retries with exponential backoff and `Retry-After`, a real User-Agent and a delay
  between pages. It does not get you rate-limited.
- Runs on your machine or in Docker, on a schedule you own.
- Full source code, 41 offline tests, README, `.env.example`, Dockerfile and a demo script.
- Commercial licence: one business, unlimited stores, unlimited runs.

**Who it is for**

- Store owners who check competitor prices by hand every week.
- Agencies that need a client's or a competitor's catalog as a spreadsheet in seconds.
- Dropshippers and arbitrage sellers watching for restocks and price drops.
- Data people who want the CSV, not another dashboard subscription.

**Why not just use a scraper API?**

Because you pay per product, forever. A typical Shopify scraper API charges $1.50–$6.00 per 1,000
products, so ten catalogs of 2,500 SKUs cost roughly $25–$100 **every month**. CatalogWatch is one
payment, runs locally, and keeps your price history in a file you own.

**Why not changedetection.io?**

It watches pages and diffs text, so you get a notification that "something changed" in the HTML.
CatalogWatch understands products: you get "SKU A11768M080 dropped from 130.00 to 99.00".

**Honest limits**

- Public data only: catalogs behind a login are out of scope.
- If a store disabled its public catalog endpoint, CatalogWatch falls back to JSON-LD on the
  listing page, which returns fewer fields (no variant options, no stock quantity).
- One currency per store, exactly as published.
- No SLA, no hosting, no ongoing maintenance needed: the endpoint it reads is the store's own API.

**Requirements:** Python 3.10+ (or Docker) and a machine that can reach the store's website.
Windows, macOS and Linux.

**Support:** installation support by email for 30 days. Nothing to maintain afterwards.

---

## FAQ

**Does it need a headless browser or a proxy?**
No. It reads JSON the store serves publicly, which is why it does not break when a theme changes.

**Can I monitor stores on a schedule?**
Yes — one cron line: `catalogwatch watch --store <url> --out out/changes.csv --telegram`.

**Does it work with my own Shopify store?**
Yes, and for your own store the Shopify admin CSV export is still the better tool. CatalogWatch is
for catalogs you do not have admin access to.

**Is scraping competitor prices legal?**
Reading publicly published product data is generally accepted, but the store's terms and
`robots.txt` are your responsibility. CatalogWatch sends an identifiable User-Agent and delays
between requests so you do not hammer anyone's server.

**What if the store blocks it?**
Some stores block datacentre IPs. Run it from your own machine or a residential connection; that is
the configuration the tool is designed for.

**Refunds?**
Per the marketplace policy. Test it on your own competitor list first — the `fetch` command takes
seconds.
