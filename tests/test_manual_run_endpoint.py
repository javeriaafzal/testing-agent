from __future__ import annotations

import unittest
import uuid
from unittest.mock import patch

from app.main import run_workflow
from app.models import ExecutionStatus, Workflow


class FakeDBSession:
    def __init__(self, workflow: Workflow | None) -> None:
        self.workflow = workflow
        self.saved_execution = None

    def get(self, model, value):
        return self.workflow

    def add(self, obj) -> None:
        self.saved_execution = obj

    def commit(self) -> None:
        return None

    def refresh(self, obj) -> None:
        return None


class FakeJob:
    def __init__(self) -> None:
        self.id = "job-123"
        self.origin = "workflow-executions"


class ManualRunEndpointTests(unittest.TestCase):
    def test_run_endpoint_enqueues_job_and_creates_queued_execution(self) -> None:
        workflow_id = uuid.uuid4()
        workflow = Workflow(
            id=workflow_id,
            name="Checkout",
            base_url="https://example.test",
            config_json={"steps": []},
            latency_threshold_ms=1000,
        )
        db = FakeDBSession(workflow)

        with patch("app.main.enqueue_workflow_run", return_value=FakeJob()) as enqueue_mock:
            response = run_workflow(workflow_id, db)

        self.assertIsNotNone(db.saved_execution)
        self.assertEqual(ExecutionStatus.QUEUED, db.saved_execution.status)
        enqueue_mock.assert_called_once_with(workflow_id, db.saved_execution.id)
        self.assertEqual(str(workflow_id), response["workflow_id"])
        self.assertEqual(str(db.saved_execution.id), response["execution_id"])
        self.assertEqual("job-123", response["job_id"])


if __name__ == "__main__":
    unittest.main()
