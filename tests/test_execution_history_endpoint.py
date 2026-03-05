from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.main import list_workflow_executions
from app.models import APILog, Execution, ExecutionStatus, Workflow


class FakeExecutionQuery:
    def __init__(self, executions: list[Execution]) -> None:
        self.executions = executions

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self) -> list[Execution]:
        return self.executions


class FakeDBSession:
    def __init__(self, workflow: Workflow | None, executions: list[Execution]) -> None:
        self.workflow = workflow
        self.executions = executions

    def get(self, model, value):
        return self.workflow

    def query(self, model):
        return FakeExecutionQuery(self.executions)


class ExecutionHistoryEndpointTests(unittest.TestCase):
    def test_history_returns_status_timestamp_failure_reason_and_api_logs(self) -> None:
        workflow_id = uuid.uuid4()
        workflow = Workflow(
            id=workflow_id,
            name="Checkout",
            base_url="https://example.test",
            config_json={"steps": []},
            latency_threshold_ms=1000,
        )
        execution = Execution(
            workflow_id=workflow_id,
            status=ExecutionStatus.FAIL,
            started_at=datetime(2026, 3, 5, 10, 30, tzinfo=timezone.utc),
            failure_reason='{"reason":"500"}',
        )
        execution.api_logs = [
            APILog(
                endpoint="https://example.test/api/orders",
                method="GET",
                status_code=500,
                latency_ms=215,
                response_snippet="internal error",
            )
        ]
        db = FakeDBSession(workflow, [execution])

        response = list_workflow_executions(workflow_id, db)

        self.assertEqual(1, len(response))
        self.assertEqual("FAIL", response[0].status)
        self.assertEqual(execution.started_at, response[0].timestamp)
        self.assertEqual('{"reason":"500"}', response[0].failure_reason)
        self.assertEqual(1, len(response[0].api_logs))
        self.assertEqual("https://example.test/api/orders", response[0].api_logs[0].endpoint)

    def test_history_raises_not_found_when_workflow_is_missing(self) -> None:
        db = FakeDBSession(None, [])

        with self.assertRaises(HTTPException) as ctx:
            list_workflow_executions(uuid.uuid4(), db)

        self.assertEqual(404, ctx.exception.status_code)
        self.assertEqual("Workflow not found", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
