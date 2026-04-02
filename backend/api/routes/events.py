"""Event ingestion pipeline routes."""
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import UserEvent, User
from schemas.events import EventCreate, EventBatch, EventResponse
from ml.embeddings.feature_store import invalidate_user_features

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=201)
async def ingest_event(
    payload: EventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user_check = await db.execute(select(User).where(User.id == payload.user_id))
    if not user_check.scalar_one_or_none():
        raise HTTPException(404, "User not found")

    event = UserEvent(
        user_id=payload.user_id,
        event_type=payload.event_type,
        event_source=payload.event_source,
        properties=json.dumps(payload.properties),
        session_id=payload.session_id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Invalidate feature cache for this user
    background_tasks.add_task(invalidate_user_features, payload.user_id)
    return event


@router.post("/batch", status_code=201)
async def ingest_batch(
    payload: EventBatch,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user_ids = set()
    events = []
    for e in payload.events:
        events.append(UserEvent(
            user_id=e.user_id,
            event_type=e.event_type,
            event_source=e.event_source,
            properties=json.dumps(e.properties),
            session_id=e.session_id,
        ))
        user_ids.add(e.user_id)

    db.add_all(events)
    await db.commit()

    for uid in user_ids:
        background_tasks.add_task(invalidate_user_features, uid)

    return {"ingested": len(events)}


@router.get("/user/{user_id}", response_model=list[EventResponse])
async def get_user_events(
    user_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserEvent)
        .where(UserEvent.user_id == user_id)
        .order_by(UserEvent.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
