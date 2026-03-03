from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.agent.browser import BrowserSession
from app.agent.evaluator import evaluate_api_logs
from app.agent.network import NetworkInterceptor
from app.agent.step_executor import StepExecutor
from app.models import APILog, Execution, ExecutionStatus, Workflow


class ExecutionOrchestrator:
    def __init__(self, screenshot_dir: str = "artifacts/screenshots") -> None:
        self.screenshot_dir = Path(screenshot_dir)
        self.step_executor = StepExecutor()

    def run_workflow(self, db: Session, workflow: Workflow) -> Execution:
        execution = Execution(workflow_id=workflow.id, status=ExecutionStatus.FAIL)
        db.add(execution)
        db.commit()
        db.refresh(execution)

        interceptor = NetworkInterceptor()
        page = None

        try:
            with BrowserSession() as browser:
                page = browser.open_page(workflow.base_url)
                interceptor.attach(page)
                steps = workflow.config_json.get("steps", []) if isinstance(workflow.config_json, dict) else []
                self.step_executor.execute(page, workflow.base_url, steps)

                failure = evaluate_api_logs(interceptor.logs, workflow.latency_threshold_ms)
                self._save_api_logs(db, execution, interceptor.logs)

                if failure is not None:
                    execution.status = ExecutionStatus.FAIL
                    execution.failure_reason = json.dumps(failure)
                    execution.screenshot_path = self._capture_screenshot(page, execution.id.hex)
                else:
                    execution.status = ExecutionStatus.PASS
                    execution.failure_reason = None
        except Exception as exc:
            execution.status = ExecutionStatus.FAIL
            execution.failure_reason = str(exc)
            if page is not None:
                execution.screenshot_path = self._capture_screenshot(page, execution.id.hex)
            self._save_api_logs(db, execution, interceptor.logs)
        finally:
            execution.completed_at = datetime.now(timezone.utc)
            db.add(execution)
            db.commit()
            db.refresh(execution)

        return execution

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
