"""Policy registry routes."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import Policy
from schemas.policies import PolicyCreate, PolicyResponse
from services.audit_service import log_action
from ml.evaluation.policy_evaluator import evaluate_policy

router = APIRouter()


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).order_by(Policy.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=PolicyResponse, status_code=201)
async def create_policy(payload: PolicyCreate, db: AsyncSession = Depends(get_db)):
    policy = Policy(
        name=payload.name,
        version=payload.version,
        description=payload.description,
        bandit_strategy=payload.bandit_strategy,
        config=json.dumps(payload.config),
        performance_metrics=json.dumps({}),
    )
    db.add(policy)
    await db.flush()
    await log_action(db, "api", "policy_created", "policy", policy.id, {"name": payload.name})
    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Policy not found")
    return p


@router.post("/{policy_id}/promote")
async def promote_policy(policy_id: str, db: AsyncSession = Depends(get_db)):
    """Promote a policy to active status (retiring the current active one)."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(404, "Policy not found")

    # Retire current active
    active_result = await db.execute(select(Policy).where(Policy.status == "active"))
    for p in active_result.scalars().all():
        p.status = "retired"
        p.retired_at = datetime.utcnow()

    policy.status = "active"
    policy.promoted_at = datetime.utcnow()
    await log_action(db, "api", "policy_promoted", "policy", policy_id)
    await db.commit()
    return {"message": f"Policy {policy_id} promoted to active"}


@router.post("/{policy_id}/rollback")
async def rollback_policy(policy_id: str, db: AsyncSession = Depends(get_db)):
    """Roll back a policy."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(404, "Policy not found")
    policy.status = "rolled_back"
    policy.retired_at = datetime.utcnow()
    await log_action(db, "api", "policy_rolled_back", "policy", policy_id)
    await db.commit()
    return {"message": f"Policy {policy_id} rolled back"}


@router.get("/{policy_id}/evaluate")
async def evaluate(policy_id: str, window_days: int = 7, db: AsyncSession = Depends(get_db)):
    """Run offline policy evaluation."""
    return await evaluate_policy(policy_id, db, window_days=window_days)
