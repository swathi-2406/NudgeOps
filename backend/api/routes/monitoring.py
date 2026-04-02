"""Monitoring and system health routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from services.monitoring_service import compute_system_metrics, fairness_report

router = APIRouter()

@router.get("/metrics")
async def system_metrics(db: AsyncSession = Depends(get_db)):
    return await compute_system_metrics(db)

@router.get("/fairness")
async def fairness_check(db: AsyncSession = Depends(get_db)):
    return await fairness_report(db)

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    metrics = await compute_system_metrics(db)
    return {
        "status": "healthy" if not metrics["alerts"] else "degraded",
        "alerts": metrics["alerts"],
        "interventions_last_24h": metrics["interventions_last_24h"],
        "active_users_7d": metrics["active_users_7d"],
    }
