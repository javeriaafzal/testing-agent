from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class APILogResponse(BaseModel):
    endpoint: str
    method: str
    status_code: int
    latency_ms: int
    response_snippet: str | None

    model_config = {"from_attributes": True}


class ExecutionHistoryResponse(BaseModel):
    status: str
    timestamp: datetime
    failure_reason: str | None
    api_logs: list[APILogResponse]

