from datetime import datetime, timezone, timedelta
from typing import Optional
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from pydantic import BaseModel
from ....core.database import get_db
from ....core.security import get_current_user, require_agent_or_admin, require_admin
from ....models.user import User
from ....models.ticket import Ticket
from ....models.ticket_note import TicketNote
from ....models.audit_log import AuditLog
from ....models.ai_resolution import AIResolution
from ....models.sla_config import SLAConfig

router = APIRouter()


def ticket_to_dict(t: Ticket, user_name: str = None, agent_name: str = None, confidence_score: float = None):
    return {
        "ticket_id": t.ticket_id,
        "freshservice_ticket_id": t.freshservice_ticket_id,
        "title": t.title,
        "description": t.description,
        "use_case": t.use_case,
        "status": t.status,
        "priority": t.priority,
        "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
        "sla_status": t.sla_status,
        "sla_breach_predicted": t.sla_breach_predicted,
        "source": t.source,
        "user_id": t.user_id,
        "assigned_agent_id": t.assigned_agent_id,
        "resolution_type": t.resolution_type,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        "confidence_score": confidence_score or t.confidence_score,
        "user_name": user_name,
        "agent_name": agent_name,
    }


async def compute_sla_deadline(db: AsyncSession, use_case: str, priority: str) -> Optional[datetime]:
    result = await db.execute(
        select(SLAConfig).where(and_(SLAConfig.use_case == use_case, SLAConfig.priority == priority))
    )
    sla = result.scalar_one_or_none()
    if sla:
        return datetime.now(timezone.utc) + timedelta(hours=sla.resolution_hours)
    hours_map = {"low": 8, "medium": 4, "high": 2, "urgent": 1}
    return datetime.now(timezone.utc) + timedelta(hours=hours_map.get(priority, 4))


async def log_audit(db: AsyncSession, event_type: str, ticket_id: str = None, actor_id: str = None, actor_type: str = "user", details: dict = None):
    log = AuditLog(
        ticket_id=ticket_id,
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        details=json.dumps(details) if details else None,
        platform="web_dashboard"
    )
    db.add(log)


@router.get("")
async def list_tickets(
    status: Optional[str] = None,
    use_case: Optional[str] = None,
    priority: Optional[str] = None,
    sla_status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Ticket)

    if current_user.role == "user":
        query = query.where(Ticket.user_id == current_user.user_id)

    if status:
        query = query.where(Ticket.status == status)
    if use_case:
        query = query.where(Ticket.use_case == use_case)
    if priority:
        query = query.where(Ticket.priority == priority)
    if sla_status:
        query = query.where(Ticket.sla_status == sla_status)
    if search:
        query = query.where(Ticket.title.ilike(f"%{search}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.order_by(Ticket.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    tickets = result.scalars().all()

    user_ids = list({t.user_id for t in tickets} | {t.assigned_agent_id for t in tickets if t.assigned_agent_id})
    users_result = await db.execute(select(User).where(User.user_id.in_(user_ids)))
    users_map = {u.user_id: u.full_name for u in users_result.scalars().all()}

    ticket_ids = [t.ticket_id for t in tickets]
    ai_result = await db.execute(
        select(AIResolution).where(AIResolution.ticket_id.in_(ticket_ids))
        .order_by(AIResolution.created_at.desc())
    )
    ai_map = {}
    for ai in ai_result.scalars().all():
        if ai.ticket_id not in ai_map:
            ai_map[ai.ticket_id] = ai.confidence_score

    return {
        "tickets": [
            ticket_to_dict(
                t,
                user_name=users_map.get(t.user_id),
                agent_name=users_map.get(t.assigned_agent_id) if t.assigned_agent_id else None,
                confidence_score=ai_map.get(t.ticket_id)
            )
            for t in tickets
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("", status_code=201)
async def create_ticket(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    use_case = data.get("use_case", "windows_troubleshooting")
    priority = data.get("priority", "medium")
    sla_deadline = await compute_sla_deadline(db, use_case, priority)

    ticket = Ticket(
        title=data.get("title", ""),
        description=data.get("description"),
        use_case=use_case,
        priority=priority,
        source=data.get("source", "web_dashboard"),
        user_id=current_user.user_id,
        sla_deadline=sla_deadline,
        metadata_json=json.dumps(data.get("metadata", {})) if data.get("metadata") else None
    )
    db.add(ticket)
    await db.flush()
    await log_audit(db, "ticket_created", ticket.ticket_id, current_user.user_id, details={"title": ticket.title})
    await db.commit()
    await db.refresh(ticket)
    return ticket_to_dict(ticket, user_name=current_user.full_name)


@router.get("/{ticketId}")
async def get_ticket(ticketId: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role == "user" and ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user_result = await db.execute(select(User).where(User.user_id == ticket.user_id))
    ticket_user = user_result.scalar_one_or_none()

    agent = None
    if ticket.assigned_agent_id:
        agent_result = await db.execute(select(User).where(User.user_id == ticket.assigned_agent_id))
        agent = agent_result.scalar_one_or_none()

    ai_result = await db.execute(
        select(AIResolution).where(AIResolution.ticket_id == ticketId).order_by(AIResolution.created_at.desc())
    )
    ai_res = ai_result.scalars().first()

    td = ticket_to_dict(
        ticket,
        user_name=ticket_user.full_name if ticket_user else None,
        agent_name=agent.full_name if agent else None
    )
    if ai_res and current_user.role in ("admin", "agent"):
        td["ai_resolution"] = {
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
    else:
        td["ai_resolution"] = None
    return td


@router.patch("/{ticketId}")
async def update_ticket(
    ticketId: str, data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = {k: v for k, v in data.items() if k in ("title", "description", "status", "priority", "assigned_agent_id")}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.execute(update(Ticket).where(Ticket.ticket_id == ticketId).values(**update_data))
    await log_audit(db, "ticket_updated", ticketId, current_user.user_id, details=update_data)
    await db.commit()
    await db.refresh(ticket)
    return ticket_to_dict(ticket)


@router.delete("/{ticketId}")
async def delete_ticket(
    ticketId: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    await db.execute(delete(Ticket).where(Ticket.ticket_id == ticketId))
    await db.commit()
    return {"message": "Ticket deleted"}


@router.post("/{ticketId}/resolve")
async def resolve_ticket(
    ticketId: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    from ....ai.langchain_agent import run_ai_resolution
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    resolution = await run_ai_resolution(ticket, db, current_user)
    return resolution


@router.post("/{ticketId}/escalate")
async def escalate_ticket(
    ticketId: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    from ....models.agent_group import AgentGroup
    from ....models.agent_group_member import AgentGroupMember
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    group_result = await db.execute(select(AgentGroup).where(AgentGroup.use_case == ticket.use_case))
    group = group_result.scalars().first()

    assigned_agent_id = None
    if group:
        members_result = await db.execute(
            select(AgentGroupMember).where(AgentGroupMember.group_id == group.group_id)
            .order_by(AgentGroupMember.priority_order)
        )
        members = members_result.scalars().all()
        for m in members:
            if m.priority_order < 999:
                assigned_agent_id = m.user_id
                break
        if not assigned_agent_id and members:
            assigned_agent_id = members[0].user_id

    await db.execute(
        update(Ticket).where(Ticket.ticket_id == ticketId).values(
            status="escalated", assigned_agent_id=assigned_agent_id,
            updated_at=datetime.now(timezone.utc)
        )
    )
    await log_audit(db, "ticket_escalated", ticketId, current_user.user_id, details={"assigned_to": assigned_agent_id})
    await db.commit()
    await db.refresh(ticket)
    return ticket_to_dict(ticket)


@router.get("/{ticketId}/notes")
async def list_ticket_notes(
    ticketId: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role == "user" and ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(TicketNote).where(TicketNote.ticket_id == ticketId)
    if current_user.role == "user":
        query = query.where(TicketNote.is_internal == False)
    query = query.order_by(TicketNote.created_at.asc())
    notes_result = await db.execute(query)
    notes = notes_result.scalars().all()

    author_ids = [n.created_by for n in notes if n.created_by]
    authors_result = await db.execute(select(User).where(User.user_id.in_(author_ids)))
    authors_map = {u.user_id: u.full_name for u in authors_result.scalars().all()}

    return [
        {
            "note_id": n.note_id,
            "ticket_id": n.ticket_id,
            "note_type": n.note_type,
            "content": n.content,
            "created_by": n.created_by,
            "is_internal": n.is_internal,
            "created_at": n.created_at.isoformat(),
            "author_name": authors_map.get(n.created_by) if n.created_by else "System"
        }
        for n in notes
    ]


@router.post("/{ticketId}/notes", status_code=201)
async def add_ticket_note(
    ticketId: str, data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticketId))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role == "user" and ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    is_internal = data.get("is_internal", False)
    if current_user.role == "user":
        is_internal = False

    note = TicketNote(
        ticket_id=ticketId,
        note_type=data.get("note_type", "human_note"),
        content=data.get("content", ""),
        created_by=current_user.user_id,
        is_internal=is_internal
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return {
        "note_id": note.note_id,
        "ticket_id": note.ticket_id,
        "note_type": note.note_type,
        "content": note.content,
        "created_by": note.created_by,
        "is_internal": note.is_internal,
        "created_at": note.created_at.isoformat(),
        "author_name": current_user.full_name
    }


@router.get("/{ticketId}/timeline")
async def get_ticket_timeline(
    ticketId: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    result = await db.execute(
        select(AuditLog).where(AuditLog.ticket_id == ticketId).order_by(AuditLog.created_at.asc())
    )
    logs = result.scalars().all()

    actor_ids = [l.actor_id for l in logs if l.actor_id]
    if actor_ids:
        actors_result = await db.execute(select(User).where(User.user_id.in_(actor_ids)))
        actors_map = {u.user_id: u.full_name for u in actors_result.scalars().all()}
    else:
        actors_map = {}

    return [
        {
            "log_id": l.log_id,
            "ticket_id": l.ticket_id,
            "event_type": l.event_type,
            "actor_id": l.actor_id,
            "actor_type": l.actor_type,
            "actor_name": actors_map.get(l.actor_id) if l.actor_id else "System",
            "details": json.loads(l.details) if l.details else None,
            "ip_address": l.ip_address,
            "platform": l.platform,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
