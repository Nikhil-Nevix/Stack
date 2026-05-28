from datetime import datetime, timezone
from typing import Optional
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


def safe_str(val) -> Optional[str]:
    return str(val) if val is not None else None
