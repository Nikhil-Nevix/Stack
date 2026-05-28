import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class ConfidenceThreshold(Base):
    __tablename__ = "confidence_thresholds"

    threshold_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    use_case: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    auto_resolve_min: Mapped[float] = mapped_column(Float, default=85.0)
    review_after_min: Mapped[float] = mapped_column(Float, default=60.0)
    updated_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.user_id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
