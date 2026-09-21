"""HTTP layer: timeouts, anti-blocking headers, exponential backoff and Retry-After support."""

from __future__ import annotations

import random
import time
from typing import Any, Callable

import httpx

from .config import Settings

RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class FetchError(RuntimeError):
    def __init__(self, message: str, url: str | None = None, status: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.status = status


class Fetcher:
    """Thin HTTP client with retries. Injects a client, sleep and jitter source for tests."""

    def __init__(
        self,
        settings: Settings,
        client: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        self.settings = settings
        self._client = client if client is not None else httpx.Client(follow_redirects=True)
        self._sleep = sleep
        self._rand = rand

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Fetcher":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def pause(self) -> None:
        """Polite delay between paginated requests (uses the injected sleep in tests)."""
        delay = self.settings.page_delay
        if delay > 0:
            self._sleep(delay)

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self._request(url, params)
        try:
            return response.json()
        except ValueError as exc:
            raise FetchError(f"invalid JSON from {url}: {exc}", url=url) from exc

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        return self._request(url, params).text

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.user_agent,
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        }

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        base = self.settings.retry_base_delay * (2**attempt)
        return base + self._rand() * 0.25

    def _request(self, url: str, params: dict[str, Any] | None) -> Any:
        attempt = 0
        while True:
            try:
                response = self._client.get(
                    url,
                    params=params,
                    headers=self._headers(),
                    timeout=self.settings.request_timeout,
                )
            except httpx.HTTPError as exc:
                if attempt >= self.settings.max_retries:
                    raise FetchError(f"request failed after {attempt + 1} attempts: {exc}", url=url) from exc
                self._sleep(self._backoff(attempt, None))
                attempt += 1
                continue

            if response.status_code in RETRY_STATUS and attempt < self.settings.max_retries:
                self._sleep(self._backoff(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue

            if response.status_code >= 400:
                raise FetchError(f"HTTP {response.status_code} for {url}", url=url, status=response.status_code)

            return response
