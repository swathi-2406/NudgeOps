"""User behavioral embeddings."""
import json
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from db.models import UserEmbedding
from ml.embeddings.feature_store import get_user_features

logger = structlog.get_logger(__name__)


def compute_embedding(features: Dict[str, Any], dim: int = 32) -> np.ndarray:
    base = np.array([
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
    np.random.seed(int(sum(base * 1000)) % (2**31))
    projection = np.random.randn(len(base), dim).astype(np.float32) * 0.1
    embedding = np.tanh(base @ projection)
    embedding[0] = base[0]
    embedding[1] = base[1]
    embedding[2] = base[3]
    embedding[3] = base[4]
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding.astype(float)


async def compute_and_store_embedding(user_id: str, db: AsyncSession, version: str = "v1") -> List[float]:
    features = await get_user_features(user_id, db)
    embedding_list = compute_embedding(features, dim=settings.EMBEDDING_DIM).tolist()
    result = await db.execute(
        select(UserEmbedding)
        .where(UserEmbedding.user_id == user_id)
        .where(UserEmbedding.embedding_version == version)
        .order_by(UserEmbedding.computed_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.embedding = json.dumps(embedding_list)
        existing.feature_snapshot = json.dumps(features)
        existing.computed_at = datetime.utcnow()
    else:
        db.add(UserEmbedding(
            user_id=user_id,
            embedding=json.dumps(embedding_list),
            embedding_version=version,
            feature_snapshot=json.dumps(features),
        ))
    await db.commit()
    return embedding_list


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


async def find_similar_users(user_id: str, db: AsyncSession, top_k: int = 5, version: str = "v1") -> List[Dict]:
    result = await db.execute(
        select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        .where(UserEmbedding.embedding_version == version)
        .order_by(UserEmbedding.computed_at.desc()).limit(1)
    )
    target = result.scalar_one_or_none()
    if not target:
        return []
    target_vec = np.array(json.loads(target.embedding), dtype=np.float32)
    all_result = await db.execute(
        select(UserEmbedding).where(UserEmbedding.user_id != user_id).where(UserEmbedding.embedding_version == version)
    )
    sims = []
    for emb in all_result.scalars().all():
        vec = np.array(json.loads(emb.embedding), dtype=np.float32)
        sims.append({"user_id": emb.user_id, "similarity": cosine_similarity(target_vec, vec)})
    sims.sort(key=lambda x: x["similarity"], reverse=True)
    return sims[:top_k]
