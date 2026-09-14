"""
GridPulse AI — Weather Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WeatherRiskItem(BaseModel):
    asset_id: str
    asset_name: str
    wind_speed: float
    rainfall: float
    lightning_probability: float
    flood_risk: float
    temperature: float
    weather_risk_score: float
    dominant_hazard: str
    timestamp: Optional[datetime] = None


class WeatherListResponse(BaseModel):
    weather_data: List[WeatherRiskItem]
    total: int


class WeatherDetailResponse(BaseModel):
    asset_id: str
    asset_name: str
    current: Optional[dict] = None
    history: List[dict] = []
    risk_analysis: Optional[dict] = None
