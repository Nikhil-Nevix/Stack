from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import json
from ....core.database import get_db
from ....core.security import get_current_user, require_agent_or_admin
from ....models.user import User
from ....models.ticket import Ticket
from ....models.audit_log import AuditLog
from backend.mock.mock_store import MockStore, mock_store

router = APIRouter()

TODAY_START = lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    if await MockStore.is_mock():
        return mock_store.get_dashboard_summary()

    today = TODAY_START()
    total_open = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.status == "open"))).scalar() or 0
    escalated = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.status == "escalated"))).scalar() or 0
    resolved_today = (await db.execute(
        select(func.count()).select_from(Ticket).where(
            and_(Ticket.status.in_(["auto_resolved", "closed"]), Ticket.updated_at >= today)
        )
    )).scalar() or 0

    total_closed = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.status.in_(["auto_resolved", "closed"])))).scalar() or 0
    sla_met = (await db.execute(select(func.count()).select_from(Ticket).where(
        and_(Ticket.status.in_(["auto_resolved", "closed"]), Ticket.sla_status == "safe")
    ))).scalar() or 0
    sla_met_pct = round((sla_met / total_closed * 100) if total_closed else 100.0, 1)

    auto_res = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.resolution_type == "auto"))).scalar() or 0
    auto_pct = round((auto_res / total_closed * 100) if total_closed else 0.0, 1)

    use_case_result = await db.execute(
        select(Ticket.use_case, func.count(Ticket.ticket_id)).group_by(Ticket.use_case)
    )
    by_use_case = [{"use_case": r[0], "count": r[1]} for r in use_case_result.all()]

    status_result = await db.execute(
        select(Ticket.status, func.count(Ticket.ticket_id)).group_by(Ticket.status)
    )
    by_status = [{"status": r[0], "count": r[1]} for r in status_result.all()]

    return {
        "open_tickets": total_open,
        "resolved_today": resolved_today,
        "sla_met_pct": sla_met_pct,
        "auto_resolution_pct": auto_pct,
        "by_use_case": by_use_case,
        "by_status": by_status,
        "escalated_tickets": escalated,
        "avg_resolution_mins": None
    }


@router.get("/my-summary")
async def get_my_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if await MockStore.is_mock():
        user_summary = mock_store.get_dashboard_summary()
        uid = current_user.user_id
        tickets = mock_store.get_tickets_for_user(uid)
        return {
            "my_open": sum(1 for ticket in tickets if ticket.get("status") in {"open", "in_progress", "escalated"}),
            "my_resolved": sum(1 for ticket in tickets if ticket.get("status") in {"auto_resolved", "closed"}),
            "my_sla_breached": sum(1 for ticket in tickets if ticket.get("sla_status") == "breached"),
            "my_avg_resolution_mins": None,
        }

    uid = current_user.user_id
    my_open = (await db.execute(select(func.count()).select_from(Ticket).where(
        and_(Ticket.user_id == uid, Ticket.status.in_(["open", "in_progress", "escalated"]))
    ))).scalar() or 0
    my_resolved = (await db.execute(select(func.count()).select_from(Ticket).where(
        and_(Ticket.user_id == uid, Ticket.status.in_(["auto_resolved", "closed"]))
    ))).scalar() or 0
    my_breached = (await db.execute(select(func.count()).select_from(Ticket).where(
        and_(Ticket.user_id == uid, Ticket.sla_status == "breached")
    ))).scalar() or 0
    return {"my_open": my_open, "my_resolved": my_resolved, "my_sla_breached": my_breached, "my_avg_resolution_mins": None}


@router.get("/live-queue")
async def get_live_queue(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_agent_or_admin)):
    if await MockStore.is_mock():
        return [
            ticket
            for ticket in mock_store.get_all_tickets()
            if ticket.get("status") in {"open", "in_progress"}
        ][:50]

    result = await db.execute(
        select(Ticket).where(Ticket.status.in_(["open", "in_progress"])).order_by(Ticket.created_at.desc()).limit(50)
    )
    tickets = result.scalars().all()
    return [{"ticket_id": t.ticket_id, "title": t.title, "use_case": t.use_case, "status": t.status,
             "priority": t.priority, "sla_status": t.sla_status, "sla_breach_predicted": t.sla_breach_predicted,
             "source": t.source, "user_id": t.user_id, "assigned_agent_id": t.assigned_agent_id,
             "resolution_type": t.resolution_type, "created_at": t.created_at.isoformat(),
             "updated_at": None, "closed_at": None, "confidence_score": t.confidence_score,
             "freshservice_ticket_id": t.freshservice_ticket_id, "description": t.description,
             "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
             "user_name": None, "agent_name": None} for t in tickets]


@router.get("/sla-at-risk")
async def get_sla_at_risk(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_agent_or_admin)):
    if await MockStore.is_mock():
        return mock_store.get_at_risk_tickets()[:20]

    result = await db.execute(
        select(Ticket).where(Ticket.sla_status.in_(["at_risk", "breached"])).order_by(Ticket.sla_deadline.asc()).limit(20)
    )
    tickets = result.scalars().all()
    return [{"ticket_id": t.ticket_id, "title": t.title, "use_case": t.use_case, "status": t.status,
             "priority": t.priority, "sla_status": t.sla_status, "sla_breach_predicted": t.sla_breach_predicted,
             "source": t.source, "user_id": t.user_id, "assigned_agent_id": t.assigned_agent_id,
             "resolution_type": t.resolution_type, "created_at": t.created_at.isoformat(),
             "updated_at": None, "closed_at": None, "confidence_score": t.confidence_score,
             "freshservice_ticket_id": t.freshservice_ticket_id, "description": t.description,
             "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
             "user_name": None, "agent_name": None} for t in tickets]


@router.get("/recent-activity")
async def get_recent_activity(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_agent_or_admin)):
    if await MockStore.is_mock():
        return mock_store.get_recent_activity(limit=20)

    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)
    )
    logs = result.scalars().all()
    actor_ids = [l.actor_id for l in logs if l.actor_id]
    actors_map = {}
    if actor_ids:
        actors_result = await db.execute(select(User).where(User.user_id.in_(actor_ids)))
        actors_map = {u.user_id: u.full_name for u in actors_result.scalars().all()}
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
