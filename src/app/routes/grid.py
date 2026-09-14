"""
GridPulse AI — Grid Topology Router
Handles /api/v1/grid endpoints.
"""
from fastapi import APIRouter, HTTPException

from src.app.database.neo4j import get_neo4j_session
from src.app.services.neo4j_service import Neo4jService
from src.app.schemas.grid import TopologyResponse, CascadeImpactResponse
from src.app.core.graph_scoring import CascadeAnalyzer

router = APIRouter(prefix="/grid", tags=["Grid"])


@router.get("/topology", response_model=TopologyResponse)
async def get_grid_topology():
    """Returns full grid graph for visualization."""
    async with get_neo4j_session() as session:
        svc = Neo4jService(session)
        topology = await svc.get_topology()
    return topology


@router.get("/assets/{asset_id}/impact", response_model=CascadeImpactResponse)
async def get_cascade_impact(asset_id: str):
    """Returns full cascade failure analysis for the given asset."""
    async with get_neo4j_session() as session:
        svc = Neo4jService(session)
        analyzer = CascadeAnalyzer(svc)
        result = await analyzer.analyze_cascade(asset_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found in grid")
    return result
