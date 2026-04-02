from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    external_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    timezone: str = "UTC"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    external_id: str
    email: Optional[str]
    display_name: Optional[str]
    segment: str
    timezone: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
