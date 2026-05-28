from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from ....core.database import get_db
from ....core.security import require_admin
from ....models.sop import SOP

router = APIRouter()


@router.get("")
async def list_sops(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(SOP).order_by(SOP.created_at.desc()))
    sops = result.scalars().all()
    return [{"sop_id": s.sop_id, "title": s.title, "use_case": s.use_case,
             "content": s.content, "version": s.version, "is_active": s.is_active,
             "created_at": s.created_at.isoformat(),
             "updated_at": s.updated_at.isoformat() if s.updated_at else None} for s in sops]


@router.post("", status_code=201)
async def create_sop(data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    sop = SOP(
        title=data["title"],
        use_case=data["use_case"],
        content=data["content"],
        version=data.get("version", "1.0"),
        created_by=current_user.user_id
    )
    db.add(sop)
    await db.commit()
    await db.refresh(sop)
    return {"sop_id": sop.sop_id, "title": sop.title, "use_case": sop.use_case,
            "content": sop.content, "version": sop.version, "is_active": sop.is_active,
            "created_at": sop.created_at.isoformat(), "updated_at": None}


@router.get("/{sopId}")
async def get_sop(sopId: str, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(SOP).where(SOP.sop_id == sopId))
    sop = result.scalar_one_or_none()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    return {"sop_id": sop.sop_id, "title": sop.title, "use_case": sop.use_case,
            "content": sop.content, "version": sop.version, "is_active": sop.is_active,
            "created_at": sop.created_at.isoformat(),
            "updated_at": sop.updated_at.isoformat() if sop.updated_at else None}


@router.patch("/{sopId}")
async def update_sop(sopId: str, data: dict, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    result = await db.execute(select(SOP).where(SOP.sop_id == sopId))
    sop = result.scalar_one_or_none()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    update_vals = {k: v for k, v in data.items() if k in ("title", "content", "version", "is_active")}
    update_vals["updated_at"] = datetime.now(timezone.utc)
    await db.execute(update(SOP).where(SOP.sop_id == sopId).values(**update_vals))
    await db.commit()
    await db.refresh(sop)
    return {"sop_id": sop.sop_id, "title": sop.title, "use_case": sop.use_case,
            "content": sop.content, "version": sop.version, "is_active": sop.is_active,
            "created_at": sop.created_at.isoformat(),
            "updated_at": sop.updated_at.isoformat() if sop.updated_at else None}


@router.delete("/{sopId}")
async def delete_sop(sopId: str, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    await db.execute(delete(SOP).where(SOP.sop_id == sopId))
    await db.commit()
    return {"message": "SOP deleted"}
