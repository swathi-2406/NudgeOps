"""Offline Policy Evaluation + A/B test analysis."""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import InterventionLog, Policy
from core.constants import FeedbackSignal, FEEDBACK_REWARD
from core.config import settings

logger = structlog.get_logger(__name__)


async def evaluate_policy(policy_id: str, db: AsyncSession, window_days: int = None) -> Dict[str, Any]:
    window_days = window_days or settings.POLICY_EVALUATION_WINDOW_DAYS
    since = datetime.utcnow() - timedelta(days=window_days)
    result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.policy_id == policy_id)
        .where(InterventionLog.delivered_at >= since)
    )
    logs = result.scalars().all()
    if not logs:
        return {"error": "no_data", "policy_id": policy_id}

    total = len(logs)
    with_feedback = [l for l in logs if l.feedback_signal is not None]
    n_feedback = len(with_feedback)
    response_rate = n_feedback / total if total else 0.0
    feedback_dist: Dict[str, int] = {}
    rewards: List[float] = []
    for log in with_feedback:
        feedback_dist[log.feedback_signal] = feedback_dist.get(log.feedback_signal, 0) + 1
        if log.reward is not None:
            rewards.append(log.reward)

    mean_reward = float(np.mean(rewards)) if rewards else 0.0
    reward_std = float(np.std(rewards)) if len(rewards) > 1 else 0.0
    completion_rate = feedback_dist.get("completed", 0) / total if total else 0.0
    engagement_rate = (feedback_dist.get("completed", 0) + feedback_dist.get("engaged", 0)) / total if total else 0.0
    dismiss_rate = feedback_dist.get("dismissed", 0) / total if total else 0.0
    negative_rate = feedback_dist.get("negative", 0) / total if total else 0.0

    ci_lower, ci_upper = 0.0, 0.0
    if len(rewards) >= 2:
        ci = stats.t.interval(0.95, len(rewards) - 1, loc=mean_reward, scale=stats.sem(rewards))
        ci_lower, ci_upper = float(ci[0]), float(ci[1])

    health_score = min(100.0, (engagement_rate * 30 + completion_rate * 40 + (1 - dismiss_rate) * 15 + (1 - negative_rate) * 15) * 100)
    return {
        "policy_id": policy_id,
        "evaluated_at": datetime.utcnow().isoformat(),
        "window_days": window_days,
        "total_deliveries": total,
        "total_with_feedback": n_feedback,
        "response_rate": round(response_rate, 4),
        "completion_rate": round(completion_rate, 4),
        "engagement_rate": round(engagement_rate, 4),
        "dismiss_rate": round(dismiss_rate, 4),
        "negative_rate": round(negative_rate, 4),
        "mean_reward": round(mean_reward, 4),
        "reward_std": round(reward_std, 4),
        "reward_ci_lower": round(ci_lower, 4),
        "reward_ci_upper": round(ci_upper, 4),
        "feedback_distribution": feedback_dist,
        "health_score": round(health_score, 2),
    }


async def run_ab_test_analysis(control_id: str, treatment_id: str, db: AsyncSession, window_days: int = 14) -> Dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=window_days)

    async def get_rewards(policy_id):
        r = await db.execute(
            select(InterventionLog.reward)
            .where(InterventionLog.policy_id == policy_id)
            .where(InterventionLog.delivered_at >= since)
            .where(InterventionLog.reward.isnot(None))
        )
        return [row[0] for row in r.all()]

    control_rewards = await get_rewards(control_id)
    treatment_rewards = await get_rewards(treatment_id)
    n_c, n_t = len(control_rewards), len(treatment_rewards)
    min_n = settings.AB_TEST_MIN_SAMPLE_SIZE
    if n_c < min_n or n_t < min_n:
        return {"status": "insufficient_data", "n_control": n_c, "n_treatment": n_t, "min_required": min_n, "winner": "inconclusive"}

    c_arr, t_arr = np.array(control_rewards), np.array(treatment_rewards)
    t_stat, p_value = stats.ttest_ind(c_arr, t_arr)
    significant = p_value < settings.AB_TEST_SIGNIFICANCE_LEVEL
    c_mean, t_mean = float(np.mean(c_arr)), float(np.mean(t_arr))
    relative_lift = (t_mean - c_mean) / abs(c_mean) if c_mean != 0 else 0.0
    pooled_std = np.sqrt((np.var(c_arr) + np.var(t_arr)) / 2)
    cohens_d = (t_mean - c_mean) / pooled_std if pooled_std > 0 else 0.0
    winner = ("treatment" if t_mean > c_mean else "control") if significant else "inconclusive"

    return {
        "status": "complete",
        "n_control": n_c, "n_treatment": n_t,
        "control_mean_reward": round(c_mean, 4),
        "treatment_mean_reward": round(t_mean, 4),
        "relative_lift_pct": round(relative_lift * 100, 2),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 6),
        "significant": significant,
        "cohens_d": round(float(cohens_d), 4),
        "winner": winner,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


async def check_for_retraining_needed(db: AsyncSession) -> Tuple[bool, str]:
    since = datetime.utcnow() - timedelta(days=1)
    result = await db.execute(
        select(func.count(InterventionLog.id))
        .where(InterventionLog.delivered_at >= since)
        .where(InterventionLog.feedback_signal.isnot(None))
    )
    recent_feedback = result.scalar() or 0
    if recent_feedback >= settings.POLICY_MIN_FEEDBACK_FOR_RETRAIN:
        return True, f"Sufficient feedback: {recent_feedback} events"
    neg_result = await db.execute(
        select(func.count(InterventionLog.id))
        .where(InterventionLog.delivered_at >= since)
        .where(InterventionLog.feedback_signal == "negative")
    )
    neg_count = neg_result.scalar() or 0
    if recent_feedback > 0 and neg_count / recent_feedback > 0.3:
        return True, f"High negative rate: {neg_count}/{recent_feedback}"
    return False, "Retraining not needed"
