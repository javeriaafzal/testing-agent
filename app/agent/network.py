from __future__ import annotations

import time
from typing import Any

from playwright.sync_api import Page, Request, Response


class NetworkInterceptor:
    """Captures API request/response telemetry for xhr/fetch calls."""

    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []
        self._request_start_times: dict[Request, float] = {}

    def attach(self, page: Page) -> None:
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    def _on_request(self, request: Request) -> None:
        if request.resource_type in {"xhr", "fetch"}:
            self._request_start_times[request] = time.perf_counter()

    def _on_response(self, response: Response) -> None:
        request = response.request
        if request.resource_type not in {"xhr", "fetch"}:
            return

        started_at = self._request_start_times.pop(request, None)
        latency_ms = int((time.perf_counter() - started_at) * 1000) if started_at is not None else 0

        snippet: str | None
        try:
            snippet = response.text()[:500]
        except Exception:
            snippet = None

        self.logs.append(
            {
                "url": request.url,
                "method": request.method,
                "status": response.status,
                "latency_ms": latency_ms,
                "response_snippet": snippet,
                "request_failed": False,
            }
        )

    def _on_request_failed(self, request: Request) -> None:
        if request.resource_type not in {"xhr", "fetch"}:
            return

        started_at = self._request_start_times.pop(request, None)
        latency_ms = int((time.perf_counter() - started_at) * 1000) if started_at is not None else 0
        failure_text = request.failure

        self.logs.append(
            {
                "url": request.url,
                "method": request.method,
                "status": 0,
                "latency_ms": latency_ms,
                "response_snippet": str(failure_text)[:500] if failure_text else None,
                "request_failed": True,
            }
        )
