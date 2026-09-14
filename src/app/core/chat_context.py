"""
GridPulse AI — Chat Context Builder
Constructs structured, grounded context from PostgreSQL, Neo4j, Risk Engine, DGA, Weather, and Crew Dispatch.
"""
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.services.postgres_service import PostgresService
from src.app.core.chat_intent import ChatIntent
from src.app.core.asset_health import calculate_asset_health
from src.app.core.weather_risk import calculate_weather_risk, analyze_storm_asset_vulnerability
from src.app.core.crew_dispatch import generate_crew_preposition_plan
from src.app.core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class ChatContextBuilder:
    """
    Builds data-rich, intent-tailored context for operators and AI advisory.
    """

    def __init__(self, db: AsyncSession, neo4j_svc=None):
        self.db = db
        self.pg_svc = PostgresService(db)
        self.neo4j_svc = neo4j_svc
        self.risk_engine = RiskEngine(db, neo4j_svc) if neo4j_svc else None

    async def build_context(
        self,
        intent: ChatIntent,
        asset_ids: List[str],
        user_message: str
    ) -> Dict[str, Any]:
        """
        Builds focused context dictionary matching the detected intent and assets.
        """
        context: Dict[str, Any] = {
            "intent": intent.value,
            "queried_assets": asset_ids,
            "user_question": user_message,
        }

        # 0. Handle unknown / unmonitored asset queries directly
        if intent == ChatIntent.UNKNOWN_ASSET:
            unknown_id = asset_ids[0] if asset_ids else "unspecified asset"
            context["unknown_asset_id"] = unknown_id
            context["primary_asset"] = {"asset_id": unknown_id, "found": False}
            return context

        # 1. Handle multi-asset / comparison intent
        if intent == ChatIntent.COMPARE_ASSETS and len(asset_ids) >= 2:
            context["comparison"] = [
                await self.get_full_asset_profile(aid) for aid in asset_ids[:2]
            ]
            return context

        # 2. Handle single asset queries
        if asset_ids:
            primary_id = asset_ids[0]
            context["primary_asset"] = await self.get_full_asset_profile(primary_id)

            # If cascade or critical facility question, fetch Neo4j graph details
            if intent in (ChatIntent.CASCADE_IMPACT, ChatIntent.CRITICAL_FACILITY):
                context["cascade_details"] = await self._get_cascade_details(primary_id)

            return context

        # 3. Handle grid-wide questions
        all_assets, total = await self.pg_svc.get_all_assets()
        context["total_assets"] = total

        # Gather brief profiles for all assets
        asset_summaries = []
        for a in all_assets:
            risk = await self.pg_svc.get_latest_risk(a.asset_id)
            weather = await self.pg_svc.get_latest_weather(a.asset_id)
            sensor = await self.pg_svc.get_latest_sensor(a.asset_id)
            dga = await self.pg_svc.get_latest_dga(a.asset_id)

            w_score = 0.0
            w_hazard = "none"
            if weather:
                w_res = calculate_weather_risk({
                    "wind_speed": weather.wind_speed,
                    "rainfall": weather.rainfall,
                    "lightning_probability": weather.lightning_probability,
                    "flood_risk": weather.flood_risk,
                    "temperature": weather.temperature,
                })
                w_score = w_res["weather_risk_score"]
                w_hazard = w_res["dominant_hazard"]

            # Quick asset health
            hi = 100.0
            dga_sev = "LOW"
            if sensor:
                s_data = {
                    "oil_temperature_c": sensor.temperature,
                    "vibration_mms": sensor.vibration,
                    "partial_discharge_pc": sensor.partial_discharge,
                }
                if dga:
                    s_data.update({
                        "h2_ppm": dga.h2, "ch4_ppm": dga.ch4, "c2h2_ppm": dga.c2h2,
                        "c2h4_ppm": dga.c2h4, "c2h6_ppm": dga.c2h6, "co_ppm": dga.co, "co2_ppm": dga.co2
                    })
                h_res = calculate_asset_health(s_data)
                hi = h_res["health_index"]
                dga_sev = h_res.get("dga_severity", "LOW")

            asset_summaries.append({
                "asset_id": a.asset_id,
                "name": a.name,
                "asset_type": str(a.asset_type.value if hasattr(a.asset_type, "value") else a.asset_type),
                "critical_facility": a.critical_facility,
                "facility_type": a.facility_type,
                "final_risk_score": risk.final_risk_score if risk else 0.5,
                "risk_level": risk.risk_level if risk else "UNKNOWN",
                "health_index": hi,
                "dga_severity": dga_sev,
                "weather_risk_score": w_score,
                "dominant_hazard": w_hazard,
            })

        # Sort assets by risk score descending
        asset_summaries.sort(key=lambda x: x["final_risk_score"], reverse=True)
        context["ranked_assets"] = asset_summaries
        context["top_asset"] = asset_summaries[0] if asset_summaries else None

        # Filter specifically for intents
        if intent == ChatIntent.LIGHTNING_ASSETS:
            context["lightning_assets"] = [
                a for a in asset_summaries if a["dominant_hazard"] == "lightning" or a["weather_risk_score"] > 0.4
            ]
        elif intent == ChatIntent.DGA_WARNING_ASSETS:
            context["dga_warning_assets"] = [
                a for a in asset_summaries if a["dga_severity"] in ("MEDIUM", "HIGH", "CRITICAL")
            ]
        elif intent == ChatIntent.COMPOUND_RISK:
            context["compound_risk_assets"] = [
                a for a in asset_summaries if a["health_index"] < 65.0 and a["weather_risk_score"] > 0.4
            ]

        # 48-Hour crew plan
        crew_plan = generate_crew_preposition_plan(asset_summaries)
        context["crew_plan"] = crew_plan

        return context

    async def get_full_asset_profile(self, asset_id: str) -> Dict[str, Any]:
        """
        Retrieves a 360-degree operational profile for a single asset.
        """
        asset = await self.pg_svc.get_asset(asset_id)
        if not asset:
            return {"asset_id": asset_id, "found": False}

        sensor = await self.pg_svc.get_latest_sensor(asset_id)
        dga = await self.pg_svc.get_latest_dga(asset_id)
        weather = await self.pg_svc.get_latest_weather(asset_id)
        risk = await self.pg_svc.get_latest_risk(asset_id)
        incidents = await self.pg_svc.get_incidents_for_asset(asset_id, limit=5)

        # 1. Sensor Data
        sensor_info = None
        sensor_dict = {}
        if sensor:
            sensor_dict = {
                "oil_temperature_c": sensor.temperature,
                "vibration_mms": sensor.vibration,
                "partial_discharge_pc": sensor.partial_discharge,
            }
            sensor_info = {
                "temperature_c": sensor.temperature,
                "vibration_mms": sensor.vibration,
                "partial_discharge_pc": sensor.partial_discharge,
                "timestamp": sensor.timestamp.isoformat() if sensor.timestamp else None,
            }

        # 2. DGA Data & Classification
        dga_info = None
        if dga:
            sensor_dict.update({
                "h2_ppm": dga.h2, "ch4_ppm": dga.ch4, "c2h6_ppm": dga.c2h6,
                "c2h4_ppm": dga.c2h4, "c2h2_ppm": dga.c2h2, "co_ppm": dga.co, "co2_ppm": dga.co2
            })
            dga_info = {
                "h2": dga.h2, "ch4": dga.ch4, "c2h2": dga.c2h2,
                "c2h4": dga.c2h4, "c2h6": dga.c2h6, "co": dga.co, "co2": dga.co2,
                "timestamp": dga.timestamp.isoformat() if dga.timestamp else None,
            }

        # 3. Canonical Asset Health Index
        health_res = calculate_asset_health(sensor_dict)

        # 4. Canonical Weather Risk
        weather_info = None
        weather_risk_score = 0.1
        dominant_hazard = "none"
        if weather:
            w_input = {
                "wind_speed": weather.wind_speed,
                "rainfall": weather.rainfall,
                "lightning_probability": weather.lightning_probability,
                "flood_risk": weather.flood_risk,
                "temperature": weather.temperature,
            }
            w_res = calculate_weather_risk(w_input)
            weather_risk_score = w_res["weather_risk_score"]
            dominant_hazard = w_res["dominant_hazard"]
            weather_info = {
                **w_input,
                "weather_risk_score": weather_risk_score,
                "dominant_hazard": dominant_hazard,
                "timestamp": weather.timestamp.isoformat() if weather.timestamp else None,
            }

        # 5. Vulnerability
        vulnerability = analyze_storm_asset_vulnerability(
            weather={
                "wind_speed": weather.wind_speed if weather else 20.0,
                "rainfall": weather.rainfall if weather else 0.0,
                "lightning_probability": weather.lightning_probability if weather else 0.05,
                "flood_risk": weather.flood_risk if weather else 0.05,
                "temperature": weather.temperature if weather else 25.0,
            },
            health_index=health_res["health_index"],
            critical_facility=asset.critical_facility,
        )

        # 6. Cascade Impact
        cascade_data = await self._get_cascade_details(asset_id)

        # 7. Crew Staging Recommendation
        crew_plan = generate_crew_preposition_plan([{
            "asset_id": asset_id,
            "asset_name": asset.name,
            "vulnerability_score": vulnerability["vulnerability_score"],
            "critical_facility": asset.critical_facility,
            "dominant_hazard": dominant_hazard,
        }])
        crew_rec = crew_plan["priority_assets"][0] if crew_plan["priority_assets"] else {}

        return {
            "asset_id": asset_id,
            "found": True,
            "name": asset.name,
            "asset_type": str(asset.asset_type.value if hasattr(asset.asset_type, "value") else asset.asset_type),
            "capacity": asset.capacity,
            "critical_facility": asset.critical_facility,
            "facility_type": asset.facility_type,
            "status": asset.status,
            "latitude": asset.latitude,
            "longitude": asset.longitude,
            "sensor": sensor_info,
            "dga": dga_info,
            "health": {
                "health_index": health_res["health_index"],
                "health_band": health_res["health_band"],
                "dominant_risk": health_res["dominant_risk"],
                "dga_fault_type": health_res["dga_fault_type"],
                "dga_severity": health_res["dga_severity"],
                "dga_confidence": health_res["dga_confidence"],
                "explanation": health_res["explanation"],
                "recommended_action": health_res["recommended_action"],
            },
            "weather": weather_info,
            "vulnerability": vulnerability,
            "risk": {
                "final_risk_score": risk.final_risk_score if risk else 0.5,
                "risk_level": risk.risk_level if risk else "UNKNOWN",
                "failure_probability": risk.failure_probability if risk else 0.3,
                "asset_health_risk": risk.asset_health_risk if risk else 0.3,
                "weather_risk": risk.weather_risk if risk else weather_risk_score,
                "grid_impact": risk.grid_impact if risk else 0.3,
                "cascade_risk": risk.cascade_risk if risk else 0.2,
                "critical_multiplier": risk.critical_multiplier if risk else 1.0,
            },
            "cascade": cascade_data,
            "incidents": incidents,
            "crew": crew_rec,
        }

    async def _get_cascade_details(self, asset_id: str) -> Dict[str, Any]:
        """Fetches cascade data from Neo4j or provides clear fallback."""
        if not self.neo4j_svc:
            return {
                "available": False,
                "explanation": "Neo4j graph engine unavailable; cascade analysis could not be calculated.",
                "affected_asset_count": 0,
                "critical_facility_count": 0,
                "affected_facilities": [],
                "cascade_path": [asset_id],
                "cascade_risk": 0.2,
                "grid_impact": 0.3,
            }

        from src.app.core.graph_scoring import CascadeAnalyzer
        try:
            analyzer = CascadeAnalyzer(self.neo4j_svc)
            cascade = await analyzer.analyze_cascade(asset_id)
            if cascade:
                cascade["available"] = True
                return cascade
        except Exception as e:
            logger.warning(f"Error querying Neo4j cascade for {asset_id}: {e}")

        return {
            "available": False,
            "explanation": "Neo4j unavailable or asset has no graph connections.",
            "affected_asset_count": 0,
            "critical_facility_count": 0,
            "affected_facilities": [],
            "cascade_path": [asset_id],
            "cascade_risk": 0.2,
            "grid_impact": 0.3,
        }
