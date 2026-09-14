"""
GridPulse AI — Risk Score Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RiskScoreBase(BaseModel):
    asset_id: str
    failure_probability: float
    asset_health_risk: float
    weather_risk: float
    grid_impact: float
    cascade_risk: float
    critical_multiplier: float
    final_risk_score: float
    risk_level: str


class RiskScoreCreate(RiskScoreBase):
    timestamp: datetime


class RiskScoreResponse(RiskScoreBase):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class RiskSummaryItem(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    final_risk_score: float
    risk_level: str
    failure_probability: float
    grid_impact: float
    cascade_risk: float
    timestamp: Optional[datetime] = None


class RiskListResponse(BaseModel):
    risk_scores: List[RiskSummaryItem]
    total: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class WorkOrderBase(BaseModel):
    asset_id: str
    priority: str
    description: str
    assigned_crew: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    assigned_crew: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    description: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    id: int
    status: str

    model_config = {"from_attributes": True}
