from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExecutionStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus, name="execution_status"), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    api_logs: Mapped[list["APILog"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
