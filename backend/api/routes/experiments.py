"""A/B Testing experiment routes."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import Experiment, Policy
from schemas.experiments import ExperimentCreate, ExperimentResponse
from ml.evaluation.policy_evaluator import run_ab_test_analysis
from services.audit_service import log_action

router = APIRouter()


@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment).order_by(Experiment.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create_experiment(payload: ExperimentCreate, db: AsyncSession = Depends(get_db)):
    exp = Experiment(**payload.model_dump(), results=json.dumps({}))
    db.add(exp)
    await db.flush()
    await log_action(db, "api", "experiment_created", "experiment", exp.id, {"name": payload.name})
    await db.commit()
    await db.refresh(exp)
    return exp


@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    if exp.status != "created":
        raise HTTPException(400, f"Cannot start experiment in status: {exp.status}")
    exp.status = "running"
    exp.started_at = datetime.utcnow()
    await log_action(db, "api", "experiment_started", "experiment", experiment_id)
    await db.commit()
    return {"message": "Experiment started", "started_at": exp.started_at.isoformat()}


@router.post("/{experiment_id}/conclude")
async def conclude_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")

    analysis = await run_ab_test_analysis(exp.control_policy_id, exp.treatment_policy_id, db)
    exp.results = json.dumps(analysis)
    exp.winner = analysis.get("winner", "inconclusive")
    exp.status = "concluded"
    exp.concluded_at = datetime.utcnow()
    await log_action(db, "api", "experiment_concluded", "experiment", experiment_id, {"winner": exp.winner})
    await db.commit()
    return {"message": "Experiment concluded", "winner": exp.winner, "analysis": analysis}


@router.get("/{experiment_id}/results")
async def get_results(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    return {
        "experiment_id": experiment_id,
        "name": exp.name,
        "status": exp.status,
        "winner": exp.winner,
        "results": json.loads(exp.results or "{}"),
    }
