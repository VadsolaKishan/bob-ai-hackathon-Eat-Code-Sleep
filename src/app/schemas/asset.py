"""
GridPulse AI — Asset Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class AssetType(str, Enum):
    transformer = "transformer"
    substation = "substation"
    feeder = "feeder"
    critical_facility = "critical_facility"


class AssetStatus(str, Enum):
    active = "active"
    maintenance = "maintenance"
    offline = "offline"


class AssetBase(BaseModel):
    asset_id: str
    name: str
    asset_type: AssetType
    latitude: float
    longitude: float
    capacity: Optional[float] = None
    critical_facility: bool = False
    facility_type: Optional[str] = None
    status: AssetStatus = AssetStatus.active
    installation_date: Optional[date] = None


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: int
    risk_level: Optional[str] = None
    final_risk_score: Optional[float] = None

    model_config = {"from_attributes": True}


class SensorReadingBase(BaseModel):
    asset_id: str
    timestamp: datetime
    temperature: float
    vibration: float
    partial_discharge: float


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingResponse(SensorReadingBase):
    id: int

    model_config = {"from_attributes": True}


class DGAReadingBase(BaseModel):
    asset_id: str
    timestamp: datetime
    h2: float = 0.0
    ch4: float = 0.0
    c2h2: float = 0.0
    c2h4: float = 0.0
    c2h6: float = 0.0
    co: float = 0.0
    co2: float = 0.0


class DGAReadingCreate(DGAReadingBase):
    pass


class DGAReadingResponse(DGAReadingBase):
    id: int

    model_config = {"from_attributes": True}


class WeatherReadingBase(BaseModel):
    asset_id: str
    timestamp: datetime
    wind_speed: float = 0.0
    rainfall: float = 0.0
    lightning_probability: float = 0.0
    flood_risk: float = 0.0
    temperature: float = 25.0


class WeatherReadingCreate(WeatherReadingBase):
    pass


class WeatherReadingResponse(WeatherReadingBase):
    id: int

    model_config = {"from_attributes": True}


class IncidentBase(BaseModel):
    asset_id: str
    timestamp: datetime
    failure_type: str
    severity: str
    description: str


class IncidentCreate(IncidentBase):
    pass


class IncidentResponse(IncidentBase):
    id: int

    model_config = {"from_attributes": True}


class AssetDetailResponse(BaseModel):
    asset: AssetResponse
    latest_sensor: Optional[SensorReadingResponse] = None
    latest_dga: Optional[DGAReadingResponse] = None
    latest_weather: Optional[WeatherReadingResponse] = None
    latest_risk: Optional[dict] = None
    incidents: List[IncidentResponse] = []


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int
