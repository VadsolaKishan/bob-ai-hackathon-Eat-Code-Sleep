"""
GridPulse AI — Dashboard Router
Handles /api/v1/dashboard endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.postgres import get_db
from src.app.services.postgres_service import PostgresService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Returns aggregated data for the main dashboard."""
    svc = PostgresService(db)
    assets, total = await svc.get_all_assets()

    risk_distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    top_risk_assets = []
    weather_alerts = []

    for asset in assets:
        risk = await svc.get_latest_risk(asset.asset_id)
        if risk:
            level = risk.risk_level
            if level in risk_distribution:
                risk_distribution[level] += 1
            top_risk_assets.append({
                "asset_id": asset.asset_id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "risk_level": risk.risk_level,
                "final_risk_score": risk.final_risk_score,
                "latitude": asset.latitude,
                "longitude": asset.longitude,
            })

        weather = await svc.get_latest_weather(asset.asset_id)
        if weather and (weather.wind_speed > 60 or weather.lightning_probability > 0.6 or weather.flood_risk > 0.5):
            weather_alerts.append({
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "wind_speed": weather.wind_speed,
                "lightning_probability": weather.lightning_probability,
                "flood_risk": weather.flood_risk,
                "temperature": weather.temperature,
            })

    top_risk_assets.sort(key=lambda x: x.get("final_risk_score", 0), reverse=True)
    top5 = top_risk_assets[:5]

    recent_incidents = await svc.get_recent_incidents(limit=5)
    active_work_orders = await svc.count_workorders_by_status("pending") + \
                         await svc.count_workorders_by_status("in_progress") + \
                         await svc.count_workorders_by_status("assigned")

    return {
        "summary": {
            "total_assets": total,
            "critical_count": risk_distribution["CRITICAL"],
            "high_count": risk_distribution["HIGH"],
            "medium_count": risk_distribution["MEDIUM"],
            "low_count": risk_distribution["LOW"],
            "active_work_orders": active_work_orders,
        },
        "top_risk_assets": top5,
        "recent_incidents": recent_incidents,
        "weather_alerts": weather_alerts,
        "risk_distribution": risk_distribution,
    }
