"""Bandit engine routes — nudge selection and feedback."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from schemas.interventions import NudgeRequest, NudgeResponse, FeedbackRequest
from services.bandit_service import select_intervention, record_feedback

router = APIRouter()


@router.post("/nudge", response_model=NudgeResponse)
async def get_nudge(payload: NudgeRequest, db: AsyncSession = Depends(get_db)):
    """Select and deliver the most effective intervention for a user."""
    try:
        result = await select_intervention(payload.user_id, db, payload.context)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Bandit error: {str(e)}")


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    """Record user feedback on a delivered intervention."""
    valid_signals = ["engaged", "completed", "ignored", "dismissed", "negative"]
    if payload.feedback_signal not in valid_signals:
        raise HTTPException(400, f"Invalid signal. Must be one of: {valid_signals}")
    try:
        result = await record_feedback(payload.log_id, payload.user_id, payload.feedback_signal, db)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/state/{user_id}")
async def get_bandit_state(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get current bandit arm states for a user."""
    from sqlalchemy import select
    from db.models import BanditState
    result = await db.execute(select(BanditState).where(BanditState.user_id == user_id))
    states = result.scalars().all()
    return [
        {
            "intervention_type": s.intervention_type,
            "alpha": s.alpha,
            "beta": s.beta,
            "n_pulls": s.n_pulls,
            "mean_reward": s.mean_reward,
            "is_failing": s.is_failing,
            "estimated_success_prob": s.alpha / (s.alpha + s.beta),
        }
        for s in states
    ]
