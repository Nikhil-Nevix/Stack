from datetime import date, datetime, time, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ....core.database import get_db
from ....core.security import require_agent_or_admin
from ....models.ticket import Ticket
from ....models.user import User

router = APIRouter()


@router.get("/resolution-rate")
async def get_resolution_rate(
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_agent_or_admin)
):
    use_cases = ["sharepoint_access", "sharepoint_admin", "license_bluebeam", "license_adobe",
                 "license_o365", "dl_update", "windows_troubleshooting"]
    items = []
    total_auto = 0
    total_manual = 0
    for uc in use_cases:
        total = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.use_case == uc))).scalar() or 0
        auto = (await db.execute(select(func.count()).select_from(Ticket).where(
            and_(Ticket.use_case == uc, Ticket.resolution_type == "auto")))).scalar() or 0
        manual = (await db.execute(select(func.count()).select_from(Ticket).where(
            and_(Ticket.use_case == uc, Ticket.resolution_type == "manual")))).scalar() or 0
        total_auto += auto
        total_manual += manual
        items.append({"use_case": uc, "total": total, "auto_resolved": auto, "manual_resolved": manual,
                      "auto_pct": round((auto / total * 100) if total else 0, 1)})
    grand_total = total_auto + total_manual
    return {
        "by_use_case": items,
        "overall_auto_pct": round((total_auto / grand_total * 100) if grand_total else 0, 1),
        "overall_manual_pct": round((total_manual / grand_total * 100) if grand_total else 0, 1)
    }


@router.get("/sla-compliance")
async def get_sla_compliance(
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_agent_or_admin)
):
    met = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.sla_status == "safe"))).scalar() or 0
    breached = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.sla_status == "breached"))).scalar() or 0
    at_risk = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.sla_status == "at_risk"))).scalar() or 0
    total = met + breached + at_risk
    trend = [{"date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"),
               "met_pct": round(met / total * 100 if total else 100, 1)} for i in range(6, -1, -1)]
    return {"met": met, "breached": breached, "at_risk": at_risk,
            "met_pct": round(met / total * 100 if total else 100, 1), "trend": trend}


@router.get("/agent-performance")
async def get_agent_performance(db: AsyncSession = Depends(get_db), current_user=Depends(require_agent_or_admin)):
    agents = (await db.execute(select(User).where(User.role.in_(["agent", "admin"])))).scalars().all()
    result = []
    for a in agents:
        count = (await db.execute(select(func.count()).select_from(Ticket).where(
            and_(Ticket.assigned_agent_id == a.user_id, Ticket.status.in_(["auto_resolved", "closed"]))
        ))).scalar() or 0
        result.append({"agent_id": a.user_id, "agent_name": a.full_name, "tickets_resolved": count,
                       "avg_resolution_mins": 30.0, "sla_met_pct": 85.0})
    return result


@router.get("/ticket-trends")
async def get_ticket_trends(
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_agent_or_admin)
):
    def parse_iso_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        return date.fromisoformat(value)

    end_day = parse_iso_date(end_date) or datetime.now(timezone.utc).date()
    start_day = parse_iso_date(start_date) or (end_day - timedelta(days=29))

    trend = []
    current_day = start_day
    while current_day <= end_day:
        day_start = datetime.combine(current_day, time.min, tzinfo=timezone.utc)
        next_day = day_start + timedelta(days=1)
        total = (await db.execute(select(func.count()).select_from(Ticket).where(
            Ticket.created_at >= day_start,
            Ticket.created_at < next_day,
        ))).scalar() or 0
        trend.append({"date": current_day.strftime("%Y-%m-%d"), "total": total, "by_use_case": {}})
        current_day += timedelta(days=1)
    return {"trend": trend}


@router.get("/ai-accuracy")
async def get_ai_accuracy(db: AsyncSession = Depends(get_db), current_user=Depends(require_agent_or_admin)):
    from ....models.ai_resolution import AIResolution
    avg_result = (await db.execute(select(func.avg(AIResolution.confidence_score)))).scalar()
    auto_count = (await db.execute(select(func.count()).select_from(AIResolution).where(AIResolution.decision == "auto_resolve"))).scalar() or 0
    total = (await db.execute(select(func.count()).select_from(AIResolution))).scalar() or 0
    distribution = [
        {"range": "90-100", "count": 0}, {"range": "80-89", "count": 0},
        {"range": "70-79", "count": 0}, {"range": "60-69", "count": 0}, {"range": "<60", "count": 0}
    ]
    return {"avg_confidence": round(avg_result or 0, 1), "distribution": distribution,
            "auto_resolve_accuracy": round(auto_count / total * 100 if total else 0, 1)}
