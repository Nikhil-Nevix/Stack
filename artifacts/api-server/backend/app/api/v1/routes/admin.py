from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from ....core.database import get_db
from ....core.security import require_admin, get_current_user, get_password_hash
from ....models.user import User
from ....models.confidence_threshold import ConfidenceThreshold
from ....models.sla_config import SLAConfig
from ....models.agent_group import AgentGroup
from ....models.agent_group_member import AgentGroupMember
from backend.mock.mock_store import mock_store, MockStore

router = APIRouter()


@router.get("/thresholds")
async def list_thresholds(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(ConfidenceThreshold))
    thresholds = result.scalars().all()
    return [{"threshold_id": t.threshold_id, "use_case": t.use_case, "auto_resolve_min": t.auto_resolve_min,
             "review_after_min": t.review_after_min, "updated_at": t.updated_at.isoformat()} for t in thresholds]


@router.patch("/thresholds/{useCase}")
async def update_threshold(useCase: str, data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(ConfidenceThreshold).where(ConfidenceThreshold.use_case == useCase))
    threshold = result.scalar_one_or_none()
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")
    update_vals = {k: v for k, v in data.items() if k in ("auto_resolve_min", "review_after_min")}
    update_vals["updated_at"] = datetime.now(timezone.utc)
    update_vals["updated_by"] = current_user.user_id
    await db.execute(update(ConfidenceThreshold).where(ConfidenceThreshold.use_case == useCase).values(**update_vals))
    await db.commit()
    await db.refresh(threshold)
    return {"threshold_id": threshold.threshold_id, "use_case": threshold.use_case,
            "auto_resolve_min": threshold.auto_resolve_min, "review_after_min": threshold.review_after_min,
            "updated_at": threshold.updated_at.isoformat()}


@router.get("/sla-configs")
async def list_sla_configs(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(SLAConfig))
    configs = result.scalars().all()
    return [{"sla_id": c.sla_id, "use_case": c.use_case, "priority": c.priority,
             "resolution_hours": c.resolution_hours, "warning_threshold_percent": c.warning_threshold_percent} for c in configs]


@router.patch("/sla-configs")
async def update_sla_configs(data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    for item in data.get("configs", []):
        result = await db.execute(
            select(SLAConfig).where(SLAConfig.use_case == item["use_case"], SLAConfig.priority == item["priority"])
        )
        config = result.scalar_one_or_none()
        if config:
            await db.execute(
                update(SLAConfig).where(SLAConfig.sla_id == config.sla_id).values(
                    resolution_hours=item.get("resolution_hours", config.resolution_hours),
                    warning_threshold_percent=item.get("warning_threshold_percent", config.warning_threshold_percent),
                    updated_at=datetime.now(timezone.utc)
                )
            )
    await db.commit()
    return {"message": "SLA configs updated"}


@router.get("/groups")
async def list_agent_groups(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    groups_result = await db.execute(select(AgentGroup))
    groups = groups_result.scalars().all()

    all_group_ids = [g.group_id for g in groups]
    members_result = await db.execute(
        select(AgentGroupMember).where(AgentGroupMember.group_id.in_(all_group_ids))
        .order_by(AgentGroupMember.priority_order)
    )
    members = members_result.scalars().all()

    user_ids = [m.user_id for m in members]
    if user_ids:
        users_result = await db.execute(select(User).where(User.user_id.in_(user_ids)))
        users_map = {u.user_id: u for u in users_result.scalars().all()}
    else:
        users_map = {}

    members_by_group = {}
    for m in members:
        if m.group_id not in members_by_group:
            members_by_group[m.group_id] = []
        u = users_map.get(m.user_id)
        members_by_group[m.group_id].append({
            "user_id": m.user_id,
            "full_name": u.full_name if u else "Unknown",
            "email": u.email if u else "",
            "priority_order": m.priority_order
        })

    return [
        {
            "group_id": g.group_id,
            "group_name": g.group_name,
            "use_case": g.use_case,
            "assignment_mode": g.assignment_mode,
            "members": members_by_group.get(g.group_id, [])
        }
        for g in groups
    ]


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [{"user_id": u.user_id, "email": u.email, "full_name": u.full_name, "role": u.role,
             "department": u.department, "device_name": u.device_name, "is_active": u.is_active,
             "last_login": u.last_login.isoformat() if u.last_login else None,
             "created_at": u.created_at.isoformat()} for u in users]


@router.post("/users", status_code=201)
async def create_user(data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    from ....core.security import validate_jadeglobal_domain
    validate_jadeglobal_domain(data["email"])
    existing = await db.execute(select(User).where(User.email == data["email"].lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data["email"].lower(),
        full_name=data["full_name"],
        role=data.get("role", "user"),
        department=data.get("department"),
        password_hash=get_password_hash(data["password"]),
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"user_id": user.user_id, "email": user.email, "full_name": user.full_name, "role": user.role,
            "department": user.department, "device_name": user.device_name, "is_active": user.is_active,
            "last_login": None, "created_at": user.created_at.isoformat()}


@router.patch("/users/{userId}")
async def update_user(userId: str, data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(User).where(User.user_id == userId))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email == "admin@jadeglobal.com" and data.get("role") and data["role"] != "admin":
        raise HTTPException(status_code=400, detail="Cannot change admin@jadeglobal.com role")

    update_vals = {k: v for k, v in data.items() if k in ("full_name", "role", "department", "is_active")}
    update_vals["updated_at"] = datetime.now(timezone.utc)
    await db.execute(update(User).where(User.user_id == userId).values(**update_vals))
    await db.commit()
    await db.refresh(user)
    return {"user_id": user.user_id, "email": user.email, "full_name": user.full_name, "role": user.role,
            "department": user.department, "device_name": user.device_name, "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat()}


@router.get("/system-health")
async def get_system_health(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "services": {"database": db_status, "redis": "not_configured", "elasticsearch": "not_configured"}
    }


@router.get("/settings/data-source")
async def get_data_source(current_user=Depends(get_current_user)):
    return {"data_source": await MockStore.get_mode()}


@router.patch("/settings/data-source")
async def update_data_source(data: dict, current_user=Depends(require_admin)):
    mode = data.get("mode")
    if mode not in {"mock", "live"}:
        raise HTTPException(status_code=400, detail="mode must be 'mock' or 'live'")
    await MockStore.set_mode(mode)
    return {
        "success": True,
        "data_source": mode,
        "message": f"Switched to {mode} data successfully."
    }
