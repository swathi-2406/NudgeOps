"""Interventions catalog routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import Intervention, InterventionLog
from schemas.interventions import InterventionResponse

router = APIRouter()


@router.get("/", response_model=list[InterventionResponse])
async def list_interventions(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    q = select(Intervention)
    if active_only:
        q = q.where(Intervention.is_active == True)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(intervention_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Intervention).where(Intervention.id == intervention_id))
    intv = result.scalar_one_or_none()
    if not intv:
        raise HTTPException(404, "Intervention not found")
    return intv


@router.get("/{intervention_id}/logs")
async def get_intervention_logs(
    intervention_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.intervention_id == intervention_id)
        .order_by(InterventionLog.delivered_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "feedback_signal": l.feedback_signal,
            "reward": l.reward,
            "delivered_at": l.delivered_at.isoformat(),
        }
        for l in logs
    ]
