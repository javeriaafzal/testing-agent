from __future__ import annotations

import time
from urllib.parse import urljoin

from playwright.sync_api import Page


class StepExecutor:
    """Executes workflow steps sequentially against a Playwright page."""

    def __init__(self, default_timeout_ms: int) -> None:
        self.default_timeout_ms = default_timeout_ms

    def execute(
        self,
        page: Page,
        base_url: str,
        steps: list[dict],
        *,
        run_timeout_seconds: int | None = None,
    ) -> None:
        started_at = time.monotonic()
        for step in steps:
            if run_timeout_seconds is not None and (time.monotonic() - started_at) > run_timeout_seconds:
                raise TimeoutError(f"Workflow execution timed out after {run_timeout_seconds} seconds")

            action = step.get("action")
            timeout = step.get("timeout_ms", self.default_timeout_ms)

            if action == "goto":
                target_url = step.get("url", base_url)
                if isinstance(target_url, str) and not target_url.startswith(("http://", "https://")):
                    target_url = urljoin(base_url, target_url)
                page.goto(target_url, timeout=timeout)
            elif action == "click":
                page.click(step["selector"], timeout=timeout)
            elif action == "fill":
                page.fill(step["selector"], step["value"], timeout=timeout)
            elif action == "wait_for_selector":
                page.wait_for_selector(step["selector"], timeout=timeout)
            elif action == "wait_for_navigation":
                page.wait_for_navigation(timeout=timeout)
            else:
                raise ValueError(f"Unsupported action: {action}")
