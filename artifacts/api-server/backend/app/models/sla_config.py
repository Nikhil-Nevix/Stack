import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class SLAConfig(Base):
    __tablename__ = "sla_configs"
    __table_args__ = (UniqueConstraint("use_case", "priority"),)

    sla_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    use_case: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    warning_threshold_percent: Mapped[float] = mapped_column(Float, default=75.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
