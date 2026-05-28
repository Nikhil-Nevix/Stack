from datetime import datetime, timezone, date, timedelta
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ....core.database import get_db
from ....core.security import require_admin
from ....models.roi_metric import ROIMetric
from ....models.ticket import Ticket
from ....core.config import settings

router = APIRouter()


async def calculate_roi(db: AsyncSession) -> dict:
    today = date.today()
    period_start = today.replace(day=1)
    auto_count = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.resolution_type == "auto"))).scalar() or 0
    manual_count = (await db.execute(select(func.count()).select_from(Ticket).where(Ticket.resolution_type == "manual"))).scalar() or 0
    total = auto_count + manual_count
    hours_saved = round(auto_count * settings.AVG_MANUAL_RESOLUTION_MINS / 60, 2)
    cost_saved = round(hours_saved * settings.AGENT_HOURLY_COST, 2)
    return {
        "metric_id": str(uuid.uuid4()),
        "period_start": period_start.isoformat(),
        "period_end": today.isoformat(),
        "total_tickets": total,
        "auto_resolved_count": auto_count,
        "manual_resolved_count": manual_count,
        "avg_auto_resolution_mins": 5.0,
        "avg_manual_resolution_mins": settings.AVG_MANUAL_RESOLUTION_MINS,
        "hours_saved": hours_saved,
        "cost_saved": cost_saved,
        "agent_hourly_cost": settings.AGENT_HOURLY_COST,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/current")
async def get_current_roi(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    return await calculate_roi(db)


@router.get("/history")
async def get_roi_history(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(ROIMetric).order_by(ROIMetric.period_start.desc()).limit(12))
    metrics = result.scalars().all()
    if not metrics:
        return [await calculate_roi(db)]
    return [{"metric_id": m.metric_id, "period_start": m.period_start.isoformat(),
             "period_end": m.period_end.isoformat(), "total_tickets": m.total_tickets,
             "auto_resolved_count": m.auto_resolved_count, "manual_resolved_count": m.manual_resolved_count,
             "avg_auto_resolution_mins": m.avg_auto_resolution_mins, "avg_manual_resolution_mins": m.avg_manual_resolution_mins,
             "hours_saved": m.hours_saved, "cost_saved": m.cost_saved, "agent_hourly_cost": m.agent_hourly_cost,
             "calculated_at": m.calculated_at.isoformat()} for m in metrics]


@router.post("/recalculate")
async def recalculate_roi(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    data = await calculate_roi(db)
    metric = ROIMetric(
        metric_id=data["metric_id"],
        period_start=date.fromisoformat(data["period_start"]),
        period_end=date.fromisoformat(data["period_end"]),
        total_tickets=data["total_tickets"],
        auto_resolved_count=data["auto_resolved_count"],
        manual_resolved_count=data["manual_resolved_count"],
        avg_auto_resolution_mins=data["avg_auto_resolution_mins"],
        avg_manual_resolution_mins=data["avg_manual_resolution_mins"],
        hours_saved=data["hours_saved"],
        cost_saved=data["cost_saved"],
        agent_hourly_cost=data["agent_hourly_cost"]
    )
    db.add(metric)
    await db.commit()
    return data


@router.patch("/settings")
async def update_roi_settings(data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    if "agent_hourly_cost" in data:
        settings.AGENT_HOURLY_COST = float(data["agent_hourly_cost"])
    if "avg_manual_resolution_mins" in data:
        settings.AVG_MANUAL_RESOLUTION_MINS = float(data["avg_manual_resolution_mins"])
    return {"message": "ROI settings updated"}
