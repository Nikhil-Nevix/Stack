import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class AIResolution(Base):
    __tablename__ = "ai_resolutions"

    resolution_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.ticket_id"), nullable=False)
    intent_detected: Mapped[str | None] = mapped_column(String, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    sop_matched: Mapped[str | None] = mapped_column(String, ForeignKey("sops.sop_id"), nullable=True)
    sop_title: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    intent_clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sop_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    historical_success_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    resolution_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String, nullable=True)
    execution_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
