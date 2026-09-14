"""
GridPulse AI — Risk Router
Handles /api/v1/risk endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.postgres import get_db
from src.app.schemas.risk import RiskListResponse
from src.app.services.postgres_service import PostgresService

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("", response_model=RiskListResponse)
async def get_all_risk_scores(db: AsyncSession = Depends(get_db)):
    """Returns risk scores for all assets sorted by final_risk_score descending."""
    from src.app.core.risk_engine import RiskEngine
    from src.app.services.neo4j_service import Neo4jService
    from src.app.database.neo4j import get_neo4j_session

    svc = PostgresService(db)
    assets, _ = await svc.get_all_assets()

    scores = []
    async with get_neo4j_session() as neo4j_session:
        neo4j_svc = Neo4jService(neo4j_session)
        risk_engine = RiskEngine(db, neo4j_svc)
        for asset in assets:
            try:
                score = await risk_engine.compute_risk(asset.asset_id)
                scores.append(score)
            except Exception:
                pass

    scores.sort(key=lambda x: x.get("final_risk_score", 0), reverse=True)

    critical = sum(1 for s in scores if s.get("risk_level") == "CRITICAL")
    high = sum(1 for s in scores if s.get("risk_level") == "HIGH")
    medium = sum(1 for s in scores if s.get("risk_level") == "MEDIUM")
    low = sum(1 for s in scores if s.get("risk_level") == "LOW")

    return RiskListResponse(
        risk_scores=scores,
        total=len(scores),
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low
    )
