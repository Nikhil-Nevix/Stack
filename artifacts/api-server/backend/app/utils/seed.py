"""
Initial data seeder — runs at startup, idempotent.
Creates default users, agent groups, thresholds, and SLA configs.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import AsyncSessionLocal
from ..core.security import get_password_hash
from ..models.user import User
from ..models.agent_group import AgentGroup
from ..models.agent_group_member import AgentGroupMember
from ..models.confidence_threshold import ConfidenceThreshold
from ..models.sla_config import SLAConfig
from ..models.sop import SOP
from ..utils.logger import logger


ADMIN_USERS = [
    {"email": "admin@jadeglobal.com", "full_name": "STACK Administrator", "role": "admin",
     "department": "IT Operations", "password": "Admin@Stack2025"},
]

AGENT_USERS = [
    {"email": "rajesh.kumar@jadeglobal.com", "full_name": "Rajesh Kumar", "role": "agent", "department": "IT Support"},
    {"email": "priya.sharma@jadeglobal.com", "full_name": "Priya Sharma", "role": "agent", "department": "IT Support"},
    {"email": "amit.patel@jadeglobal.com", "full_name": "Amit Patel", "role": "agent", "department": "IT Support"},
    {"email": "sneha.gupta@jadeglobal.com", "full_name": "Sneha Gupta", "role": "agent", "department": "IT Support"},
    {"email": "vikram.singh@jadeglobal.com", "full_name": "Vikram Singh", "role": "agent", "department": "IT Support"},
    {"email": "ananya.reddy@jadeglobal.com", "full_name": "Ananya Reddy", "role": "agent", "department": "IT Support"},
    {"email": "rahul.verma@jadeglobal.com", "full_name": "Rahul Verma", "role": "agent", "department": "IT Support"},
    {"email": "kavya.nair@jadeglobal.com", "full_name": "Kavya Nair", "role": "agent", "department": "IT Support"},
    {"email": "arun.menon@jadeglobal.com", "full_name": "Arun Menon", "role": "agent", "department": "IT Support"},
]

END_USERS = [
    {"email": "testuser@jadeglobal.com", "full_name": "Test User", "role": "user",
     "department": "Engineering", "password": "Test@Stack2025"},
    {"email": "datta@jadeglobal.com", "full_name": "Datta Bagade", "role": "user",
     "department": "IT Operations", "password": "Datta@Stack2025"},
]

GROUPS = [
    {"group_name": "SharePoint Support", "use_case": "sharepoint_access", "assignment_mode": "round_robin",
     "agents": ["rajesh.kumar@jadeglobal.com", "priya.sharma@jadeglobal.com"]},
    {"group_name": "License Management", "use_case": "license_o365", "assignment_mode": "round_robin",
     "agents": ["amit.patel@jadeglobal.com", "sneha.gupta@jadeglobal.com"]},
    {"group_name": "DL Management", "use_case": "dl_update", "assignment_mode": "round_robin",
     "agents": ["vikram.singh@jadeglobal.com", "ananya.reddy@jadeglobal.com"]},
    {"group_name": "L2 Windows Support", "use_case": "windows_troubleshooting", "assignment_mode": "round_robin",
     "agents": ["rahul.verma@jadeglobal.com", "kavya.nair@jadeglobal.com"]},
]

USE_CASES = [
    "sharepoint_access", "sharepoint_admin",
    "license_bluebeam", "license_adobe", "license_o365",
    "dl_update", "windows_troubleshooting"
]

PRIORITIES = ["low", "medium", "high", "urgent"]
SLA_HOURS = {"low": 8, "medium": 4, "high": 2, "urgent": 1}

SAMPLE_SOPS = [
    {
        "title": "SharePoint Site Access Grant Procedure",
        "use_case": "sharepoint_access",
        "content": """# SharePoint Site Access Grant SOP\n\n## Purpose\nGrant SharePoint site access to authorized Jade Global employees.\n\n## Prerequisites\n- Requester must be a valid @jadeglobal.com employee\n- Site must exist and be accessible\n- Justification must be provided\n\n## Steps\n1. Verify requester identity in Azure Active Directory\n2. Validate the SharePoint site URL via Microsoft Graph API\n3. Check if user already has access (avoid duplicate grants)\n4. Call Graph API: POST /v1.0/sites/{site-id}/permissions with appropriate role\n5. Send confirmation email to requester\n6. Update Freshservice ticket with resolution note\n7. Log action to STACK audit trail\n\n## Rollback\n- If incorrect access granted: revoke immediately via Graph API\n- Notify IT Manager for audit""",
        "version": "2.1"
    },
    {
        "title": "Microsoft O365 License Assignment",
        "use_case": "license_o365",
        "content": """# O365 License Assignment SOP\n\n## Purpose\nAssign or revoke Microsoft Office 365 licenses for Jade Global employees.\n\n## Steps\n1. Validate requester and target user in Azure AD\n2. Check available license count in Microsoft 365 Admin Center via Graph API\n3. Assign: PATCH /v1.0/users/{userId} with assignedLicenses\n4. Revoke: Remove licenseId from assignedLicenses\n5. Wait 60 seconds for propagation\n6. Verify assignment status\n7. Update Freshservice ticket\n\n## License SKUs\n- Microsoft 365 E3: 6fd2c87f-b296-42f0-b197-1e91e994b900\n- Microsoft 365 Business Premium: cbdc14ab-d96c-4c30-b9f4-6ada7cdc1d46""",
        "version": "1.3"
    },
    {
        "title": "Windows Device Troubleshooting via WinRM",
        "use_case": "windows_troubleshooting",
        "content": """# Windows Troubleshooting SOP\n\n## Purpose\nRemotely diagnose and resolve Windows device issues via WinRM.\n\n## Prerequisites\n- WinRM enabled on target device\n- Device must be on Jade Global corporate network or VPN\n- Device hostname/IP must be provided\n\n## Steps\n1. Resolve device hostname to IP via Active Directory\n2. Test WinRM connectivity: Test-WSMan -ComputerName {hostname}\n3. Create PowerShell session: New-PSSession\n4. Run diagnostic script based on issue type:\n   - Password Reset: Unlock-ADAccount + Set-ADAccountPassword\n   - Disk Cleanup: Invoke disk cleanup + temp file removal\n   - Performance: Get-Process | Sort CPU | Select top 10\n   - Printer: Reset print spooler service\n5. Apply remediation script\n6. Verify resolution\n7. Close PSSession\n8. Update Freshservice ticket""",
        "version": "3.0"
    },
    {
        "title": "Distribution List Member Update",
        "use_case": "dl_update",
        "content": """# Distribution List Update SOP\n\n## Purpose\nAdd or remove members from Exchange Online distribution lists.\n\n## Steps\n1. Validate DL exists in Exchange Online\n2. Validate target user exists in Azure AD\n3. Check if user is already a member\n4. Execute via Exchange Online PowerShell:\n   - Add: Add-DistributionGroupMember -Identity {DL} -Member {user}\n   - Remove: Remove-DistributionGroupMember -Identity {DL} -Member {user}\n5. Verify membership change: Get-DistributionGroupMember\n6. Update Freshservice ticket\n7. Notify user of completion""",
        "version": "1.5"
    }
]


async def seed_initial_data():
    async with AsyncSessionLocal() as db:
        try:
            existing = (await db.execute(select(User).where(User.email == "admin@jadeglobal.com"))).scalar_one_or_none()
            if existing:
                logger.info("Seed data already exists, skipping")
                return

            logger.info("Seeding initial data...")
            user_map = {}

            for u in ADMIN_USERS:
                user = User(email=u["email"], full_name=u["full_name"], role=u["role"],
                            department=u.get("department"), password_hash=get_password_hash(u["password"]))
                db.add(user)
                await db.flush()
                user_map[u["email"]] = user

            for u in AGENT_USERS:
                user = User(email=u["email"], full_name=u["full_name"], role=u["role"],
                            department=u.get("department"), password_hash=get_password_hash("Agent@Stack2025"))
                db.add(user)
                await db.flush()
                user_map[u["email"]] = user

            for u in END_USERS:
                user = User(email=u["email"], full_name=u["full_name"], role=u["role"],
                            department=u.get("department"), password_hash=get_password_hash(u["password"]))
                db.add(user)
                await db.flush()
                user_map[u["email"]] = user

            datta_user_id = None
            datta = (await db.execute(select(User).where(User.email == "datta@jadeglobal.com"))).scalar_one_or_none()
            if datta:
                datta_user_id = datta.user_id

            for g in GROUPS:
                group = AgentGroup(group_name=g["group_name"], use_case=g["use_case"], assignment_mode=g["assignment_mode"])
                db.add(group)
                await db.flush()
                for idx, agent_email in enumerate(g["agents"]):
                    if agent_email in user_map:
                        member = AgentGroupMember(group_id=group.group_id, user_id=user_map[agent_email].user_id, priority_order=idx + 1)
                        db.add(member)
                if datta_user_id:
                    fallback = AgentGroupMember(group_id=group.group_id, user_id=datta_user_id, priority_order=999)
                    db.add(fallback)

            for uc in USE_CASES:
                threshold = ConfidenceThreshold(use_case=uc, auto_resolve_min=85.0, review_after_min=60.0)
                db.add(threshold)
                for priority in PRIORITIES:
                    sla = SLAConfig(use_case=uc, priority=priority, resolution_hours=SLA_HOURS[priority], warning_threshold_percent=75.0)
                    db.add(sla)

            admin_user = user_map.get("admin@jadeglobal.com")
            for sop_data in SAMPLE_SOPS:
                sop = SOP(title=sop_data["title"], use_case=sop_data["use_case"],
                          content=sop_data["content"], version=sop_data["version"],
                          created_by=admin_user.user_id if admin_user else None)
                db.add(sop)

            await db.commit()
            logger.info("Seed data complete: admin, 9 agents, 2 end users, 4 agent groups, SOPs seeded")
        except Exception as e:
            await db.rollback()
            logger.error(f"Seed error: {e}")
            raise
