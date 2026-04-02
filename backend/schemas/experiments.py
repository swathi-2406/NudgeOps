from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    control_policy_id: str
    treatment_policy_id: str
    traffic_split: float = 0.5
    target_segment: Optional[str] = None
    hypothesis: Optional[str] = None
    primary_metric: str = "completion_rate"
    min_sample_size: int = 30

class ExperimentResponse(BaseModel):
    id: str
    name: str
    status: str
    control_policy_id: str
    treatment_policy_id: str
    traffic_split: float
    winner: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
