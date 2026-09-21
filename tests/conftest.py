from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def shopify_page1():
    return fixture_json("shopify_page1.json")


@pytest.fixture
def shopify_page2():
    return fixture_json("shopify_page2.json")


@pytest.fixture
def woo_page1():
    return fixture_json("woo_page1.json")


@pytest.fixture
def woo_variable():
    return fixture_json("woo_variable.json")


@pytest.fixture
def jsonld_html():
    return fixture_text("jsonld_listing.html")
