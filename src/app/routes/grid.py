"""
GridPulse AI — Grid Topology Router
Handles /api/v1/grid endpoints with graceful in-memory fallback.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.app.database.postgres import get_db
from src.app.database.neo4j import get_neo4j_session
from src.app.services.neo4j_service import Neo4jService
from src.app.services.in_memory_grid import InMemoryGridService
from src.app.services.postgres_service import PostgresService
from src.app.schemas.grid import TopologyResponse, CascadeImpactResponse
from src.app.core.graph_scoring import CascadeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grid", tags=["Grid"])


@router.get("/topology", response_model=TopologyResponse)
async def get_grid_topology(db: AsyncSession = Depends(get_db)):
    """Returns full grid graph for visualization with seamless fallback when Neo4j is offline."""
    topology = None
    try:
        async with get_neo4j_session() as session:
            svc = Neo4jService(session)
            topology = await svc.get_topology()
    except Exception as e:
        logger.warning(f"Neo4j topology query unavailable, using in-memory fallback: {e}")

    if not topology or not topology.get("nodes"):
        fallback_svc = InMemoryGridService()
        topology = await fallback_svc.get_topology()

    # Enrich nodes with live risk scores from PostgreSQL if available
    try:
        pg_svc = PostgresService(db)
        assets, _ = await pg_svc.get_all_assets()
        risk_map = {a.asset_id: a for a in assets}
        for node in topology.get("nodes", []):
            nid = node.get("id") or node.get("asset_id")
            if nid in risk_map:
                if risk_map[nid].risk_level:
                    node["risk_level"] = risk_map[nid].risk_level
                if risk_map[nid].final_risk_score is not None:
                    node["final_risk_score"] = risk_map[nid].final_risk_score
    except Exception as e:
        logger.debug(f"Risk score enrichment skipped: {e}")

    return topology


@router.get("/assets/{asset_id}/impact", response_model=CascadeImpactResponse)
async def get_cascade_impact(asset_id: str):
    """Returns full cascade failure analysis for the given asset with seamless fallback."""
    result = None
    try:
        async with get_neo4j_session() as session:
            svc = Neo4jService(session)
            analyzer = CascadeAnalyzer(svc)
            result = await analyzer.analyze_cascade(asset_id)
    except Exception as e:
        logger.warning(f"Neo4j cascade impact failed for {asset_id}, using in-memory fallback: {e}")

    if not result:
        fallback_svc = InMemoryGridService()
        analyzer = CascadeAnalyzer(fallback_svc)
        result = await analyzer.analyze_cascade(asset_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found in grid")
    return result
