import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class PowershellExecution(Base):
    __tablename__ = "powershell_executions"

    execution_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.ticket_id"), nullable=False)
    resolution_id: Mapped[str | None] = mapped_column(String, ForeignKey("ai_resolutions.resolution_id"), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String, nullable=True)
    device_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    script_name: Mapped[str] = mapped_column(String, nullable=False)
    script_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(String, nullable=False)
    output_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
