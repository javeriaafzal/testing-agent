from __future__ import annotations

from typing import Any


def evaluate_api_logs(logs: list[dict[str, Any]], latency_threshold_ms: int) -> dict[str, Any] | None:
    for log in logs:
        if log.get("request_failed"):
            return {
                "type": "REQUEST_FAILURE",
                "endpoint": log.get("url"),
                "method": log.get("method"),
            }

        status_code = int(log.get("status", 0))
        if status_code < 200 or status_code > 299:
            return {
                "type": "STATUS_FAILURE",
                "endpoint": log.get("url"),
                "status_code": status_code,
            }

        latency_ms = int(log.get("latency_ms", 0))
        if latency_ms > latency_threshold_ms:
            return {
                "type": "LATENCY_FAILURE",
                "endpoint": log.get("url"),
                "latency_ms": latency_ms,
                "threshold_ms": latency_threshold_ms,
            }

    return None
