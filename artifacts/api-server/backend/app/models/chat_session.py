import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), nullable=False)
    ticket_id: Mapped[str | None] = mapped_column(String, ForeignKey("tickets.ticket_id"), nullable=True)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    messages: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_flow: Mapped[str | None] = mapped_column(String, nullable=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    collected_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
