"""
GridPulse AI — AI Advisory Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AdvisoryRequest(BaseModel):
    asset_id: str
    question: str


class AdvisoryResponse(BaseModel):
    asset_id: str
    question: str
    summary: str
    risk_factors: List[str]
    potential_consequences: List[str]
    recommended_actions: List[str]
    urgency: str
    provider: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    provider: str
    timestamp: datetime
    asset_id: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    recommended_actions: Optional[List[str]] = None
    data_sources: Optional[List[str]] = None


class AdvisoryRecord(BaseModel):
    id: int
    asset_id: str
    question: str
    response: str
    provider: str
    created_at: datetime

    model_config = {"from_attributes": True}
