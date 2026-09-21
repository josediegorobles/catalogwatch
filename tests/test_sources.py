from __future__ import annotations

import pytest

from catalogwatch.config import load_settings
from catalogwatch.http import Fetcher
from catalogwatch.sources import SourceError, fetch_catalog

from fakes import FakeClient, FakeResponse

STORE = "https://shop.example.com"


def make_fetcher(router) -> Fetcher:
    return Fetcher(load_settings(env={}), client=FakeClient(router), sleep=lambda _: None, rand=lambda: 0.0)


def shopify_router(page1, page2):
    def route(url, params):
        page = int((params or {}).get("page", 1))
        return FakeResponse(200, json_data=page1 if page == 1 else page2)

    return route


def test_shopify_catalog_is_paginated_and_normalised(shopify_page1, shopify_page2):
    fetcher = make_fetcher(shopify_router(shopify_page1, shopify_page2))
    catalog = fetch_catalog(STORE, fetcher)

    assert catalog.source == "shopify"
    assert catalog.store == STORE
    assert len(catalog.products) == 2

    shoe = catalog.products[0]
    assert shoe.title == "Trail Runner 2"
    assert shoe.handle == "trail-runner-2"
    assert shoe.vendor == "Northbound"
    assert shoe.product_type == "Shoes"
    assert shoe.tags == ("trail", "running")
    assert shoe.url == f"{STORE}/products/trail-runner-2"
    assert shoe.image_url == "https://cdn.example-shop.com/products/trail-runner-2-1.jpg"
    assert len(shoe.variants) == 2
    assert shoe.variants[0].sku == "NB-TR2-42-BLK"
    assert shoe.variants[0].price == "129.00"
    assert shoe.variants[0].available is True
    assert shoe.variants[1].available is False
    assert shoe.variants[1].compare_at_price == ""

    sock = catalog.products[1]
    assert len(sock.variants) == 1
    assert sock.variants[0].sku == ""
    assert sock.image_url == ""


def test_shopify_pagination_stops_at_max_pages(shopify_page1):
    fetcher = make_fetcher(shopify_router(shopify_page1, shopify_page1))
    catalog = fetch_catalog(STORE, fetcher, max_pages=2)
    assert len(catalog.products) == 4


def test_auto_detects_woocommerce_when_shopify_endpoint_is_missing(woo_page1):
    def route(url, params):
        if "products.json" in url:
            return FakeResponse(404, text="Not Found")
        page = int((params or {}).get("page", 1))
        return FakeResponse(200, json_data=woo_page1 if page == 1 else [])

    catalog = fetch_catalog(STORE, make_fetcher(route))
    assert catalog.source == "woo"
    assert len(catalog.products) == 2

    mug = catalog.products[0]
    assert mug.title == "Ceramic Mug 350ml"
    assert mug.variants[0].sku == "MUG-350-WHT"
    assert mug.variants[0].price == "19.99"
    assert mug.variants[0].compare_at_price == "24.99"
    assert mug.variants[0].available is True
    assert mug.image_url == "https://woo.example-shop.com/img/mug.jpg"
    assert mug.tags == ("new",)

    apron = catalog.products[1]
    assert apron.variants[0].sku == ""
    assert apron.variants[0].available is False


def test_woo_variable_product_variations_can_be_expanded(woo_variable):
    def route(url, params):
        if "products.json" in url:
            return FakeResponse(404, text="Not Found")
        if url.rstrip("/").endswith("/products/205"):
            return FakeResponse(200, json_data=woo_variable)
        page = int((params or {}).get("page", 1))
        if page == 1:
            parent = dict(woo_variable)
            parent["variations"] = [{"id": 206}, {"id": 207}]
            return FakeResponse(200, json_data=[parent])
        return FakeResponse(200, json_data=[])

    catalog = fetch_catalog(STORE, make_fetcher(route), expand_variations=True)
    tee = catalog.products[0]
    assert len(tee.variants) == 2
    assert tee.variants[0].sku == "TEE-S-BLK"
    assert tee.variants[0].option1 == "S"
    assert tee.variants[0].option2 == "Black"
    assert tee.variants[1].available is False


def test_jsonld_fallback_reads_product_scripts(jsonld_html):
    def route(url, params):
        if "products.json" in url or "wp-json" in url:
            return FakeResponse(404, text="Not Found")
        page = int((params or {}).get("page", 1))
        return FakeResponse(200, text=jsonld_html if page == 1 else "<html></html>")

    catalog = fetch_catalog(STORE, make_fetcher(route))
    assert catalog.source == "jsonld"
    assert [p.title for p in catalog.products] == ["Field Notebook A5", "Brass Pencil"]

    notebook = catalog.products[0]
    assert notebook.variants[0].sku == "NB-A5-KRAFT"
    assert notebook.variants[0].price == "12.50"
    assert notebook.variants[0].available is True
    assert notebook.image_url == "https://generic.example-shop.com/img/notebook.jpg"
    assert notebook.vendor == "Paperbound"

    pencil = catalog.products[1]
    assert pencil.variants[0].price == "8.00"
    assert pencil.variants[0].available is False


def test_raises_when_no_source_matches():
    fetcher = make_fetcher(lambda url, params: FakeResponse(404, text="nope"))
    with pytest.raises(SourceError):
        fetch_catalog(STORE, fetcher)
