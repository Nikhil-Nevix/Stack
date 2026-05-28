"""
Microsoft Teams Bot Framework integration — stub implementation.
Requires TEAMS_APP_ID and TEAMS_APP_PASSWORD.
"""
import httpx
from ..core.config import settings
from ..utils.logger import logger


class TeamsBotService:
    TEAMS_AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    async def get_bot_token(self) -> str:
        if not (settings.TEAMS_APP_ID and settings.TEAMS_APP_PASSWORD):
            logger.warning("Teams Bot credentials not configured")
            return ""
        url = self.TEAMS_AUTH_URL.format(tenant="botframework.com")
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data={
                "grant_type": "client_credentials",
                "client_id": settings.TEAMS_APP_ID,
                "client_secret": settings.TEAMS_APP_PASSWORD,
                "scope": "https://api.botframework.com/.default"
            })
            if resp.status_code == 200:
                return resp.json().get("access_token", "")
        return ""

    async def send_message(self, service_url: str, conversation_id: str, text: str, options: list = None) -> bool:
        logger.info(f"[STUB] Teams send message to {conversation_id}: {text[:50]}...")
        return True

    def build_adaptive_card(self, text: str, options: list = None) -> dict:
        body = [{"type": "TextBlock", "text": text, "wrap": True, "weight": "Bolder"}]
        if options:
            body.append({
                "type": "ActionSet",
                "actions": [{"type": "Action.Submit", "title": opt, "data": {"selection": opt}} for opt in options[:5]]
            })
        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard", "version": "1.4", "body": body}
            }]
        }


teams_service = TeamsBotService()
