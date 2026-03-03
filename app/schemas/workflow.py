from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowBase(BaseModel):
    name: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    steps: list[dict] = Field(default_factory=list)
    latency_threshold_ms: int = Field(gt=0)


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowResponse(WorkflowBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
