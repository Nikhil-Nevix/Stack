"""
Microsoft Graph API service — stub implementation.
Requires GRAPH_API_TENANT_ID, GRAPH_API_CLIENT_ID, GRAPH_API_CLIENT_SECRET.
"""
import httpx
from ..core.config import settings
from ..utils.logger import logger


class GraphAPIService:
    TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    BASE_URL = "https://graph.microsoft.com/v1.0"

    async def _get_token(self) -> str:
        if not (settings.GRAPH_API_TENANT_ID and settings.GRAPH_API_CLIENT_ID and settings.GRAPH_API_CLIENT_SECRET):
            raise RuntimeError("Microsoft Graph API credentials not configured")
        url = self.TOKEN_URL.format(tenant_id=settings.GRAPH_API_TENANT_ID)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data={
                "grant_type": "client_credentials",
                "client_id": settings.GRAPH_API_CLIENT_ID,
                "client_secret": settings.GRAPH_API_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default"
            })
            response.raise_for_status()
            return response.json()["access_token"]

    async def grant_sharepoint_access(self, site_url: str, user_email: str, role: str = "read") -> dict:
        logger.info(f"[STUB] Grant SharePoint access: {user_email} -> {site_url} ({role})")
        return {"status": "success", "message": f"Access granted to {user_email} on {site_url}"}

    async def assign_o365_license(self, user_email: str, sku_id: str) -> dict:
        logger.info(f"[STUB] Assign O365 license: {user_email} -> {sku_id}")
        return {"status": "success", "message": f"License assigned to {user_email}"}

    async def revoke_o365_license(self, user_email: str, sku_id: str) -> dict:
        logger.info(f"[STUB] Revoke O365 license: {user_email} -> {sku_id}")
        return {"status": "success", "message": f"License revoked from {user_email}"}

    async def update_distribution_list(self, dl_email: str, user_email: str, action: str) -> dict:
        logger.info(f"[STUB] DL update: {action} {user_email} {'to' if action == 'add' else 'from'} {dl_email}")
        return {"status": "success", "message": f"DL {action} completed for {user_email}"}

    async def get_user_info(self, email: str) -> dict:
        logger.info(f"[STUB] Get user info: {email}")
        return {"email": email, "displayName": email.split("@")[0].replace(".", " ").title()}


graph_service = GraphAPIService()
