from __future__ import annotations

import uuid

from redis import Redis
from rq import Queue
from rq.job import Job

from app.config import settings

QUEUE_NAME = "workflow-executions"


def get_redis_connection() -> Redis:
    return Redis.from_url(settings.redis_url)


def get_workflow_queue() -> Queue:
    return Queue(name=QUEUE_NAME, connection=get_redis_connection())


def enqueue_workflow_run(workflow_id: uuid.UUID) -> Job:
    queue = get_workflow_queue()
    return queue.enqueue("workers.worker.run_workflow_job", str(workflow_id))


def enqueue_test_job(message: str = "queue-online") -> Job:
    queue = get_workflow_queue()
    return queue.enqueue("workers.worker.test_job", message)
