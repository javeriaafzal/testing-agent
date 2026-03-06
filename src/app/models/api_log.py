from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class APILog(Base):
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(String(1024), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    response_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="api_logs")
