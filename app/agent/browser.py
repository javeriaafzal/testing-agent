from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserSession:
    """Thin synchronous Playwright wrapper for workflow execution."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def open_page(self, base_url: str) -> Page:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context()
        page = self._context.new_page()
        page.goto(base_url)
        return page

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> "BrowserSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
