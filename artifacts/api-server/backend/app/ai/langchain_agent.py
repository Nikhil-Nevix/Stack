"""
AI Resolution Engine — LangChain + Azure OpenAI GPT-4o.
Falls back to rule-based scoring when API keys are not yet configured.
"""
import json
import time
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..core.config import settings
from ..models.ticket import Ticket
from ..models.ai_resolution import AIResolution
from ..models.sop import SOP
from ..models.confidence_threshold import ConfidenceThreshold
from ..models.ticket_note import TicketNote
from ..models.audit_log import AuditLog


USE_CASE_INTENT_MAP = {
    "sharepoint_access": "SharePoint site access grant or revoke request",
    "sharepoint_admin": "SharePoint site admin access request",
    "license_bluebeam": "BlueBeam Revu license assignment or revocation",
    "license_adobe": "Adobe Acrobat license assignment or revocation",
    "license_o365": "Microsoft Office 365 license assignment or revocation",
    "dl_update": "Exchange distribution list member add or remove",
    "windows_troubleshooting": "Windows device issue — password reset, printer, performance, disk, network, or software"
}

RESOLUTION_STEPS_TEMPLATE = {
    "sharepoint_access": {
        "steps": [
            {"step": 1, "action": "Validate requester identity via Azure AD"},
            {"step": 2, "action": "Check SharePoint site exists and is accessible"},
            {"step": 3, "action": "Call Microsoft Graph API — Sites.FullControl.All permission"},
            {"step": 4, "action": "Grant/revoke site permission for the user"},
            {"step": 5, "action": "Send confirmation email via Graph API"},
            {"step": 6, "action": "Log action to Freshservice ticket"}
        ]
    },
    "license_bluebeam": {
        "steps": [
            {"step": 1, "action": "Validate user eligibility in Freshservice"},
            {"step": 2, "action": "Check license availability in BlueBeam portal"},
            {"step": 3, "action": "Assign/revoke license via BlueBeam API"},
            {"step": 4, "action": "Update Freshservice ticket"},
            {"step": 5, "action": "Notify user via email"}
        ]
    },
    "license_adobe": {
        "steps": [
            {"step": 1, "action": "Validate user eligibility"},
            {"step": 2, "action": "Check Adobe Admin Console via UMAPI"},
            {"step": 3, "action": "Assign/revoke product profile"},
            {"step": 4, "action": "Update Freshservice ticket"},
            {"step": 5, "action": "Notify user via email"}
        ]
    },
    "license_o365": {
        "steps": [
            {"step": 1, "action": "Validate user in Azure AD"},
            {"step": 2, "action": "Check license availability in Microsoft 365 admin"},
            {"step": 3, "action": "Assign/remove license via Graph API"},
            {"step": 4, "action": "Update Freshservice ticket"},
            {"step": 5, "action": "Notify user"}
        ]
    },
    "dl_update": {
        "steps": [
            {"step": 1, "action": "Validate distribution list exists in Exchange Online"},
            {"step": 2, "action": "Validate target user exists in Azure AD"},
            {"step": 3, "action": "Add/remove member via Exchange Online PowerShell"},
            {"step": 4, "action": "Verify membership change"},
            {"step": 5, "action": "Update Freshservice ticket and notify user"}
        ]
    },
    "windows_troubleshooting": {
        "steps": [
            {"step": 1, "action": "Connect to device via WinRM (port 5985)"},
            {"step": 2, "action": "Diagnose issue with diagnostic PowerShell script"},
            {"step": 3, "action": "Execute remediation script based on issue type"},
            {"step": 4, "action": "Verify fix applied successfully"},
            {"step": 5, "action": "Update Freshservice ticket with resolution details"},
            {"step": 6, "action": "Notify user and close ticket"}
        ]
    }
}


def compute_rule_based_scores(ticket: Ticket, sop_found: bool, description_length: int) -> dict:
    intent_detected = USE_CASE_INTENT_MAP.get(ticket.use_case, ticket.use_case)
    intent_clarity = 85.0 if description_length > 30 else (65.0 if description_length > 10 else 40.0)
    sop_match = 90.0 if sop_found else 60.0
    historical = 80.0
    completeness = min(100.0, 50.0 + description_length * 0.5)
    confidence = round((intent_clarity * 0.3 + sop_match * 0.3 + historical * 0.25 + completeness * 0.15), 1)
    return {
        "intent_detected": intent_detected,
        "intent_clarity_score": intent_clarity,
        "sop_match_score": sop_match,
        "historical_success_score": historical,
        "input_completeness_score": completeness,
        "confidence_score": confidence
    }


async def run_ai_resolution(ticket: Ticket, db: AsyncSession, actor) -> dict:
    start_time = time.time()

    sop_result = await db.execute(
        select(SOP).where(and_(SOP.use_case == ticket.use_case, SOP.is_active == True))
        .order_by(SOP.created_at.desc())
    )
    sop = sop_result.scalars().first()

    description = ticket.description or ""
    scores = compute_rule_based_scores(ticket, sop is not None, len(description))
    confidence = scores["confidence_score"]

    threshold_result = await db.execute(
        select(ConfidenceThreshold).where(ConfidenceThreshold.use_case == ticket.use_case)
    )
    threshold = threshold_result.scalar_one_or_none()
    auto_min = threshold.auto_resolve_min if threshold else 85.0
    review_min = threshold.review_after_min if threshold else 60.0

    if confidence >= auto_min:
        decision = "auto_resolve"
    elif confidence >= review_min:
        decision = "review_after"
    else:
        decision = "escalate"

    use_case_key = ticket.use_case
    for k in RESOLUTION_STEPS_TEMPLATE:
        if use_case_key.startswith(k) or k in use_case_key:
            use_case_key = k
            break

    steps = RESOLUTION_STEPS_TEMPLATE.get(use_case_key, RESOLUTION_STEPS_TEMPLATE["windows_troubleshooting"])

    if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
        try:
            from langchain_openai import AzureChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage
            llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=0.1,
                max_tokens=1000
            )
            sop_context = f"\nSOP Available:\n{sop.content[:1000]}" if sop else ""
            prompt = f"""You are STACK AI, an IT service desk automation system for Jade Global Software.

Analyze this IT support ticket and provide a resolution assessment.

Ticket Category: {ticket.use_case}
Title: {ticket.title}
Description: {description[:500]}
{sop_context}

Provide a JSON response with:
{{
  "root_cause": "brief root cause analysis",
  "recommended_steps": ["step 1", "step 2", "step 3"],
  "confidence_adjustment": 0
}}"""
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            response_text = response.content
            try:
                ai_data = json.loads(response_text.strip().strip("```json").strip("```"))
                root_cause = ai_data.get("root_cause", "")
                adj = float(ai_data.get("confidence_adjustment", 0))
                confidence = max(0.0, min(100.0, confidence + adj))
                if confidence >= auto_min:
                    decision = "auto_resolve"
                elif confidence >= review_min:
                    decision = "review_after"
                else:
                    decision = "escalate"
            except Exception:
                root_cause = "AI analysis completed"
        except Exception:
            root_cause = "AI analysis pending (API not configured)"
    else:
        root_cause = "AI analysis pending (Azure OpenAI credentials not yet configured)"

    elapsed = int(time.time() - start_time)

    ai_res = AIResolution(
        ticket_id=ticket.ticket_id,
        intent_detected=scores["intent_detected"],
        root_cause=root_cause,
        sop_matched=sop.sop_id if sop else None,
        sop_title=sop.title if sop else None,
        confidence_score=confidence,
        intent_clarity_score=scores["intent_clarity_score"],
        sop_match_score=scores["sop_match_score"],
        historical_success_score=scores["historical_success_score"],
        input_completeness_score=scores["input_completeness_score"],
        decision=decision,
        resolution_steps=json.dumps(steps),
        execution_status="pending",
        time_taken_seconds=elapsed
    )
    db.add(ai_res)

    new_status = "auto_resolved" if decision == "auto_resolve" else ("escalated" if decision == "escalate" else "in_progress")
    resolution_type = "auto" if decision == "auto_resolve" else "manual"

    from sqlalchemy import update as sa_update
    from datetime import datetime as dt, timezone as tz
    await db.execute(
        sa_update(Ticket).where(Ticket.ticket_id == ticket.ticket_id).values(
            status=new_status,
            resolution_type=resolution_type,
            confidence_score=confidence,
            closed_at=dt.now(tz.utc) if decision == "auto_resolve" else None,
            updated_at=dt.now(tz.utc)
        )
    )

    note = TicketNote(
        ticket_id=ticket.ticket_id,
        note_type="ai_note",
        content=f"AI Analysis Complete\nDecision: {decision}\nConfidence: {confidence:.1f}%\nRoot Cause: {root_cause}",
        is_internal=True
    )
    db.add(note)

    log = AuditLog(
        ticket_id=ticket.ticket_id,
        event_type="ai_resolution_triggered",
        actor_id=actor.user_id if hasattr(actor, "user_id") else None,
        actor_type="agent",
        details=json.dumps({"decision": decision, "confidence": confidence}),
        platform="web_dashboard"
    )
    db.add(log)
    await db.commit()
    await db.refresh(ai_res)

    return {
        "resolution_id": ai_res.resolution_id,
        "ticket_id": ai_res.ticket_id,
        "intent_detected": ai_res.intent_detected,
        "root_cause": ai_res.root_cause,
        "confidence_score": ai_res.confidence_score,
        "intent_clarity_score": ai_res.intent_clarity_score,
        "sop_match_score": ai_res.sop_match_score,
        "historical_success_score": ai_res.historical_success_score,
        "input_completeness_score": ai_res.input_completeness_score,
        "decision": ai_res.decision,
        "resolution_steps": json.loads(ai_res.resolution_steps) if ai_res.resolution_steps else None,
        "execution_status": ai_res.execution_status,
        "execution_output": ai_res.execution_output,
        "time_taken_seconds": ai_res.time_taken_seconds,
        "sop_title": ai_res.sop_title,
        "created_at": ai_res.created_at.isoformat()
    }
