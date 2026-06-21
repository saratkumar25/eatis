"""
app/schemas/resource.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ResourceResponse(BaseModel):
    id: int
    event_id: int
    officers_required: int
    barricades_required: int
    patrol_vehicles: int
    emergency_units: int
    tow_vehicles: int
    deployment_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
