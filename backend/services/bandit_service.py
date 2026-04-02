"""
Bandit Service — orchestrates arm selection, state persistence, feedback updates.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Intervention, InterventionLog, BanditState, Policy
from ml.bandit.engine import BanditEngine, ArmState, arm_states_from_db, initialize_fresh_arms
from ml.embeddings.feature_store import get_user_features, features_to_context_vector, invalidate_user_features
from core.constants import (
    InterventionType, BanditStrategy, FeedbackSignal, FEEDBACK_REWARD, INTERVENTION_METADATA
)
from core.config import settings

logger = structlog.get_logger(__name__)


async def _get_or_create_bandit_states(user_id: str, db: AsyncSession) -> Dict[str, ArmState]:
    result = await db.execute(select(BanditState).where(BanditState.user_id == user_id))
    db_states = result.scalars().all()

    if not db_states:
        # First time: create fresh states for all intervention types
        fresh = initialize_fresh_arms()
        for itype, arm in fresh.items():
            db.add(BanditState(
                user_id=user_id,
                intervention_type=itype,
                alpha=arm.alpha,
                beta=arm.beta,
            ))
        await db.flush()
        return fresh

    return arm_states_from_db(db_states)


async def _get_active_policy(db: AsyncSession) -> Optional[Policy]:
    result = await db.execute(select(Policy).where(Policy.status == "active").limit(1))
    return result.scalar_one_or_none()


async def select_intervention(
    user_id: str,
    db: AsyncSession,
    context_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Main entry point: select the best intervention for a user."""

    # Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    opted_out = user.get_opted_out()

    # Get active policy
    policy = await _get_active_policy(db)
    strategy = BanditStrategy(policy.bandit_strategy) if policy else BanditStrategy.THOMPSON_SAMPLING
    policy_config = policy.get_config() if policy else {}
    max_manip = policy_config.get("max_manipulativeness_score", 7)

    # Load bandit states
    arm_states = await _get_or_create_bandit_states(user_id, db)

    # Get context features
    features = await get_user_features(user_id, db)
    context_vec = features_to_context_vector(features)

    # Create engine and select
    engine = BanditEngine(
        user_id=user_id,
        arm_states=arm_states,
        strategy=strategy,
        excluded_types=opted_out,
        max_manipulativeness=max_manip,
    )

    selected_type, selection_reason = engine.select_arm(context=context_vec)

    # Failure detection
    failing = engine.detect_failures()
    if failing:
        logger.warning("failure_modes_detected", user_id=user_id, failing_arms=failing)

    # Fairness check
    violation = engine.check_fairness_violation()
    if violation:
        logger.warning("fairness_violation", user_id=user_id, arm=violation)

    # Get intervention from DB
    intv_result = await db.execute(
        select(Intervention)
        .where(Intervention.intervention_type == selected_type)
        .where(Intervention.is_active == True)
        .limit(1)
    )
    intervention = intv_result.scalar_one_or_none()
    if not intervention:
        raise ValueError(f"No active intervention for type {selected_type}")

    # Render message
    display_name = user.display_name or "there"
    message = intervention.message_template.replace("{name}", display_name)

    # Log delivery
    log = InterventionLog(
        user_id=user_id,
        intervention_id=intervention.id,
        policy_id=policy.id if policy else None,
        bandit_strategy=strategy.value,
        context_features=json.dumps(features),
        message_rendered=message,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    logger.info(
        "intervention_selected",
        user_id=user_id,
        intervention_type=selected_type,
        strategy=strategy.value,
        reason=selection_reason,
        log_id=log.id,
    )

    return {
        "intervention_id": intervention.id,
        "intervention_type": selected_type,
        "message": message,
        "selection_reason": selection_reason,
        "log_id": log.id,
    }


async def record_feedback(
    log_id: str,
    user_id: str,
    feedback_signal: str,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Record user feedback and update bandit arm state."""

    # Load the log
    log_result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.id == log_id)
        .where(InterventionLog.user_id == user_id)
    )
    log = log_result.scalar_one_or_none()
    if not log:
        raise ValueError(f"Log {log_id} not found")

    # Get intervention type
    intv_result = await db.execute(select(Intervention).where(Intervention.id == log.intervention_id))
    intervention = intv_result.scalar_one()
    itype = intervention.intervention_type

    # Compute reward
    signal = FeedbackSignal(feedback_signal)
    reward = FEEDBACK_REWARD[signal]

    # Update log
    log.feedback_signal = feedback_signal
    log.reward = reward
    log.feedback_at = datetime.utcnow()

    # Update bandit state
    state_result = await db.execute(
        select(BanditState)
        .where(BanditState.user_id == user_id)
        .where(BanditState.intervention_type == itype)
    )
    state = state_result.scalar_one_or_none()
    if state:
        arm = ArmState(itype)
        arm.alpha = state.alpha
        arm.beta = state.beta
        arm.n_pulls = state.n_pulls
        arm.total_reward = state.total_reward
        arm.mean_reward = state.mean_reward
        arm.recent_rewards = state.get_recent_rewards()
        arm.is_failing = state.is_failing

        arm.update(reward)

        state.alpha = arm.alpha
        state.beta = arm.beta
        state.n_pulls = arm.n_pulls
        state.total_reward = arm.total_reward
        state.mean_reward = arm.mean_reward
        state.set_recent_rewards(arm.recent_rewards)
        state.is_failing = arm.is_failing
        state.last_updated = datetime.utcnow()

    await db.commit()
    await invalidate_user_features(user_id)

    logger.info("feedback_recorded", log_id=log_id, signal=feedback_signal, reward=reward)
    return {"log_id": log_id, "reward": reward, "feedback_signal": feedback_signal}
