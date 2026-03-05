from __future__ import annotations

import unittest
from unittest.mock import patch

from app.agent.network import NetworkInterceptor
from app.agent.step_executor import StepExecutor


class FakeRequest:
    def __init__(self, *, resource_type: str = "xhr", headers: dict[str, str] | None = None, failure=None) -> None:
        self.resource_type = resource_type
        self.headers = headers or {}
        self.url = "https://example.test/api/orders"
        self.method = "GET"
        self.failure = failure


class FakeResponse:
    def __init__(self, request: FakeRequest, status: int = 500, text: str = "") -> None:
        self.request = request
        self.status = status
        self._text = text

    def text(self) -> str:
        return self._text


class FakePage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def goto(self, url, timeout=None):
        self.calls.append(("goto", timeout))


class HardeningTests(unittest.TestCase):
    def test_network_interceptor_masks_authorization_and_truncates_snippet(self) -> None:
        interceptor = NetworkInterceptor()
        request = FakeRequest(headers={"Authorization": "Bearer abc", "X-Test": "1"})

        interceptor._on_request(request)
        interceptor._on_response(FakeResponse(request=request, status=500, text="x" * 999))

        self.assertEqual("***", interceptor.logs[0]["request_headers"]["Authorization"])
        self.assertEqual(300, len(interceptor.logs[0]["response_snippet"]))

    def test_step_executor_uses_default_timeout(self) -> None:
        page = FakePage()
        executor = StepExecutor(default_timeout_ms=4321)

        executor.execute(page, "https://example.test", [{"action": "goto", "url": "/health"}])

        self.assertEqual([("goto", 4321)], page.calls)

    def test_step_executor_honors_run_timeout(self) -> None:
        page = FakePage()
        executor = StepExecutor(default_timeout_ms=1000)

        with patch("app.agent.step_executor.time.monotonic", side_effect=[0.0, 2.0]):
            with self.assertRaises(TimeoutError):
                executor.execute(
                    page,
                    "https://example.test",
                    [{"action": "goto", "url": "/health"}],
                    run_timeout_seconds=1,
                )


if __name__ == "__main__":
    unittest.main()
