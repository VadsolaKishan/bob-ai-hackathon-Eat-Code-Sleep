"""
GridPulse AI — Module Integration Adapters
Canonical adapters bridging DGA analysis, Weather risk calculation, and Crew pre-positioning.
Delegates to the canonical core modules:
- src.app.core.dga_classifier
- src.app.core.weather_risk
- src.app.core.crew_dispatch
"""
from typing import Dict, Any, List, Optional
from src.app.core.dga_classifier import classify_dga
from src.app.core.weather_risk import calculate_weather_risk as canonical_weather_risk
from src.app.core.crew_dispatch import generate_crew_preposition_plan, STAGING_HUBS


def _safe_float(obj, attr: str, default: float = 0.0) -> float:
    if obj is None:
        return default
    if isinstance(obj, dict):
        v = obj.get(attr, default)
    else:
        v = getattr(obj, attr, default)
    if isinstance(v, (int, float)):
        return float(v)
    return default


class DGAAdapter:
    """
    Dissolved Gas Analysis fault classifier using canonical IEEE C57.104-inspired DGA module.
    Classifies transformer faults based on dissolved gas concentrations and ratios.
    """

    FAULT_TYPES = {
        "NORMAL": "No significant fault detected — within normal operating limits",
        "THERMAL_LOW": "Low-temperature thermal fault (< 300°C) — overloaded cellulose",
        "THERMAL_HIGH": "High-temperature thermal fault (> 700°C) — oil overheating/pyrolysis",
        "THERMAL": "Thermal fault — overheating detected",
        "ARCING": "High-energy electrical arcing — immediate intervention required",
        "PARTIAL_DISCHARGE": "Partial discharge in gas or oil voids",
        "MULTIPLE_FAULT": "Multiple concurrent fault signatures detected",
    }

    @staticmethod
    def classify_fault_type(dga) -> Dict[str, Any]:
        """
        Classify fault type using canonical DGA classifier with multi-fault recognition.
        
        Args:
            dga: DGAReading object or dict with gas values.
            
        Returns:
            dict with fault_type, severity, ratios, description, key_gases
        """
        h2 = _safe_float(dga, "h2", 0.0)
        ch4 = _safe_float(dga, "ch4", 0.0)
        c2h2 = _safe_float(dga, "c2h2", 0.0)
        c2h4 = _safe_float(dga, "c2h4", 0.0)
        c2h6 = _safe_float(dga, "c2h6", 0.0)
        co = _safe_float(dga, "co", 0.0)
        co2 = _safe_float(dga, "co2", 0.0)

        raw_sample = {
            "h2_ppm": h2,
            "ch4_ppm": ch4,
            "c2h2_ppm": c2h2,
            "c2h4_ppm": c2h4,
            "c2h6_ppm": c2h6,
            "co_ppm": co,
            "co2_ppm": co2,
        }

        canonical_res = classify_dga(raw_sample)

        # Detect multiple concurrent faults
        faults_found = []
        if c2h2 > 3.0:
            faults_found.append("ARCING")
        elif c2h2 > 1.0:
            faults_found.append("PARTIAL_DISCHARGE")

        if c2h4 > 50.0:
            faults_found.append("THERMAL_HIGH")
        elif c2h4 > 20.0:
            faults_found.append("THERMAL_LOW")

        if h2 > 150.0 and "PARTIAL_DISCHARGE" not in faults_found:
            faults_found.append("PARTIAL_DISCHARGE")

        if len(faults_found) > 1:
            fault_type = "MULTIPLE_FAULT"
            severity = "critical"
        elif len(faults_found) == 1:
            fault_type = faults_found[0]
            if fault_type == "ARCING":
                severity = "critical"
            elif fault_type == "THERMAL_HIGH":
                severity = "high"
            elif fault_type in ("THERMAL_LOW", "PARTIAL_DISCHARGE"):
                severity = "medium"
            else:
                severity = canonical_res.severity.lower()
        else:
            fault_type = canonical_res.fault_type
            severity = canonical_res.severity.lower()

        return {
            "fault_type": fault_type,
            "severity": severity,
            "confidence": canonical_res.confidence,
            "ratios": canonical_res.ratios,
            "description": canonical_res.explanation or DGAAdapter.FAULT_TYPES.get(fault_type, "DGA Analysis"),
            "recommended_focus": canonical_res.recommended_focus,
            "key_gases": {
                "h2_ppm": round(h2, 2),
                "c2h2_ppm": round(c2h2, 2),
                "c2h4_ppm": round(c2h4, 2),
                "ch4_ppm": round(ch4, 2),
            },
        }


class WeatherAdapter:
    """
    Weather risk calculator and crew positioning planner.
    Bridges weather readings into the risk engine using canonical weather_risk.py.
    """

    @staticmethod
    def calculate_weather_risk(weather) -> Dict[str, Any]:
        """
        Calculate weather risk score and identify dominant hazard using canonical weather_risk.
        
        Args:
            weather: WeatherReading object or dict.
            
        Returns:
            dict with weather_risk_score (0-1), risk_factors, dominant_hazard, component_scores
        """
        wind = _safe_float(weather, "wind_speed", 0.0)
        rain = _safe_float(weather, "rainfall", 0.0)
        lightning = _safe_float(weather, "lightning_probability", 0.0)
        flood = _safe_float(weather, "flood_risk", 0.0)
        temp = _safe_float(weather, "temperature", 25.0)

        w_dict = {
            "wind_speed": wind,
            "rainfall": rain,
            "lightning_probability": lightning,
            "flood_risk": flood,
            "temperature": temp,
        }

        canonical_res = canonical_weather_risk(w_dict)
        score = canonical_res["weather_risk_score"]
        hazard = canonical_res["dominant_hazard"]
        hazard_display = "heat" if hazard == "temperature" else hazard

        if wind < 20 and rain < 2 and lightning < 0.1 and flood < 0.1 and 15 <= temp <= 30:
            score = 0.0

        risk_factors = []
        if wind > 70:
            risk_factors.append(f"Severe wind: {wind:.1f} km/h (threshold: 70 km/h)")
        elif wind > 45:
            risk_factors.append(f"Elevated wind: {wind:.1f} km/h")

        if temp > 40:
            risk_factors.append(f"Extreme heat: {temp:.1f}°C (threshold: 40°C)")
        elif temp > 35:
            risk_factors.append(f"High temperature: {temp:.1f}°C")

        if lightning > 0.7:
            risk_factors.append(f"High lightning probability: {lightning:.0%}")
        elif lightning > 0.4:
            risk_factors.append(f"Moderate lightning probability: {lightning:.0%}")

        if rain > 30 or flood > 0.5:
            risk_factors.append(f"Flood/heavy rain risk: {rain:.1f} mm/h, flood: {flood:.0%}")
        elif rain > 15 or flood > 0.3:
            risk_factors.append(f"Moderate rainfall: {rain:.1f} mm/h")

        return {
            "weather_risk_score": score,
            "risk_factors": risk_factors,
            "dominant_hazard": hazard_display,
            "component_scores": {
                "wind": min(wind / 70, 1.0),
                "rainfall": min(rain / 30, 1.0),
                "lightning": lightning,
                "flood": flood,
                "temperature": 1.0 if temp >= 45 else (0.7 if temp >= 40 else 0.0),
            },
        }

    @staticmethod
    def generate_crew_positioning(assets_with_risk: List[Dict]) -> Dict[str, Any]:
        """
        Generate a 48-hour crew staging plan based on risk-ranked assets
        using canonical crew_dispatch.py.
        """
        plan = generate_crew_preposition_plan(assets_with_risk, forecast_hours=48)

        asset_assignments = []
        deployment_schedule = []

        for idx, item in enumerate(plan["priority_assets"]):
            risk_level = item.get("priority", "LOW")
            crew_count = 3 if risk_level == "CRITICAL" else (2 if risk_level == "HIGH" else 1)

            asset_assignments.append({
                "rank": idx + 1,
                "asset_id": item["asset_id"],
                "asset_name": item["asset_name"],
                "risk_level": risk_level,
                "final_risk_score": item["priority_score"],
                "staging_hub": item["staging_hub"],
                "crew_count": crew_count,
                "deploy_within": item["staging_window"],
                "required_equipment": item["required_equipment"],
            })

            if risk_level in ("CRITICAL", "HIGH"):
                deployment_schedule.append({
                    "time_window": f"T+{'0' if risk_level == 'CRITICAL' else '24'}h",
                    "asset_id": item["asset_id"],
                    "action": f"Pre-position crew from {item['staging_hub']} to {item['asset_name']}",
                    "priority": risk_level,
                })

        return {
            "crew_hubs": [
                {"hub_id": h["hub_id"], "name": h["name"], "zone": h["zone"], "capacity": 3}
                for h in plan["staging_hubs"]
            ],
            "deployment_schedule": deployment_schedule,
            "asset_assignments": asset_assignments,
            "total_assets": len(asset_assignments),
            "crews_required": sum(a["crew_count"] for a in asset_assignments if a["risk_level"] in ("CRITICAL", "HIGH")),
            "summary": plan["summary"],
        }
