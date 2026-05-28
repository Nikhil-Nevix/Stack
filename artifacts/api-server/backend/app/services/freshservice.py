"""
Freshservice API integration — stub implementation.
Requires FRESHSERVICE_BASE_URL and FRESHSERVICE_API_KEY.
"""
import httpx
import base64
from ..core.config import settings
from ..utils.logger import logger


class FreshserviceService:
    def __init__(self):
        self.base_url = settings.FRESHSERVICE_BASE_URL
        self.api_key = settings.FRESHSERVICE_API_KEY

    def _auth_header(self) -> dict:
        if not (self.base_url and self.api_key):
            return {}
        creds = base64.b64encode(f"{self.api_key}:X".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

    async def create_ticket(self, subject: str, description: str, requester_email: str,
                             priority: int = 2, status: int = 2) -> dict:
        logger.info(f"[STUB] Create Freshservice ticket: {subject} for {requester_email}")
        return {"id": 9999, "display_id": "INC-9999", "subject": subject}

    async def update_ticket(self, ticket_id: int, status: int = None, note: str = None) -> dict:
        logger.info(f"[STUB] Update Freshservice ticket {ticket_id}")
        return {"id": ticket_id, "status": status}

    async def add_note(self, ticket_id: int, note: str, private: bool = True) -> dict:
        logger.info(f"[STUB] Add note to Freshservice ticket {ticket_id}")
        return {"id": 1, "note": note}


freshservice_service = FreshserviceService()
