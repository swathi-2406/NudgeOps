"""Feature Store — computes and caches behavioral features per user."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import numpy as np
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json

from core.config import settings
from db.models import UserEvent, InterventionLog, FeatureStore, BanditState
from db.redis_client import cache_get, cache_set, cache_delete

logger = structlog.get_logger(__name__)
FEATURE_CACHE_PREFIX = "features:user:"


def _cache_key(user_id: str) -> str:
    return f"{FEATURE_CACHE_PREFIX}{user_id}"


async def compute_user_features(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    now = datetime.utcnow()
    window_start = now - timedelta(days=settings.BEHAVIOR_WINDOW_DAYS)

    events_result = await db.execute(
        select(UserEvent.event_type, func.count(UserEvent.id).label("cnt"))
        .where(UserEvent.user_id == user_id)
        .where(UserEvent.created_at >= window_start)
        .group_by(UserEvent.event_type)
    )
    event_counts = {row.event_type: row.cnt for row in events_result}
    total_events = sum(event_counts.values())
    session_starts = event_counts.get("session_start", 0)
    task_completions = event_counts.get("task_complete", 0)

    last_event_result = await db.execute(
        select(UserEvent.created_at)
        .where(UserEvent.user_id == user_id)
        .order_by(UserEvent.created_at.desc())
        .limit(1)
    )
    last_event = last_event_result.scalar_one_or_none()
    days_since_last_event = (now - last_event).days if last_event else settings.BEHAVIOR_WINDOW_DAYS

    feedback_result = await db.execute(
        select(InterventionLog.feedback_signal, func.count(InterventionLog.id).label("cnt"))
        .where(InterventionLog.user_id == user_id)
        .where(InterventionLog.delivered_at >= window_start)
        .group_by(InterventionLog.feedback_signal)
    )
    feedback_counts = {row.feedback_signal: row.cnt for row in feedback_result if row.feedback_signal}
    total_delivered = sum(feedback_counts.values())

    engagement_rate = (feedback_counts.get("engaged", 0) + feedback_counts.get("completed", 0)) / total_delivered if total_delivered else 0.0
    completion_rate = feedback_counts.get("completed", 0) / total_delivered if total_delivered else 0.0
    dismiss_rate = feedback_counts.get("dismissed", 0) / total_delivered if total_delivered else 0.0
    negative_rate = feedback_counts.get("negative", 0) / total_delivered if total_delivered else 0.0

    bandit_result = await db.execute(
        select(BanditState).where(BanditState.user_id == user_id).order_by(BanditState.mean_reward.desc())
    )
    bandit_states = bandit_result.scalars().all()
    best_arm = bandit_states[0].intervention_type if bandit_states else "unknown"
    best_arm_reward = bandit_states[0].mean_reward if bandit_states else 0.0
    total_arm_pulls = sum(s.n_pulls for s in bandit_states)

    activity_score = min(1.0, total_events / 100.0)
    recency_score = max(0.0, 1.0 - (days_since_last_event / settings.BEHAVIOR_WINDOW_DAYS))
    consistency_score = min(1.0, session_starts / settings.BEHAVIOR_WINDOW_DAYS)

    return {
        "total_events_30d": total_events,
        "session_starts_30d": session_starts,
        "task_completions_30d": task_completions,
        "days_since_last_event": days_since_last_event,
        "activity_score": round(activity_score, 4),
        "recency_score": round(recency_score, 4),
        "consistency_score": round(consistency_score, 4),
        "total_interventions_delivered": total_delivered,
        "engagement_rate": round(engagement_rate, 4),
        "completion_rate": round(completion_rate, 4),
        "dismiss_rate": round(dismiss_rate, 4),
        "negative_rate": round(negative_rate, 4),
        "best_arm": best_arm,
        "best_arm_reward": round(best_arm_reward, 4),
        "total_arm_pulls": total_arm_pulls,
        "computed_at": now.isoformat(),
    }


async def get_user_features(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    cached = await cache_get(_cache_key(user_id))
    if cached is not None:
        return cached
    features = await compute_user_features(user_id, db)
    existing = await db.execute(select(FeatureStore).where(FeatureStore.user_id == user_id))
    fs = existing.scalar_one_or_none()
    if fs:
        fs.features = json.dumps(features)
        fs.computed_at = datetime.utcnow()
    else:
        fs = FeatureStore(user_id=user_id, features=json.dumps(features),
                          expires_at=datetime.utcnow() + timedelta(seconds=settings.FEATURE_CACHE_TTL_SECONDS))
        db.add(fs)
    await db.commit()
    await cache_set(_cache_key(user_id), features, ttl=settings.FEATURE_CACHE_TTL_SECONDS)
    return features


async def invalidate_user_features(user_id: str):
    await cache_delete(_cache_key(user_id))


def features_to_context_vector(features: Dict[str, Any]) -> np.ndarray:
    return np.array([
        features.get("activity_score", 0.0),
        features.get("recency_score", 0.0),
        features.get("consistency_score", 0.0),
        features.get("engagement_rate", 0.0),
        features.get("completion_rate", 0.0),
        features.get("dismiss_rate", 0.0),
        features.get("negative_rate", 0.0),
        min(1.0, features.get("total_interventions_delivered", 0) / 100.0),
        features.get("best_arm_reward", 0.0),
        min(1.0, features.get("total_arm_pulls", 0) / 200.0),
    ], dtype=np.float32)
