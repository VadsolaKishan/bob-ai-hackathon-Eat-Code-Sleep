"""
GridPulse AI — Recommendations & Work Orders Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.app.database.postgres import get_db
from src.app.schemas.risk import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse
from src.app.services.postgres_service import PostgresService

router = APIRouter(tags=["Recommendations"])


@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """Auto-generates work order recommendations from current risk scores."""
    svc = PostgresService(db)
    assets, _ = await svc.get_all_assets()

    recommendations = []
    for asset in assets:
        risk = await svc.get_latest_risk(asset.asset_id)
        if risk:
            if risk.risk_level == "CRITICAL":
                action = "Immediate inspection and crew pre-positioning required"
                priority = "critical"
            elif risk.risk_level == "HIGH":
                action = "Inspection required within 24 hours"
                priority = "high"
            elif risk.risk_level == "MEDIUM":
                action = "Schedule preventive maintenance"
                priority = "medium"
            else:
                action = "Continue normal monitoring"
                priority = "low"

            recommendations.append({
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "priority": priority,
                "action": action,
                "risk_level": risk.risk_level,
                "final_risk_score": risk.final_risk_score,
            })

    recommendations.sort(
        key=lambda x: ["low", "medium", "high", "critical"].index(x["priority"]),
        reverse=True
    )
    return {"work_orders": recommendations, "total": len(recommendations)}


@router.get("/workorders", response_model=List[WorkOrderResponse])
async def get_all_workorders(db: AsyncSession = Depends(get_db)):
    """Returns all work orders across the grid."""
    svc = PostgresService(db)
    return await svc.get_all_workorders()


@router.get("/assets/{asset_id}/workorders", response_model=List[WorkOrderResponse])
async def get_asset_workorders(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Returns work orders for a specific asset."""
    svc = PostgresService(db)
    asset = await svc.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return await svc.get_workorders(asset_id)


@router.post("/assets/{asset_id}/workorders", response_model=WorkOrderResponse, status_code=201)
async def create_workorder(
    asset_id: str,
    data: WorkOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Creates a work order for a specific asset."""
    svc = PostgresService(db)
    asset = await svc.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    data.asset_id = asset_id
    return await svc.create_workorder(data)


@router.patch("/workorders/{workorder_id}", response_model=WorkOrderResponse)
async def update_workorder(
    workorder_id: int,
    data: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Updates a work order's status or assignment."""
    svc = PostgresService(db)
    wo = await svc.update_workorder(workorder_id, data)
    if not wo:
        raise HTTPException(status_code=404, detail=f"Work order {workorder_id} not found")
    return wo
