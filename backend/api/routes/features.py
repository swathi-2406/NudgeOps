"""Feature store routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import User
from sqlalchemy import select
from ml.embeddings.feature_store import get_user_features, invalidate_user_features
from ml.embeddings.user_embeddings import compute_and_store_embedding, find_similar_users

router = APIRouter()

@router.get("/user/{user_id}")
async def get_features(user_id: str, db: AsyncSession = Depends(get_db)):
    u = await db.execute(select(User).where(User.id == user_id))
    if not u.scalar_one_or_none():
        raise HTTPException(404, "User not found")
    return await get_user_features(user_id, db)

@router.post("/user/{user_id}/invalidate")
async def invalidate(user_id: str):
    await invalidate_user_features(user_id)
    return {"message": "Feature cache invalidated"}

@router.post("/user/{user_id}/embedding")
async def compute_embedding(user_id: str, db: AsyncSession = Depends(get_db)):
    embedding = await compute_and_store_embedding(user_id, db)
    return {"user_id": user_id, "embedding_dim": len(embedding), "embedding": embedding[:8]}

@router.get("/user/{user_id}/similar")
async def similar_users(user_id: str, top_k: int = 5, db: AsyncSession = Depends(get_db)):
    return await find_similar_users(user_id, db, top_k=top_k)
