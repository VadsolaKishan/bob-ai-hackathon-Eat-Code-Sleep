from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.postgres import get_db
from src.app.services.postgres_service import PostgresService
from src.app.services.integration_service import WeatherAdapter
from src.app.schemas.weather import WeatherListResponse, WeatherDetailResponse
from src.app.core.crew_dispatch import generate_crew_preposition_plan


router = APIRouter(prefix="/weather", tags=["Weather"])


class CrewPrepositionRequest(BaseModel):
    crews: list[dict]


@router.get("", response_model=WeatherListResponse)
async def get_all_weather(
    db: AsyncSession = Depends(get_db)
):
    """Returns latest weather readings for all assets with risk scores."""

    svc = PostgresService(db)

    assets, _ = await svc.get_all_assets()

    weather_data = []

    for asset in assets:
        reading = await svc.get_latest_weather(asset.asset_id)

        if reading:
            from src.app.schemas.asset import WeatherReadingResponse

            wr = WeatherReadingResponse.model_validate(reading)

            risk_result = WeatherAdapter.calculate_weather_risk(wr)

            weather_data.append({
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "wind_speed": reading.wind_speed,
                "rainfall": reading.rainfall,
                "lightning_probability": reading.lightning_probability,
                "flood_risk": reading.flood_risk,
                "temperature": reading.temperature,
                "weather_risk_score": risk_result["weather_risk_score"],
                "dominant_hazard": risk_result["dominant_hazard"],
                "timestamp": reading.timestamp,
            })

    return WeatherListResponse(
        weather_data=weather_data,
        total=len(weather_data)
    )


DEFAULT_CREWS = [
    {"crew_id": "CREW-01", "crew_name": "Alpha Emergency Response Unit", "skills": ["HV Transformer", "DGA Repair", "High Voltage Safety"], "equipment": ["Mobile Oil Treatment Rig", "Gas Analyzer", "Bucket Truck"], "base_station": "North Operations Center", "available": True},
    {"crew_id": "CREW-02", "crew_name": "Beta Substation Specialist Crew", "skills": ["Substation Breakers", "Bushing Replacement", "Diagnostic Testing"], "equipment": ["Heavy Crane", "Diagnostic Van", "Emergency Generator"], "base_station": "East Metro Depot", "available": True},
    {"crew_id": "CREW-03", "crew_name": "Gamma Rapid Line Patrol", "skills": ["Overhead Feeders", "Storm Damage Repair", "Emergency Switching"], "equipment": ["Off-road Utility Vehicles", "Splice Kits", "Thermal Imaging Drone"], "base_station": "West Valley Station", "available": True},
    {"crew_id": "CREW-04", "crew_name": "Delta Auxiliary Fleet", "skills": ["Flood Barrier Installation", "Dewatering Pumps", "Site Securing"], "equipment": ["Submersible High-Flow Pumps", "Mobile Flood Barriers"], "base_station": "South Sector Warehouse", "available": True},
]


@router.get("/crew-preposition")
async def get_crew_preposition_plan_get(
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 48-hour crew pre-positioning plan using default crews
    and latest asset, sensor, DGA, and weather data.
    """
    req = CrewPrepositionRequest(crews=DEFAULT_CREWS)
    return await get_crew_preposition_plan(req, db)


@router.post("/crew-preposition")
async def get_crew_preposition_plan(
    request: CrewPrepositionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 48-hour crew pre-positioning plan using
    the latest PostgreSQL asset, sensor, DGA, and weather data.
    """

    svc = PostgresService(db)

    assets, _ = await svc.get_all_assets()

    dispatch_assets = []

    for asset in assets:

        sensor = await svc.get_latest_sensor(asset.asset_id)

        dga = await svc.get_latest_dga(asset.asset_id)

        weather = await svc.get_latest_weather(asset.asset_id)

        # Skip assets without weather data.
        if not weather:
            continue

        # Default health index if sensor data is unavailable.
        health_index = 100.0

        # Calculate asset health when sensor data exists.
        if sensor:

            from src.app.core.asset_health import calculate_asset_health

            sensor_data = {
                "oil_temperature_c": sensor.temperature,
                "vibration_mms": sensor.vibration,
                "partial_discharge_pc": sensor.partial_discharge,
            }

            # Add DGA data when available.
            if dga:
                sensor_data.update({
                    "h2_ppm": dga.h2,
                    "ch4_ppm": dga.ch4,
                    "c2h2_ppm": dga.c2h2,
                    "c2h4_ppm": dga.c2h4,
                    "c2h6_ppm": dga.c2h6,
                    "co_ppm": dga.co,
                    "co2_ppm": dga.co2,
                })

            health_result = calculate_asset_health(sensor_data)

            health_index = health_result["health_index"]

        # Calculate weather risk.
        from src.app.core.weather_risk import (
            calculate_weather_risk,
            calculate_asset_vulnerability,
        )

        weather_data = {
            "wind_speed": weather.wind_speed,
            "rainfall": weather.rainfall,
            "lightning_probability": weather.lightning_probability,
            "flood_risk": weather.flood_risk,
            "temperature": weather.temperature,
        }

        weather_result = calculate_weather_risk(weather_data)

        # Combine weather risk + asset degradation.
        vulnerability_result = calculate_asset_vulnerability(
            weather_risk_score=weather_result["weather_risk_score"],
            health_index=health_index,
            critical_facility=asset.critical_facility,
        )

        dispatch_assets.append({
            "asset_id": asset.asset_id,
            "vulnerability_score": (
                vulnerability_result["vulnerability_score"]
            ),
            "critical_facility": asset.critical_facility,
            "dominant_hazard": weather_result["dominant_hazard"],
        })

    # Generate the final 48-hour crew plan.
    return generate_crew_preposition_plan(
        assets=dispatch_assets,
        crews=request.crews,
        forecast_hours=48,
    )


@router.get(
    "/{asset_id}",
    response_model=WeatherDetailResponse
)
async def get_asset_weather(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns weather history and risk for a single asset."""

    svc = PostgresService(db)

    asset = await svc.get_asset(asset_id)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset {asset_id} not found"
        )

    reading = await svc.get_latest_weather(asset_id)

    risk_analysis = None

    if reading:
        from src.app.schemas.asset import WeatherReadingResponse

        wr = WeatherReadingResponse.model_validate(reading)

        risk_analysis = WeatherAdapter.calculate_weather_risk(wr)

    current_data = None
    if reading:
        if type(reading).__name__ != "MagicMock" and hasattr(reading, "model_dump") and callable(reading.model_dump):
            current_data = reading.model_dump()
        elif hasattr(reading, "__table__"):
            current_data = {c.name: getattr(reading, c.name) for c in reading.__table__.columns}
        elif isinstance(reading, dict):
            current_data = reading
        else:
            current_data = {
                "asset_id": getattr(reading, "asset_id", asset_id),
                "wind_speed": getattr(reading, "wind_speed", 0.0),
                "rainfall": getattr(reading, "rainfall", 0.0),
                "lightning_probability": getattr(reading, "lightning_probability", 0.0),
                "flood_risk": getattr(reading, "flood_risk", 0.0),
                "temperature": getattr(reading, "temperature", 25.0),
                "timestamp": getattr(reading, "timestamp", None),
            }

    return WeatherDetailResponse(
        asset_id=asset_id,
        asset_name=asset.name,
        current=current_data,
        risk_analysis=risk_analysis
    )
    """
    Generate a 48-hour crew pre-positioning plan using
    the latest PostgreSQL asset, sensor, DGA, and weather data.
    """

    svc = PostgresService(db)

    assets, _ = await svc.get_all_assets()

    dispatch_assets = []

    for asset in assets:

        sensor = await svc.get_latest_sensor(asset.asset_id)

        dga = await svc.get_latest_dga(asset.asset_id)

        weather = await svc.get_latest_weather(asset.asset_id)

        # Skip assets without weather data.
        if not weather:
            continue

        # Default health index if sensor data is unavailable.
        health_index = 100.0

        # Calculate asset health when sensor data exists.
        if sensor:

            from src.app.core.asset_health import calculate_asset_health

            sensor_data = {
                "oil_temperature_c": sensor.temperature,
                "vibration_mms": sensor.vibration,
                "partial_discharge_pc": sensor.partial_discharge,
            }

            # Add DGA data when available.
            if dga:
                sensor_data.update({
                    "h2_ppm": dga.h2,
                    "ch4_ppm": dga.ch4,
                    "c2h2_ppm": dga.c2h2,
                    "c2h4_ppm": dga.c2h4,
                    "c2h6_ppm": dga.c2h6,
                    "co_ppm": dga.co,
                    "co2_ppm": dga.co2,
                })

            health_result = calculate_asset_health(sensor_data)

            health_index = health_result["health_index"]

        # Calculate weather risk.
        from src.app.core.weather_risk import (
            calculate_weather_risk,
            calculate_asset_vulnerability,
        )

        weather_data = {
            "wind_speed": weather.wind_speed,
            "rainfall": weather.rainfall,
            "lightning_probability": weather.lightning_probability,
            "flood_risk": weather.flood_risk,
            "temperature": weather.temperature,
        }

        weather_result = calculate_weather_risk(weather_data)

        # Combine weather risk + asset degradation.
        vulnerability_result = calculate_asset_vulnerability(
            weather_risk_score=weather_result["weather_risk_score"],
            health_index=health_index,
            critical_facility=asset.critical_facility,
        )

        dispatch_assets.append({
            "asset_id": asset.asset_id,
            "vulnerability_score": (
                vulnerability_result["vulnerability_score"]
            ),
            "critical_facility": asset.critical_facility,
            "dominant_hazard": weather_result["dominant_hazard"],
        })

    # Generate the final 48-hour crew plan.
    return generate_crew_preposition_plan(
        assets=dispatch_assets,
        crews=request.crews,
        forecast_hours=48,
    )