from __future__ import annotations

import unittest

from app.alerts.email import EmailAlertService, build_alert_payload


class FakeSMTP:
    sent_messages = []

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def send_message(self, message) -> None:
        FakeSMTP.sent_messages.append(message)


class EmailAlertServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeSMTP.sent_messages = []

    def test_send_email_on_simulated_500_error(self) -> None:
        service = EmailAlertService(
            smtp_host="smtp.test",
            smtp_port=2525,
            from_email="watchdog@test.local",
            to_email="oncall@test.local",
            smtp_factory=FakeSMTP,
        )
        failure = {"type": "STATUS_FAILURE", "endpoint": "https://api.test.local/orders", "status_code": 500}
        logs = [{"url": "https://api.test.local/orders", "status": 500, "latency_ms": 187}]
        payload = build_alert_payload(failure, logs)

        service.send_failure_alert(
            workflow_name="Checkout Workflow",
            endpoint=str(payload["endpoint"]),
            status=payload["status"],
            latency_ms=payload["latency_ms"],
            screenshot_link="https://cdn.test.local/screenshot/123.png",
        )

        self.assertEqual(1, len(FakeSMTP.sent_messages))

    def test_email_contains_structured_alert_data(self) -> None:
        service = EmailAlertService(
            smtp_host="smtp.test",
            smtp_port=2525,
            from_email="watchdog@test.local",
            to_email="oncall@test.local",
            smtp_factory=FakeSMTP,
        )

        service.send_failure_alert(
            workflow_name="Checkout Workflow",
            endpoint="https://api.test.local/orders",
            status=500,
            latency_ms=187,
            screenshot_link="https://cdn.test.local/screenshot/123.png",
        )

        message_text = FakeSMTP.sent_messages[0].get_content()
        self.assertIn("Workflow name: Checkout Workflow", message_text)
        self.assertIn("Endpoint: https://api.test.local/orders", message_text)
        self.assertIn("Status: 500", message_text)
        self.assertIn("Latency: 187 ms", message_text)
        self.assertIn("Screenshot link: https://cdn.test.local/screenshot/123.png", message_text)


if __name__ == "__main__":
    unittest.main()
