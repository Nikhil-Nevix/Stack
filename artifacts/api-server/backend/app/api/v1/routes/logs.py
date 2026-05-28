from typing import Optional
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ....core.database import get_db
from ....core.security import require_admin
from ....models.audit_log import AuditLog
from ....models.api_call_log import APICallLog
from ....models.powershell_execution import PowershellExecution
from ....models.user import User

router = APIRouter()


@router.get("/audit")
async def get_audit_logs(
    ticket_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1, limit: int = 50,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)
):
    query = select(AuditLog)
    if ticket_id:
        query = query.where(AuditLog.ticket_id == ticket_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    actor_ids = [l.actor_id for l in logs if l.actor_id]
    actors_map = {}
    if actor_ids:
        actors_result = await db.execute(select(User).where(User.user_id.in_(actor_ids)))
        actors_map = {u.user_id: u.full_name for u in actors_result.scalars().all()}

    return {
        "logs": [
            {"log_id": l.log_id, "ticket_id": l.ticket_id, "event_type": l.event_type,
             "actor_id": l.actor_id, "actor_type": l.actor_type,
             "actor_name": actors_map.get(l.actor_id) if l.actor_id else "System",
             "details": json.loads(l.details) if l.details else None,
             "ip_address": l.ip_address, "platform": l.platform, "created_at": l.created_at.isoformat()}
            for l in logs
        ],
        "total": total
    }


@router.get("/api-calls")
async def get_api_call_logs(
    api_name: Optional[str] = None, page: int = 1,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)
):
    query = select(APICallLog)
    if api_name:
        query = query.where(APICallLog.api_name == api_name)
    query = query.order_by(APICallLog.called_at.desc()).limit(100)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [{"api_log_id": l.api_log_id, "ticket_id": l.ticket_id, "api_name": l.api_name,
             "endpoint": l.endpoint, "method": l.method, "response_status": l.response_status,
             "duration_ms": l.duration_ms, "called_at": l.called_at.isoformat()} for l in logs]


@router.get("/powershell")
async def get_powershell_logs(
    page: int = 1,
    db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)
):
    result = await db.execute(select(PowershellExecution).order_by(PowershellExecution.executed_at.desc()).limit(100))
    logs = result.scalars().all()
    return [{"execution_id": l.execution_id, "ticket_id": l.ticket_id, "device_name": l.device_name,
             "device_ip": l.device_ip, "script_name": l.script_name, "execution_status": l.execution_status,
             "output_log": l.output_log, "executed_at": l.executed_at.isoformat(),
             "duration_seconds": l.duration_seconds} for l in logs]
