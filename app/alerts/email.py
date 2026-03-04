from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any, Callable

from app.config import settings


class EmailAlertService:
    """Send workflow failure alerts through SMTP."""

    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        from_email: str,
        to_email: str,
        smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_email = to_email
        self.smtp_factory = smtp_factory

    @classmethod
    def from_settings(cls) -> "EmailAlertService":
        return cls(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            from_email=settings.alert_from_email,
            to_email=settings.alert_to_email,
        )

    def send_failure_alert(
        self,
        *,
        workflow_name: str,
        endpoint: str,
        status: int | None,
        latency_ms: int | None,
        screenshot_link: str | None,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = f"[Watchdog] Workflow failure: {workflow_name}"
        message["From"] = self.from_email
        message["To"] = self.to_email
        message.set_content(
            "\n".join(
                [
                    "Critical workflow failure detected.",
                    "",
                    f"Workflow name: {workflow_name}",
                    f"Endpoint: {endpoint}",
                    f"Status: {status if status is not None else 'N/A'}",
                    f"Latency: {latency_ms if latency_ms is not None else 'N/A'} ms",
                    f"Screenshot link: {screenshot_link or 'N/A'}",
                ]
            )
        )

        with self.smtp_factory(self.smtp_host, self.smtp_port) as smtp:
            smtp.send_message(message)


def build_alert_payload(failure: dict[str, Any], logs: list[dict[str, Any]]) -> dict[str, int | str | None]:
    endpoint = str(failure.get("endpoint") or "")
    matched_log = next((log for log in logs if str(log.get("url")) == endpoint), None)

    status = failure.get("status_code")
    if status is None and matched_log is not None:
        status = matched_log.get("status")

    latency_ms = failure.get("latency_ms")
    if latency_ms is None and matched_log is not None:
        latency_ms = matched_log.get("latency_ms")

    return {
        "endpoint": endpoint,
        "status": int(status) if status is not None else None,
        "latency_ms": int(latency_ms) if latency_ms is not None else None,
    }
