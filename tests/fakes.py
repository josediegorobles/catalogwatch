"""Test doubles for the HTTP layer. No sockets, no network, fully deterministic."""

from __future__ import annotations

from typing import Any, Callable


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        headers: dict[str, str] | None = None,
        json_data: Any = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self._json = json_data

    @property
    def content(self) -> bytes:
        return self.text.encode("utf-8")

    def json(self) -> Any:
        if self._json is None:
            raise ValueError("no json body in fixture")
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected raise_for_status on {self.status_code}")


class FakeClient:
    """Returns queued responses; records every call.

    `responses` may be a list of FakeResponse (consumed in order, last one repeats)
    or a callable (url, params) -> FakeResponse.
    """

    def __init__(self, responses: list[FakeResponse] | Callable[..., FakeResponse]) -> None:
        self._responses = responses
        self._index = 0
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.calls.append(
            {"url": url, "params": dict(params or {}), "headers": dict(headers or {}), "timeout": timeout}
        )
        if callable(self._responses):
            return self._responses(url, params)
        if not self._responses:
            raise AssertionError("FakeClient ran out of queued responses")
        index = min(self._index, len(self._responses) - 1)
        self._index += 1
        return self._responses[index]

    def close(self) -> None:  # pragma: no cover - parity with httpx.Client
        pass


class Boom:
    """Callable that raises on the first N calls, then delegates to `then`."""

    def __init__(self, error: Exception, times: int, then: FakeResponse) -> None:
        self.error = error
        self.times = times
        self.then = then
        self.seen = 0

    def __call__(self, url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        self.seen += 1
        if self.seen <= self.times:
            raise self.error
        return self.then
