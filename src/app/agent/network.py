from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import Page, Request, Response

from app.config import settings

logger = logging.getLogger(__name__)


class NetworkInterceptor:
    """Captures API request/response telemetry for xhr/fetch calls."""

    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []
        self._request_start_times: dict[Request, float] = {}
        self._masked_headers: dict[Request, dict[str, str]] = {}

    def attach(self, page: Page) -> None:
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    def _on_request(self, request: Request) -> None:
        if request.resource_type in {"xhr", "fetch"}:
            self._request_start_times[request] = time.perf_counter()
            self._masked_headers[request] = self._mask_headers(request.headers)

    def _on_response(self, response: Response) -> None:
        request = response.request
        if request.resource_type not in {"xhr", "fetch"}:
            return

        started_at = self._request_start_times.pop(request, None)
        masked_headers = self._masked_headers.pop(request, {})
        latency_ms = int((time.perf_counter() - started_at) * 1000) if started_at is not None else 0

        snippet: str | None
        try:
            snippet = response.text()[: settings.response_snippet_max_chars]
        except Exception:
            snippet = None

        log_entry = {
            "url": request.url,
            "method": request.method,
            "status": response.status,
            "latency_ms": latency_ms,
            "response_snippet": snippet,
            "request_failed": False,
            "request_headers": masked_headers,
        }
        self.logs.append(log_entry)
        logger.info("network_response %s", log_entry)

    def _on_request_failed(self, request: Request) -> None:
        if request.resource_type not in {"xhr", "fetch"}:
            return

        started_at = self._request_start_times.pop(request, None)
        masked_headers = self._masked_headers.pop(request, {})
        latency_ms = int((time.perf_counter() - started_at) * 1000) if started_at is not None else 0
        failure_text = request.failure

        log_entry = {
            "url": request.url,
            "method": request.method,
            "status": 0,
            "latency_ms": latency_ms,
            "response_snippet": str(failure_text)[: settings.response_snippet_max_chars] if failure_text else None,
            "request_failed": True,
            "request_headers": masked_headers,
        }
        self.logs.append(log_entry)
        logger.warning("network_request_failed %s", log_entry)

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        masked = dict(headers)
        for key in list(masked.keys()):
            if key.lower() == "authorization":
                masked[key] = "***"
        return masked
