from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class InterventionResponse(BaseModel):
    id: str
    intervention_type: str
    name: str
    description: Optional[str]
    message_template: str
    channel: str
    is_active: bool
    manipulativeness_score: int
    risk_level: str
    model_config = {"from_attributes": True}

class NudgeRequest(BaseModel):
    user_id: str
    context: Optional[Dict[str, Any]] = {}

class NudgeResponse(BaseModel):
    intervention_id: str
    intervention_type: str
    message: str
    selection_reason: str
    log_id: str

class FeedbackRequest(BaseModel):
    log_id: str
    feedback_signal: str
    user_id: str
