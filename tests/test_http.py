from __future__ import annotations

import httpx
import pytest

from catalogwatch.config import load_settings
from catalogwatch.http import FetchError, Fetcher

from fakes import Boom, FakeClient, FakeResponse


def make_fetcher(client, sleeps: list[float] | None = None) -> Fetcher:
    recorded: list[float] = [] if sleeps is None else sleeps
    return Fetcher(
        load_settings(env={"CATALOGWATCH_RETRY_BASE_DELAY": "1"}),
        client=client,
        sleep=recorded.append,
        rand=lambda: 0.0,
    )


def test_retries_on_server_error_then_succeeds():
    client = FakeClient([FakeResponse(503), FakeResponse(503), FakeResponse(200, json_data={"products": []})])
    sleeps: list[float] = []
    fetcher = make_fetcher(client, sleeps)
    assert fetcher.get_json("https://shop.example.com/products.json") == {"products": []}
    assert len(client.calls) == 3
    assert sleeps == [1.0, 2.0]


def test_client_error_is_not_retried():
    client = FakeClient([FakeResponse(404)])
    fetcher = make_fetcher(client)
    with pytest.raises(FetchError) as excinfo:
        fetcher.get_json("https://shop.example.com/products.json")
    assert excinfo.value.status == 404
    assert len(client.calls) == 1


def test_retry_after_header_is_honoured():
    client = FakeClient([FakeResponse(429, headers={"Retry-After": "2"}), FakeResponse(200, json_data=[{"id": 1}])])
    sleeps: list[float] = []
    fetcher = make_fetcher(client, sleeps)
    assert fetcher.get_json("https://woo.example-shop.com/wp-json/wc/store/v1/products") == [{"id": 1}]
    assert sleeps[0] == 2.0


def test_transport_errors_are_retried():
    client = FakeClient(Boom(httpx.ConnectTimeout("timeout"), times=1, then=FakeResponse(200, text="hello")))
    fetcher = make_fetcher(client)
    assert fetcher.get_text("https://shop.example.com/") == "hello"
    assert len(client.calls) == 2


def test_raises_after_exhausting_retries():
    client = FakeClient([FakeResponse(500)])
    fetcher = make_fetcher(client)
    with pytest.raises(FetchError):
        fetcher.get_json("https://shop.example.com/products.json")
    assert len(client.calls) == 4  # 1 try + 3 retries


def test_requests_carry_user_agent_and_timeout():
    client = FakeClient([FakeResponse(200, json_data={})])
    fetcher = make_fetcher(client)
    fetcher.get_json("https://shop.example.com/products.json")
    call = client.calls[0]
    assert "catalogwatch" in call["headers"]["User-Agent"].lower()
    assert call["timeout"] == 20.0
