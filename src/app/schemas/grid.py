"""
GridPulse AI — Grid Topology Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List


class GridNode(BaseModel):
    id: str
    type: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_level: Optional[str] = None
    final_risk_score: Optional[float] = None
    status: str = "active"
    capacity: Optional[float] = None
    critical_facility: bool = False
    facility_type: Optional[str] = None


class GridEdge(BaseModel):
    source: str
    target: str
    type: str


class TopologyResponse(BaseModel):
    nodes: List[GridNode]
    edges: List[GridEdge]
    total_nodes: int
    total_edges: int


class AffectedAsset(BaseModel):
    asset_id: str
    name: str
    type: str
    depth: int


class AffectedFacility(BaseModel):
    asset_id: str
    name: str
    facility_type: Optional[str] = None
    depth: int


class CascadeImpactResponse(BaseModel):
    failed_asset: dict
    affected_assets: List[AffectedAsset]
    affected_facilities: List[AffectedFacility]
    cascade_risk: float
    grid_impact: float
    cascade_path: List[str]
    dependency_depth: int
    affected_asset_count: int
    critical_facility_count: int
    explanation: str
