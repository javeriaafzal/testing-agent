from __future__ import annotations

import logging

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

logger = logging.getLogger(__name__)


class BrowserSession:
    """Thin synchronous Playwright wrapper for workflow execution."""

    def __init__(self, page_timeout_ms: int) -> None:
        self.page_timeout_ms = page_timeout_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def open_page(self, base_url: str) -> Page:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context()
        page = self._context.new_page()
        page.set_default_timeout(self.page_timeout_ms)
        page.goto(base_url, timeout=self.page_timeout_ms)
        return page

    def close(self) -> None:
        context = self._context
        browser = self._browser
        playwright = self._playwright
        self._context = None
        self._browser = None
        self._playwright = None

        try:
            if context is not None:
                context.close()
        except Exception:
            logger.exception("failed to close browser context")

        try:
            if browser is not None:
                browser.close()
        except Exception:
            logger.exception("failed to close browser instance")

        try:
            if playwright is not None:
                playwright.stop()
        except Exception:
            logger.exception("failed to stop playwright")

    def __enter__(self) -> "BrowserSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
