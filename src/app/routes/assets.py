"""
GridPulse AI — Assets Router
Handles all /api/v1/assets endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.app.database.postgres import get_db
from src.app.schemas.asset import (
    AssetListResponse, AssetDetailResponse, AssetResponse, SensorReadingResponse,
    DGAReadingResponse, WeatherReadingResponse, IncidentResponse
)
from src.app.schemas.risk import RiskScoreResponse
from src.app.services.postgres_service import PostgresService

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=AssetListResponse)
async def get_all_assets(
    risk_level: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Returns all assets with their latest risk scores."""
    svc = PostgresService(db)
    assets, total = await svc.get_all_assets(
        risk_level=risk_level,
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )
    return AssetListResponse(assets=assets, total=total)


@router.get("/{asset_id}", response_model=AssetDetailResponse)
async def get_asset_detail(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns full asset detail with sensor, DGA, weather and risk data."""
    svc = PostgresService(db)
    detail = await svc.get_asset_detail(asset_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return detail


@router.get("/{asset_id}/risk")
async def get_asset_risk(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns the latest risk score for a specific asset."""
    from src.app.core.risk_engine import RiskEngine
    from src.app.services.neo4j_service import Neo4jService
    from src.app.database.neo4j import get_neo4j_session

    svc = PostgresService(db)
    asset = await svc.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    async with get_neo4j_session() as neo4j_session:
        neo4j_svc = Neo4jService(neo4j_session)
        risk_engine = RiskEngine(db, neo4j_svc)
        score = await risk_engine.compute_risk(asset_id)

    return score
