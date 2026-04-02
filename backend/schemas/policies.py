from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class PolicyCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    bandit_strategy: str = "thompson_sampling"
    config: Dict[str, Any] = {}

class PolicyResponse(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str]
    status: str
    bandit_strategy: str
    created_at: datetime
    model_config = {"from_attributes": True}
