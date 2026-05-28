from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....models.ticket import Ticket

router = APIRouter()

WELCOME_FLOWS = {"hi", "hello", "help", "start", "hey"}
SHAREPOINT_KEYWORDS = {"sharepoint", "share point", "sp", "site"}
LICENSE_KEYWORDS = {"license", "bluebeam", "adobe", "o365", "microsoft", "software"}
DL_KEYWORDS = {"distribution", "dl", "mailing list", "group", "email list"}
WINDOWS_KEYWORDS = {"password", "printer", "software", "slow", "disk", "network", "wifi", "install", "laptop", "computer", "reset"}
STATUS_KEYWORDS = {"status", "ticket", "check", "update"}


def detect_intent(message: str) -> str:
    msg_lower = message.lower()
    words = set(msg_lower.split())
    if words & SHAREPOINT_KEYWORDS or any(kw in msg_lower for kw in SHAREPOINT_KEYWORDS):
        return "sharepoint_flow"
    if words & LICENSE_KEYWORDS or any(kw in msg_lower for kw in LICENSE_KEYWORDS):
        return "license_flow"
    if words & DL_KEYWORDS or any(kw in msg_lower for kw in DL_KEYWORDS):
        return "dl_flow"
    if words & WINDOWS_KEYWORDS or any(kw in msg_lower for kw in WINDOWS_KEYWORDS):
        return "windows_flow"
    if words & STATUS_KEYWORDS:
        return "status_check"
    return "welcome"


USE_CASE_MAP = {
    "sharepoint_flow": "sharepoint_access",
    "license_flow": "license_o365",
    "dl_flow": "dl_update",
    "windows_flow": "windows_troubleshooting"
}

FLOW_PROMPTS = {
    "sharepoint_flow": {
        0: ("What type of SharePoint access do you need?", ["Grant Access", "Revoke Access", "Site Admin"], "options"),
        1: ("Please provide the SharePoint site URL:", [], "text"),
        2: ("Please provide a brief justification:", [], "text"),
        3: None
    },
    "license_flow": {
        0: ("Which license do you need?", ["BlueBeam", "Adobe Acrobat", "Microsoft O365"], "options"),
        1: ("Do you want to assign or revoke this license?", ["Assign", "Revoke"], "options"),
        2: ("Please provide a brief justification:", [], "text"),
        3: None
    },
    "dl_flow": {
        0: ("What would you like to do?", ["Add Member to DL", "Remove Member from DL", "Create New DL"], "options"),
        1: ("Please provide the distribution list email address:", [], "text"),
        2: ("Please provide the user email(s) to add/remove:", [], "text"),
        3: None
    },
    "windows_flow": {
        0: ("What is the issue you're experiencing?", ["Password Reset", "Printer Issue", "Slow Performance", "Disk Space", "Network/WiFi", "Software Install"], "options"),
        1: ("Please provide your device name or hostname:", [], "text"),
        2: ("Please describe the issue in more detail:", [], "text"),
        3: None
    }
}


@router.post("/message")
async def send_chat_message(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = data.get("message", "")
    platform = data.get("platform", "web_dashboard")
    context = data.get("context", {})
    session_id = data.get("session_id", "")

    current_flow = context.get("flow")
    current_step = context.get("step", 0)
    collected_data = context.get("collected_data", {})

    if not current_flow:
        intent = detect_intent(message)
        if intent == "welcome" or message.lower().strip() in WELCOME_FLOWS:
            return {
                "reply": f"Hi {current_user.full_name}! I'm STACK AI — your IT service desk assistant by Jade Global Software.\n\nI can help you with:\n1. SharePoint access or admin requests\n2. Software license requests (BlueBeam / Adobe / O365)\n3. Distribution list updates\n4. Windows troubleshooting\n\nWhat do you need help with today?",
                "reply_type": "options",
                "options": ["SharePoint Request", "License Request", "Distribution List Update", "Windows Issue", "Check Ticket Status"],
                "ticket_id": None,
                "action_taken": "welcome_shown",
                "requires_input": True,
                "input_prompt": "Select an option or type your issue",
                "session_id": session_id
            }
        elif intent == "status_check":
            result = await db.execute(
                select(Ticket).where(Ticket.user_id == current_user.user_id).order_by(Ticket.created_at.desc()).limit(3)
            )
            tickets = result.scalars().all()
            if tickets:
                ticket_list = "\n".join([f"• {t.ticket_id[:8]}... — {t.title} ({t.status})" for t in tickets])
                return {
                    "reply": f"Here are your recent tickets:\n\n{ticket_list}",
                    "reply_type": "text",
                    "options": [],
                    "ticket_id": None,
                    "action_taken": "status_shown",
                    "requires_input": False,
                    "input_prompt": None,
                    "session_id": session_id
                }
            return {
                "reply": "You don't have any tickets yet. Would you like to raise one?",
                "reply_type": "options",
                "options": ["Yes, raise a ticket", "No thanks"],
                "ticket_id": None,
                "action_taken": "status_checked",
                "requires_input": True,
                "input_prompt": None,
                "session_id": session_id
            }
        else:
            current_flow = intent
            current_step = 0
            collected_data = {}

    if current_flow in FLOW_PROMPTS:
        if current_step > 0 and message:
            step_keys = ["selection", "detail_1", "detail_2"]
            if current_step - 1 < len(step_keys):
                collected_data[step_keys[current_step - 1]] = message

        next_step_data = FLOW_PROMPTS[current_flow].get(current_step)

        if next_step_data is None:
            use_case = USE_CASE_MAP.get(current_flow, "windows_troubleshooting")
            title_map = {
                "sharepoint_flow": f"SharePoint {collected_data.get('selection', 'Request')} - {collected_data.get('detail_1', 'N/A')}",
                "license_flow": f"License Request - {collected_data.get('selection', 'Software')}",
                "dl_flow": f"DL Update - {collected_data.get('selection', 'Distribution List Change')}",
                "windows_flow": f"Windows Issue - {collected_data.get('selection', 'General Issue')}"
            }
            title = title_map.get(current_flow, "IT Support Request")
            description = f"Submitted via {platform}. Details: {collected_data}"

            ticket = Ticket(
                title=title,
                description=description,
                use_case=use_case,
                source=platform,
                user_id=current_user.user_id,
                metadata_json=str(collected_data)
            )
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)

            return {
                "reply": f"Your ticket has been created!\n\nTicket ID: {ticket.ticket_id[:8]}...\nCategory: {use_case.replace('_', ' ').title()}\nExpected resolution: 4 hours\n\nSTACK AI is analyzing your request now...",
                "reply_type": "text",
                "options": [],
                "ticket_id": ticket.ticket_id,
                "action_taken": "ticket_created",
                "requires_input": False,
                "input_prompt": None,
                "session_id": session_id
            }

        prompt, options, reply_type = next_step_data
        return {
            "reply": prompt,
            "reply_type": reply_type,
            "options": options,
            "ticket_id": None,
            "action_taken": "awaiting_input",
            "requires_input": True,
            "input_prompt": prompt,
            "session_id": session_id,
        }

    return {
        "reply": "I didn't understand that. Type 'help' to see what I can assist with.",
        "reply_type": "text",
        "options": [],
        "ticket_id": None,
        "action_taken": "fallback",
        "requires_input": True,
        "input_prompt": "Type your issue or select an option",
        "session_id": session_id
    }
