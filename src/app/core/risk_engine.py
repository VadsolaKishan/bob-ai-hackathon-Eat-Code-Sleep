"""
GridPulse AI — Risk Engine
Computes multi-factor risk scores from PostgreSQL + Neo4j data.
Integrates canonical DGA classifier, Asset Health Index, and Weather Risk modules.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.services.postgres_service import PostgresService
from src.app.core.asset_health import calculate_asset_health
from src.app.core.weather_risk import calculate_weather_risk

logger = logging.getLogger(__name__)

# Critical facility types and their multipliers (matching CONTRACT.md)
CRITICAL_FACILITY_TYPES = {"hospital", "water_plant", "airport", "data_center", "emergency_services"}
IMPORTANT_FACILITY_TYPES = {"school", "fire_station", "police_station"}


def classify_risk_level(score: float) -> str:
    """Classify final risk score into LOW/MEDIUM/HIGH/CRITICAL (CONTRACT.md thresholds)."""
    if score >= 0.85:
        return "CRITICAL"
    elif score >= 0.70:
        return "HIGH"
    elif score >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"


def get_critical_multiplier(asset) -> float:
    """Returns the critical facility multiplier based on asset attributes."""
    if not asset:
        return settings.multiplier_normal
    if not getattr(asset, "critical_facility", False):
        return settings.multiplier_normal
    ft = (getattr(asset, "facility_type", "") or "").lower()
    if ft in CRITICAL_FACILITY_TYPES:
        return settings.multiplier_critical
    if ft in IMPORTANT_FACILITY_TYPES:
        return settings.multiplier_important
    return settings.multiplier_important


def _get_float_attr(obj, attr: str, default: float = 0.0) -> float:
    """Safely extracts a float attribute from an object, dict, or MagicMock."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(attr, default)
    else:
        val = getattr(obj, attr, default)
    if isinstance(val, (int, float)):
        return float(val)
    return default


def compute_failure_probability(sensor, dga) -> float:
    """
    Computes failure probability (0-1) from sensor and DGA readings
    using canonical Asset Health Index and physical stress components.
    """
    if not sensor and not dga:
        return 0.3  # default moderate risk when no data

    temp = _get_float_attr(sensor, "temperature", 65.0)
    vib = _get_float_attr(sensor, "vibration", 1.5)
    pd = _get_float_attr(sensor, "partial_discharge", 120.0)

    h2 = _get_float_attr(dga, "h2", 0.0)
    ch4 = _get_float_attr(dga, "ch4", 0.0)
    c2h6 = _get_float_attr(dga, "c2h6", 0.0)
    c2h4 = _get_float_attr(dga, "c2h4", 0.0)
    c2h2 = _get_float_attr(dga, "c2h2", 0.0)
    co = _get_float_attr(dga, "co", 0.0)
    co2 = _get_float_attr(dga, "co2", 0.0)

    sensor_data = {
        "oil_temperature_c": temp,
        "vibration_mms": vib,
        "partial_discharge_pc": pd,
        "h2_ppm": h2,
        "ch4_ppm": ch4,
        "c2h6_ppm": c2h6,
        "c2h4_ppm": c2h4,
        "c2h2_ppm": c2h2,
        "co_ppm": co,
        "co2_ppm": co2,
    }

    health_res = calculate_asset_health(sensor_data)
    hi = health_res["health_index"]
    degradation = max(0.0, min(1.0, (100.0 - hi) / 100.0))

    # Thermal component (0 - 0.25)
    if temp <= 65:
        thermal = 0.0
    elif temp <= 85:
        thermal = (temp - 65) / 80.0
    else:
        thermal = 0.25 + min(0.25, (temp - 85) / 40.0)

    # Vibration component (0 - 0.20)
    if vib <= 2.0:
        vib_score = 0.0
    elif vib <= 4.5:
        vib_score = (vib - 2.0) / 12.5
    else:
        vib_score = 0.20 + min(0.10, (vib - 4.5) / 15.0)

    # Partial Discharge component (0 - 0.25)
    if pd <= 200:
        pd_score = 0.0
    elif pd <= 500:
        pd_score = (pd - 200) / 1200.0
    else:
        pd_score = 0.25 + min(0.25, (pd - 500) / 2000.0)

    # DGA component (0 - 0.30) informed by canonical DGA
    dga_sev = health_res.get("dga_severity", "LOW")
    if c2h2 > 3.0 or dga_sev == "CRITICAL":
        dga_comp = 0.30
    elif c2h2 > 1.0 or dga_sev == "HIGH":
        dga_comp = 0.20
    elif c2h4 > 50.0 or dga_sev == "MEDIUM":
        dga_comp = 0.15
    elif h2 > 150.0:
        dga_comp = 0.10
    else:
        dga_comp = 0.0

    raw_total = thermal + vib_score + pd_score + dga_comp
    if c2h2 > 3.0 or dga_sev == "CRITICAL":
        prob = max(0.70, raw_total, degradation)
    elif c2h2 > 1.0 or dga_sev == "HIGH":
        prob = max(0.50, raw_total, degradation)
    else:
        prob = (degradation * 0.40) + (raw_total * 0.60)
    return min(round(prob, 3), 1.0)


def compute_asset_health_risk(value: float) -> float:
    """
    Converts either failure probability or health index into an asset health risk score (0-1).
    Clamped to [0.0, 1.0].
    """
    if value > 1.0:
        return round(max(0.0, min(1.0, (100.0 - value) / 100.0)), 3)
    return min(round(value * 0.9 + 0.05, 3), 1.0)


def compute_weather_risk(weather) -> float:
    """
    Computes weather risk score (0-1) using canonical weather_risk.py.
    """
    if not weather:
        return 0.1

    wind = _get_float_attr(weather, "wind_speed", 0.0)
    rain = _get_float_attr(weather, "rainfall", 0.0)
    lightning = _get_float_attr(weather, "lightning_probability", 0.0)
    flood = _get_float_attr(weather, "flood_risk", 0.0)
    temp = _get_float_attr(weather, "temperature", 25.0)

    w_dict = {
        "wind_speed": wind,
        "rainfall": rain,
        "lightning_probability": lightning,
        "flood_risk": flood,
        "temperature": temp,
    }

    result = calculate_weather_risk(w_dict)
    score = result["weather_risk_score"]

    if wind < 20 and rain < 2 and lightning < 0.1 and flood < 0.1 and 15 <= temp <= 30:
        return 0.0

    return score


class RiskEngine:
    """
    Canonical multi-factor risk engine orchestrating:
    - Canonical DGA classifier & Asset Health Index
    - Canonical Weather-Risk Fusion
    - Neo4j Graph Impact & Cascade Risk
    - Critical Facility Multiplier
    - PostgreSQL persistence
    """

    def __init__(self, db: AsyncSession, neo4j_svc):
        self.db = db
        self.neo4j_svc = neo4j_svc
        self.pg_svc = PostgresService(db)

    async def compute_risk(self, asset_id: str) -> Dict[str, Any]:
        """
        Full risk computation pipeline:
        1. Fetch asset + latest readings from PostgreSQL
        2. Compute canonical Asset Health & DGA classification
        3. Compute canonical Weather risk
        4. Fetch graph impact & cascade risk from Neo4j
        5. Apply CONTRACT.md weighted formula and critical multiplier
        6. Persist RiskScore and return structured result
        """
        # 1. Fetch data
        asset = await self.pg_svc.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        sensor = await self.pg_svc.get_latest_sensor(asset_id)
        dga = await self.pg_svc.get_latest_dga(asset_id)
        weather = await self.pg_svc.get_latest_weather(asset_id)

        # 2. Canonical Asset Health & DGA
        sensor_data: Dict[str, Any] = {}
        if sensor:
            sensor_data["oil_temperature_c"] = sensor.temperature
            sensor_data["vibration_mms"] = sensor.vibration
            sensor_data["partial_discharge_pc"] = sensor.partial_discharge
        if dga:
            sensor_data["h2_ppm"] = dga.h2
            sensor_data["ch4_ppm"] = dga.ch4
            sensor_data["c2h6_ppm"] = dga.c2h6
            sensor_data["c2h4_ppm"] = dga.c2h4
            sensor_data["c2h2_ppm"] = dga.c2h2
            sensor_data["co_ppm"] = dga.co
            sensor_data["co2_ppm"] = dga.co2

        health_res = calculate_asset_health(sensor_data)
        health_index = health_res["health_index"]
        asset_health_risk = round(max(0.0, min(1.0, (100.0 - health_index) / 100.0)), 3)
        failure_prob = compute_failure_probability(sensor, dga)

        # 3. Canonical Weather risk
        weather_risk = compute_weather_risk(weather)

        # 4. Graph impact & cascade from Neo4j
        try:
            grid_impact = await self.neo4j_svc.calculate_graph_impact(asset_id)
            cascade_risk = await self._compute_cascade_risk(asset_id)
        except Exception as e:
            logger.warning(f"Neo4j unavailable for {asset_id}, using defaults: {e}")
            grid_impact = 0.3
            cascade_risk = 0.2

        # 5. Apply CONTRACT formula
        critical_multiplier = get_critical_multiplier(asset)

        base_risk = (
            settings.weight_failure_probability * failure_prob
            + settings.weight_asset_health * asset_health_risk
            + settings.weight_weather * weather_risk
            + settings.weight_grid_impact * grid_impact
            + settings.weight_cascade * cascade_risk
        )

        final_risk_score = min(round(base_risk * critical_multiplier, 4), 1.0)
        risk_level = classify_risk_level(final_risk_score)

        # Build explanation of why this asset has this score
        reasons = []
        if health_res.get("dga_severity") in ("HIGH", "CRITICAL"):
            reasons.append(f"DGA indicates {health_res.get('dga_fault_type')} fault ({health_res.get('dga_severity')})")
        if health_res.get("dominant_risk"):
            reasons.append(f"Dominant internal risk: {health_res.get('dominant_risk')}")
        if weather_risk > 0.4:
            reasons.append(f"Elevated weather stress (risk: {weather_risk:.2f})")
        if critical_multiplier > 1.0:
            facility_type = getattr(asset, "facility_type", "critical facility") or "critical facility"
            reasons.append(f"Supplies {facility_type} ({critical_multiplier}x critical multiplier)")
        if cascade_risk > 0.4:
            reasons.append(f"High cascade risk ({cascade_risk:.2f}) to downstream grid assets")

        explanation = "; ".join(reasons) if reasons else f"Standard operational status. Health index: {health_index:.1f}/100."

        # 6. Persist to PostgreSQL
        score_data = {
            "asset_id": asset_id,
            "timestamp": datetime.now(timezone.utc),
            "failure_probability": failure_prob,
            "asset_health_risk": asset_health_risk,
            "weather_risk": weather_risk,
            "grid_impact": grid_impact,
            "cascade_risk": cascade_risk,
            "critical_multiplier": critical_multiplier,
            "final_risk_score": final_risk_score,
            "risk_level": risk_level,
        }
        await self.pg_svc.save_risk_score(score_data)

        return {
            **score_data,
            "asset_name": asset.name,
            "asset_type": asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
            "health_index": health_index,
            "health_band": health_res.get("health_band", "GOOD"),
            "dga_fault_type": health_res.get("dga_fault_type", "NORMAL"),
            "dga_severity": health_res.get("dga_severity", "LOW"),
            "explanation": explanation,
            "timestamp": score_data["timestamp"].isoformat(),
        }

    async def _compute_cascade_risk(self, asset_id: str) -> float:
        """Compute cascade risk via Neo4j downstream analysis."""
        from src.app.core.graph_scoring import CascadeAnalyzer
        try:
            analyzer = CascadeAnalyzer(self.neo4j_svc)
            result = await analyzer.analyze_cascade(asset_id)
            return result.get("cascade_risk", 0.2) if result else 0.2
        except Exception as e:
            logger.warning(f"Cascade calculation error for {asset_id}: {e}")
            return 0.2
