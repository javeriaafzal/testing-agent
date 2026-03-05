from __future__ import annotations

import uuid

from rq import Connection, Worker

from app.agent.orchestrator import ExecutionOrchestrator
from app.database import SessionLocal
from app.models import Execution, Workflow
from app.workers.queue import QUEUE_NAME, get_redis_connection


def test_job(message: str) -> str:
    return f"test-job:{message}"


def run_workflow_job(workflow_id: str, execution_id: str | None = None) -> str:
    workflow_uuid = uuid.UUID(workflow_id)
    execution_uuid = uuid.UUID(execution_id) if execution_id is not None else None
    db = SessionLocal()

    try:
        workflow = db.get(Workflow, workflow_uuid)
        if workflow is None:
            raise ValueError(f"Workflow {workflow_id} not found")

        execution = db.get(Execution, execution_uuid) if execution_uuid is not None else None
        if execution is not None and execution.workflow_id != workflow_uuid:
            raise ValueError(f"Execution {execution_id} does not belong to workflow {workflow_id}")

        orchestrator = ExecutionOrchestrator()
        execution = orchestrator.run_workflow(db, workflow, execution)
        return str(execution.id)
    finally:
        db.close()


def main() -> None:
    redis_connection = get_redis_connection()
    with Connection(redis_connection):
        worker = Worker([QUEUE_NAME])
        worker.work()


if __name__ == "__main__":
    main()
