"""
WinRM PowerShell execution service — stub implementation.
Requires WINRM_USERNAME and WINRM_PASSWORD.
"""
from ..core.config import settings
from ..utils.logger import logger


class WinRMService:
    def __init__(self):
        self.username = settings.WINRM_USERNAME
        self.password = settings.WINRM_PASSWORD

    async def execute_script(self, device_name: str, script: str) -> dict:
        logger.info(f"[STUB] Execute PowerShell on {device_name}")
        if not (self.username and self.password):
            return {
                "status": "stub",
                "output": f"[STUB] PowerShell would execute on {device_name}. WinRM credentials not configured.",
                "exit_code": 0
            }
        try:
            import winrm
            session = winrm.Session(device_name, auth=(self.username, self.password), transport="ntlm")
            result = session.run_ps(script)
            return {
                "status": "success" if result.status_code == 0 else "failed",
                "output": result.std_out.decode("utf-8"),
                "error": result.std_err.decode("utf-8"),
                "exit_code": result.status_code
            }
        except Exception as e:
            logger.error(f"WinRM error on {device_name}: {e}")
            return {"status": "failed", "output": str(e), "exit_code": 1}


winrm_service = WinRMService()
