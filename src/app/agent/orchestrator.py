from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session, object_session

from app.agent.browser import BrowserSession
from app.agent.evaluator import evaluate_api_logs
from app.agent.network import NetworkInterceptor
from app.agent.step_executor import StepExecutor
from app.alerts.email import EmailAlertService, build_alert_payload
from app.config import settings
from app.models import APILog, Execution, ExecutionStatus, Workflow

logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    def __init__(
        self,
        screenshot_dir: str = "artifacts/screenshots",
        email_alert_service: EmailAlertService | None = None,
    ) -> None:
        self.screenshot_dir = Path(screenshot_dir)
        self.step_executor = StepExecutor(default_timeout_ms=settings.api_timeout_seconds * 1000)
        self.page_timeout_ms = settings.api_timeout_seconds * 1000
        self.workflow_run_timeout_seconds = settings.workflow_run_timeout_seconds
        self.email_alert_service = email_alert_service or EmailAlertService.from_settings()

    def run(self, workflow: Workflow) -> Execution:
        db = object_session(workflow)
        if db is None:
            raise RuntimeError("Workflow is not attached to an active database session")
        return self.run_workflow(db, workflow)

    def run_workflow(self, db: Session, workflow: Workflow, execution: Execution | None = None) -> Execution:
        if execution is None:
            execution = Execution(workflow_id=workflow.id, status=ExecutionStatus.RUNNING)
        else:
            execution.status = ExecutionStatus.RUNNING
            execution.failure_reason = None
            execution.screenshot_path = None

        db.add(execution)
        db.commit()
        db.refresh(execution)

        logger.info("execution_started workflow_id=%s execution_id=%s", workflow.id, execution.id)
        interceptor = NetworkInterceptor()
        page = None

        try:
            with BrowserSession(page_timeout_ms=self.page_timeout_ms) as browser:
                page = browser.open_page(workflow.base_url)
                interceptor.attach(page)
                steps = workflow.config_json.get("steps", []) if isinstance(workflow.config_json, dict) else []
                self.step_executor.execute(
                    page,
                    workflow.base_url,
                    steps,
                    run_timeout_seconds=self.workflow_run_timeout_seconds,
                )

                failure = evaluate_api_logs(interceptor.logs, workflow.latency_threshold_ms)
                self._save_api_logs(db, execution, interceptor.logs)

                if failure is not None:
                    execution.status = ExecutionStatus.FAIL
                    execution.failure_reason = json.dumps(failure)
                    execution.screenshot_path = self._capture_screenshot(page, execution.id.hex)
                    self._send_failure_alert(workflow, failure, interceptor.logs, execution.screenshot_path)
                    logger.warning("execution_failed execution_id=%s reason=%s", execution.id, execution.failure_reason)
                else:
                    execution.status = ExecutionStatus.PASS
                    execution.failure_reason = None
                    logger.info("execution_passed execution_id=%s", execution.id)
        except Exception as exc:
            execution.status = ExecutionStatus.FAIL
            execution.failure_reason = str(exc)
            if page is not None:
                execution.screenshot_path = self._capture_screenshot(page, execution.id.hex)
            self._save_api_logs(db, execution, interceptor.logs)
            logger.exception("execution_exception execution_id=%s", execution.id)
        finally:
            execution.completed_at = datetime.now(timezone.utc)
            db.add(execution)
            db.commit()
            db.refresh(execution)
            logger.info("execution_completed execution_id=%s status=%s", execution.id, execution.status.value)

        return execution

    def _send_failure_alert(
        self,
        workflow: Workflow,
        failure: dict,
        logs: list[dict],
        screenshot_path: str | None,
    ) -> None:
        payload = build_alert_payload(failure, logs)
        self.email_alert_service.send_failure_alert(
            workflow_name=workflow.name,
            endpoint=str(payload["endpoint"]),
            status=payload["status"],
            latency_ms=payload["latency_ms"],
            screenshot_link=screenshot_path,
        )

    def _save_api_logs(self, db: Session, execution: Execution, logs: list[dict]) -> None:
        for log in logs:
            api_log = APILog(
                execution_id=execution.id,
                endpoint=log.get("url", ""),
                method=log.get("method", ""),
                status_code=int(log.get("status", 0)),
                latency_ms=int(log.get("latency_ms", 0)),
                response_snippet=log.get("response_snippet"),
            )
            db.add(api_log)
        db.commit()

    def _capture_screenshot(self, page, execution_id: str) -> str:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.screenshot_dir / f"{execution_id}.png"
        page.screenshot(path=str(path), full_page=True)
        return str(path)
