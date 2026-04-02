"""Monitoring service: system health, fairness checks, failure detection."""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import InterventionLog, BanditState, User, MonitoringSnapshot
from core.constants import FeedbackSignal
from core.config import settings

logger = structlog.get_logger(__name__)


async def compute_system_metrics(db: AsyncSession) -> Dict[str, Any]:
    since_24h = datetime.utcnow() - timedelta(hours=24)
    since_7d = datetime.utcnow() - timedelta(days=7)

    # Total interventions delivered
    total_result = await db.execute(select(func.count(InterventionLog.id)))
    total = total_result.scalar() or 0

    # Last 24h
    recent_result = await db.execute(
        select(func.count(InterventionLog.id))
        .where(InterventionLog.delivered_at >= since_24h)
    )
    recent_24h = recent_result.scalar() or 0

    # Feedback breakdown 7d
    fb_result = await db.execute(
        select(InterventionLog.feedback_signal, func.count(InterventionLog.id).label("cnt"))
        .where(InterventionLog.delivered_at >= since_7d)
        .where(InterventionLog.feedback_signal.isnot(None))
        .group_by(InterventionLog.feedback_signal)
    )
    feedback_dist = {row.feedback_signal: row.cnt for row in fb_result}

    total_with_fb = sum(feedback_dist.values())
    completion_rate = feedback_dist.get("completed", 0) / total_with_fb if total_with_fb else 0
    negative_rate = feedback_dist.get("negative", 0) / total_with_fb if total_with_fb else 0

    # Per-intervention type distribution 7d
    type_result = await db.execute(
        select(InterventionLog.intervention_id, func.count(InterventionLog.id).label("cnt"))
        .where(InterventionLog.delivered_at >= since_7d)
        .group_by(InterventionLog.intervention_id)
    )
    type_dist = {row.intervention_id: row.cnt for row in type_result}

    # Active users
    active_result = await db.execute(
        select(func.count(func.distinct(InterventionLog.user_id)))
        .where(InterventionLog.delivered_at >= since_7d)
    )
    active_users_7d = active_result.scalar() or 0

    # Failing arms
    failing_result = await db.execute(
        select(BanditState.user_id, BanditState.intervention_type)
        .where(BanditState.is_failing == True)
    )
    failing_arms = [{"user_id": r.user_id, "intervention_type": r.intervention_type} for r in failing_result]

    alerts = []
    if negative_rate > 0.25:
        alerts.append({"level": "warning", "message": f"High negative feedback rate: {negative_rate:.1%}"})
    if len(failing_arms) > 5:
        alerts.append({"level": "warning", "message": f"{len(failing_arms)} intervention arms currently failing"})

    return {
        "total_interventions_all_time": total,
        "interventions_last_24h": recent_24h,
        "active_users_7d": active_users_7d,
        "feedback_distribution_7d": feedback_dist,
        "completion_rate_7d": round(completion_rate, 4),
        "negative_rate_7d": round(negative_rate, 4),
        "intervention_type_distribution_7d": type_dist,
        "failing_arms_count": len(failing_arms),
        "failing_arms": failing_arms[:10],
        "alerts": alerts,
        "computed_at": datetime.utcnow().isoformat(),
    }


async def fairness_report(db: AsyncSession) -> Dict[str, Any]:
    """Check intervention distribution fairness across all users."""
    since = datetime.utcnow() - timedelta(days=settings.FAIRNESS_CHECK_WINDOW_DAYS)

    result = await db.execute(
        select(InterventionLog.user_id, InterventionLog.intervention_id, func.count(InterventionLog.id).label("cnt"))
        .where(InterventionLog.delivered_at >= since)
        .group_by(InterventionLog.user_id, InterventionLog.intervention_id)
    )
    rows = result.all()

    user_totals: Dict[str, int] = {}
    user_arm_counts: Dict[str, Dict[str, int]] = {}
    for row in rows:
        user_totals[row.user_id] = user_totals.get(row.user_id, 0) + row.cnt
        if row.user_id not in user_arm_counts:
            user_arm_counts[row.user_id] = {}
        user_arm_counts[row.user_id][row.intervention_id] = row.cnt

    violations = []
    for uid, total in user_totals.items():
        for arm, count in user_arm_counts[uid].items():
            share = count / total
            if share > settings.MAX_SINGLE_INTERVENTION_SHARE:
                violations.append({"user_id": uid, "intervention_id": arm, "share": round(share, 3)})

    return {
        "window_days": settings.FAIRNESS_CHECK_WINDOW_DAYS,
        "users_analyzed": len(user_totals),
        "fairness_cap": settings.MAX_SINGLE_INTERVENTION_SHARE,
        "violations": violations,
        "violation_count": len(violations),
        "is_fair": len(violations) == 0,
        "checked_at": datetime.utcnow().isoformat(),
    }
