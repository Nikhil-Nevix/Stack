import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Float, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class ROIMetric(Base):
    __tablename__ = "roi_metrics"

    metric_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)
    auto_resolved_count: Mapped[int] = mapped_column(Integer, default=0)
    manual_resolved_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_auto_resolution_mins: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_manual_resolution_mins: Mapped[float | None] = mapped_column(Float, nullable=True)
    hours_saved: Mapped[float] = mapped_column(Float, default=0.0)
    cost_saved: Mapped[float] = mapped_column(Float, default=0.0)
    agent_hourly_cost: Mapped[float] = mapped_column(Float, default=500.0)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
