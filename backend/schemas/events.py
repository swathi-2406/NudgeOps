from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class EventCreate(BaseModel):
    user_id: str
    event_type: str
    event_source: str = "app"
    properties: Dict[str, Any] = {}
    session_id: Optional[str] = None

class EventBatch(BaseModel):
    events: list[EventCreate]

class EventResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    event_source: str
    created_at: datetime
    model_config = {"from_attributes": True}
