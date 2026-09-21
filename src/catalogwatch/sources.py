"""Catalog sources: Shopify products.json, WooCommerce Store API, generic JSON-LD.

No browser, no selectors, no API keys: every adapter reads a public JSON/HTML endpoint
that the store itself publishes, which is why there is nothing to maintain when the
store's theme changes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from .http import FetchError, Fetcher

SOURCES = ("auto", "shopify", "woo", "jsonld")
SHOPIFY_PAGE_SIZE = 250
WOO_PAGE_SIZE = 100


class SourceError(RuntimeError):
    """Raised when a store does not expose any supported catalog endpoint."""


@dataclass(frozen=True)
class Variant:
    variant_id: str
    sku: str
    title: str
    option1: str
    option2: str
    option3: str
    price: str
    compare_at_price: str
    available: bool
    inventory_quantity: str


@dataclass(frozen=True)
class Product:
    product_id: str
    handle: str
    title: str
    vendor: str
    product_type: str
    tags: tuple[str, ...]
    url: str
    image_url: str
    updated_at: str
    variants: tuple[Variant, ...]


@dataclass(frozen=True)
class Catalog:
    store: str
    source: str
    fetched_at: str
    products: tuple[Product, ...]


def normalize_store_url(store_url: str) -> str:
    url = store_url.strip()
    if not url:
        raise SourceError("empty store URL")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def fetch_catalog(
    store_url: str,
    fetcher: Fetcher,
    *,
    source: str = "auto",
    max_pages: int = 50,
    expand_variations: bool = False,
) -> Catalog:
    base = normalize_store_url(store_url)
    candidates = SOURCES[1:] if source == "auto" else (source,)
    if source not in SOURCES:
        raise SourceError(f"unknown source '{source}' (expected one of: {', '.join(SOURCES)})")

    errors: list[str] = []
    for candidate in candidates:
        adapter = _ADAPTERS[candidate]
        try:
            products = adapter(base, fetcher, max_pages, expand_variations)
        except SourceError as exc:
            errors.append(f"{candidate}: {exc}")
            continue
        if products:
            return Catalog(
                store=base,
                source=candidate,
                fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                products=tuple(products),
            )
        errors.append(f"{candidate}: no products found")

    raise SourceError(f"no supported catalog found at {base} ({'; '.join(errors)})")


def _wait(fetcher: Fetcher) -> None:
    fetcher.pause()


# --- Shopify -----------------------------------------------------------------


def _shopify(base: str, fetcher: Fetcher, max_pages: int, expand_variations: bool) -> list[Product]:
    products: list[Product] = []
    for page in range(1, max_pages + 1):
        try:
            payload = fetcher.get_json(f"{base}/products.json", params={"limit": SHOPIFY_PAGE_SIZE, "page": page})
        except FetchError as exc:
            raise SourceError(f"/products.json not available ({exc})") from exc
        if not isinstance(payload, dict) or "products" not in payload:
            raise SourceError("/products.json did not return a product feed")
        batch = payload["products"] or []
        if not batch:
            break
        products.extend(_shopify_product(base, item) for item in batch)
        _wait(fetcher)
    return products


def _shopify_product(base: str, item: dict[str, Any]) -> Product:
    handle = str(item.get("handle") or item.get("id") or "")
    images = item.get("images") or []
    image_url = str(images[0].get("src", "")) if images else ""
    variants = tuple(_shopify_variant(variant) for variant in (item.get("variants") or []))
    if not variants:
        variants = (_shopify_variant({}),)
    return Product(
        product_id=str(item.get("id", "")),
        handle=handle,
        title=str(item.get("title", "")),
        vendor=str(item.get("vendor") or ""),
        product_type=str(item.get("product_type") or ""),
        tags=tuple(str(tag) for tag in (item.get("tags") or [])),
        url=f"{base}/products/{handle}",
        image_url=image_url,
        updated_at=str(item.get("updated_at") or ""),
        variants=variants,
    )


def _shopify_variant(item: dict[str, Any]) -> Variant:
    return Variant(
        variant_id=str(item.get("id", "")),
        sku=str(item.get("sku") or ""),
        title=str(item.get("title") or ""),
        option1=str(item.get("option1") or ""),
        option2=str(item.get("option2") or ""),
        option3=str(item.get("option3") or ""),
        price=str(item.get("price") or ""),
        compare_at_price=str(item.get("compare_at_price") or ""),
        available=bool(item.get("available")),
        inventory_quantity="",
    )


# --- WooCommerce Store API ----------------------------------------------------


def _woo(base: str, fetcher: Fetcher, max_pages: int, expand_variations: bool) -> list[Product]:
    products: list[Product] = []
    endpoint = f"{base}/wp-json/wc/store/v1/products"
    for page in range(1, max_pages + 1):
        try:
            payload = fetcher.get_json(endpoint, params={"per_page": WOO_PAGE_SIZE, "page": page})
        except FetchError as exc:
            raise SourceError(f"WooCommerce Store API not available ({exc})") from exc
        if not isinstance(payload, list):
            raise SourceError("WooCommerce Store API did not return a product list")
        if not payload:
            break
        products.extend(_woo_product(base, item, fetcher, expand_variations) for item in payload)
        _wait(fetcher)
    return products


def _woo_product(base: str, item: dict[str, Any], fetcher: Fetcher, expand_variations: bool) -> Product:
    product_id = str(item.get("id", ""))
    slug = str(item.get("slug") or product_id)
    images = item.get("images") or []
    image_url = str(images[0].get("src", "")) if images else ""

    if expand_variations and item.get("type") == "variable":
        detail = _woo_detail(base, product_id, fetcher)
        variations = detail.get("variations") if isinstance(detail, dict) else None
        if variations and isinstance(variations[0], dict):
            if not image_url:
                detail_images = detail.get("images") or []
                image_url = str(detail_images[0].get("src", "")) if detail_images else ""
            return _woo_build(base, item, slug, image_url, tuple(_woo_variation(v) for v in variations))

    variant = Variant(
        variant_id=product_id,
        sku=str(item.get("sku") or ""),
        title=str(item.get("name") or ""),
        option1="",
        option2="",
        option3="",
        price=_woo_price(item),
        compare_at_price=str(item.get("regular_price") or ""),
        available=bool(item.get("is_in_stock")),
        inventory_quantity=_woo_stock(item),
    )
    return _woo_build(base, item, slug, image_url, (variant,))


def _woo_detail(base: str, product_id: str, fetcher: Fetcher) -> dict[str, Any]:
    try:
        payload = fetcher.get_json(f"{base}/wp-json/wc/store/v1/products/{product_id}")
    except FetchError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _woo_build(base: str, item: dict[str, Any], slug: str, image_url: str, variants: tuple[Variant, ...]) -> Product:
    tags = tuple(str(tag.get("name", "")) for tag in (item.get("tags") or []) if isinstance(tag, dict))
    return Product(
        product_id=str(item.get("id", "")),
        handle=slug,
        title=str(item.get("name", "")),
        vendor="",
        product_type="",
        tags=tags,
        url=str(item.get("permalink") or f"{base}/product/{slug}"),
        image_url=image_url,
        updated_at="",
        variants=variants,
    )


def _woo_price(item: dict[str, Any]) -> str:
    price = item.get("price")
    if price:
        return str(price)
    prices = item.get("prices") or {}
    return _minor_units(prices.get("price"), prices.get("currency_minor_unit"))


def _woo_stock(item: dict[str, Any]) -> str:
    remaining = item.get("low_stock_remaining")
    return "" if remaining is None else str(remaining)


def _woo_variation(item: dict[str, Any]) -> Variant:
    options = ["", "", ""]
    for index, attribute in enumerate(item.get("attributes") or []):
        if index < len(options) and isinstance(attribute, dict):
            options[index] = str(attribute.get("value") or "")
    prices = item.get("prices") or {}
    return Variant(
        variant_id=str(item.get("id", "")),
        sku=str(item.get("sku") or ""),
        title=" / ".join(option for option in options if option),
        option1=options[0],
        option2=options[1],
        option3=options[2],
        price=_minor_units(prices.get("price"), prices.get("currency_minor_unit")),
        compare_at_price=_minor_units(prices.get("regular_price"), prices.get("currency_minor_unit")),
        available=bool(item.get("is_in_stock")),
        inventory_quantity="" if item.get("low_stock_remaining") is None else str(item.get("low_stock_remaining")),
    )


def _minor_units(value: Any, minor_unit: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        unit = int(minor_unit)
    except (TypeError, ValueError):
        return str(value)
    try:
        amount = int(str(value))
    except (TypeError, ValueError):
        return str(value)
    if unit <= 0:
        return str(amount)
    return f"{amount / (10**unit):.{unit}f}"


# --- Generic JSON-LD ----------------------------------------------------------

JSONLD_PATTERN = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)


def _jsonld(base: str, fetcher: Fetcher, max_pages: int, expand_variations: bool) -> list[Product]:
    products: list[Product] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        try:
            html = fetcher.get_text(f"{base}/", params={"page": page})
        except FetchError as exc:
            raise SourceError(f"listing page not reachable ({exc})") from exc
        new_on_page = 0
        for item in extract_jsonld_products(html):
            product = _jsonld_product(base, item)
            if not product.handle or product.handle in seen:
                continue
            seen.add(product.handle)
            products.append(product)
            new_on_page += 1
        if new_on_page == 0:
            break
        _wait(fetcher)
    return products


def extract_jsonld_products(html: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for block in JSONLD_PATTERN.findall(html or ""):
        try:
            payload = json.loads(block.strip())
        except ValueError:
            continue
        for node in _iter_nodes(payload):
            types = node.get("@type")
            type_names = [types] if isinstance(types, str) else list(types or [])
            if any(str(name).lower() == "product" for name in type_names):
                found.append(node)
    return found


def _iter_nodes(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for entry in payload:
            yield from _iter_nodes(entry)
    elif isinstance(payload, dict):
        graph = payload.get("@graph")
        if isinstance(graph, list):
            for entry in graph:
                yield from _iter_nodes(entry)
        yield payload


def _jsonld_product(base: str, item: dict[str, Any]) -> Product:
    url = str(item.get("url") or "")
    handle = _slug_from_url(url) or _slugify(str(item.get("name") or ""))
    offers = item.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    offers = offers if isinstance(offers, dict) else {}
    availability = str(offers.get("availability") or "")
    price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice") or ""
    brand = item.get("brand")
    if isinstance(brand, dict):
        vendor = str(brand.get("name") or "")
    else:
        vendor = str(brand or "")
    categories = item.get("category")
    if isinstance(categories, str):
        tags: tuple[str, ...] = (categories,)
    elif isinstance(categories, list):
        tags = tuple(str(category) for category in categories)
    else:
        tags = ()

    variant = Variant(
        variant_id=str(item.get("sku") or handle),
        sku=str(item.get("sku") or ""),
        title=str(item.get("name") or ""),
        option1="",
        option2="",
        option3="",
        price=str(price),
        compare_at_price="",
        available=availability.endswith("InStock"),
        inventory_quantity="",
    )
    return Product(
        product_id=str(item.get("productID") or item.get("sku") or handle),
        handle=handle,
        title=str(item.get("name") or ""),
        vendor=vendor,
        product_type=str(item.get("category") or ""),
        tags=tags,
        url=url or f"{base}/{handle}",
        image_url=_first_image(item.get("image")),
        updated_at="",
        variants=(variant,),
    )


def _first_image(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("url") or value.get("contentUrl") or "")
    if isinstance(value, list):
        for entry in value:
            found = _first_image(entry)
            if found:
                return found
    return ""


def _slug_from_url(url: str) -> str:
    if not url:
        return ""
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return _slugify(tail)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


_ADAPTERS: dict[str, Callable[[str, Fetcher, int, bool], list[Product]]] = {
    "shopify": _shopify,
    "woo": _woo,
    "jsonld": _jsonld,
}
