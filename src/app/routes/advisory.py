"""
GridPulse AI — Advisory Router
Handles /api/v1/advisory endpoints for both asset-specific and free-form chatbot interactions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import logging

from src.app.database.postgres import get_db
from src.app.schemas.advisory import (
    AdvisoryRequest, AdvisoryResponse, ChatRequest, ChatResponse
)
from src.app.services.postgres_service import PostgresService
from src.app.core.advisory import AdvisoryEngine
from src.app.core.chat_intent import detect_chat_intent, resolve_asset_ids
from src.app.core.chat_context import ChatContextBuilder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advisory", tags=["Advisory"])


@router.post("/chat", response_model=ChatResponse)
async def advisory_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Free-form chat with the AI grid advisor.
    Dynamically resolves assets, detects intent, builds grounded context,
    and returns authoritative structured operational advice.
    """
    from src.app.database.neo4j import get_neo4j_session
    from src.app.services.neo4j_service import Neo4jService

    # 1. Deterministic asset resolution & intent detection
    asset_ids = resolve_asset_ids(request.message)
    intent = detect_chat_intent(request.message, asset_ids)

    # 2. Build rich operational context across PostgreSQL, Neo4j, Risk, DGA, Weather, and Crew
    context_data = None
    try:
        async with get_neo4j_session() as neo4j_session:
            neo4j_svc = Neo4jService(neo4j_session)
            builder = ChatContextBuilder(db, neo4j_svc)
            context_data = await builder.build_context(intent, asset_ids, request.message)
    except Exception as e:
        logger.warning(f"Neo4j unavailable for chat context, building degraded: {e}")
        builder = ChatContextBuilder(db, None)
        context_data = await builder.build_context(intent, asset_ids, request.message)

    if request.context:
        context_data["user_context"] = request.context

    # 3. Generate advisory via Granite (or deterministic local fallback)
    engine = AdvisoryEngine()
    result_dict, provider = await engine.chat(request.message, context_data)

    response_str = result_dict.get("response", "") if isinstance(result_dict, dict) else str(result_dict)

    return ChatResponse(
        response=response_str,
        provider=provider,
        timestamp=datetime.now(timezone.utc),
        asset_id=result_dict.get("asset_id") if isinstance(result_dict, dict) else None,
        risk_level=result_dict.get("risk_level") if isinstance(result_dict, dict) else None,
        risk_score=result_dict.get("risk_score") if isinstance(result_dict, dict) else None,
        recommended_actions=result_dict.get("recommended_actions") if isinstance(result_dict, dict) else None,
        data_sources=result_dict.get("data_sources") if isinstance(result_dict, dict) else None,
    )


@router.post("", response_model=AdvisoryResponse)
async def get_asset_advisory(
    request: AdvisoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ask the AI advisor about a specific asset."""
    svc = PostgresService(db)

    asset = await svc.get_asset(request.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {request.asset_id} not found")

    sensor = await svc.get_latest_sensor(request.asset_id)
    dga = await svc.get_latest_dga(request.asset_id)
    weather = await svc.get_latest_weather(request.asset_id)
    risk = await svc.get_latest_risk(request.asset_id)

    # Fetch cascade analysis from Neo4j
    cascade_data = {}
    try:
        from src.app.database.neo4j import get_neo4j_session
        from src.app.services.neo4j_service import Neo4jService
        from src.app.core.graph_scoring import CascadeAnalyzer
        async with get_neo4j_session() as neo4j_session:
            neo4j_svc = Neo4jService(neo4j_session)
            analyzer = CascadeAnalyzer(neo4j_svc)
            cascade_data = await analyzer.analyze_cascade(request.asset_id) or {}
    except Exception as e:
        logger.warning(f"Neo4j cascade analysis error for {request.asset_id}: {e}")

    engine = AdvisoryEngine()
    advisory = await engine.get_asset_advisory(
        asset=asset,
        sensor=sensor,
        dga=dga,
        weather=weather,
        risk=risk,
        cascade=cascade_data,
        question=request.question
    )

    # Persist advisory record
    await svc.save_advisory(
        asset_id=request.asset_id,
        question=request.question,
        response=str(advisory),
        provider=advisory.get("provider", "Local Fallback")
    )

    return AdvisoryResponse(
        asset_id=request.asset_id,
        question=request.question,
        summary=advisory.get("summary", ""),
        risk_factors=advisory.get("risk_factors", []),
        potential_consequences=advisory.get("potential_consequences", []),
        recommended_actions=advisory.get("recommended_actions", []),
        urgency=advisory.get("urgency", "ROUTINE"),
        provider=advisory.get("provider", "Local Fallback"),
        created_at=datetime.now(timezone.utc)
    )
