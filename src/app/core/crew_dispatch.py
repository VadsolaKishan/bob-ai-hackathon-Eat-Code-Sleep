"""
GridPulse AI - 48-Hour Crew Pre-Positioning Engine
Prioritizes grid assets and generates an operational crew pre-positioning plan based on:
- Predicted composite risk score
- Weather vulnerability & dominant storm threat
- Asset degradation and DGA fault signatures
- Critical facility impact (hospitals, water plants, airports)
- Available crew capabilities and staging locations
- 48-hour planning horizon and staging windows
"""
from typing import List, Dict, Any, Optional

DEFAULT_CREWS = [
    {
        "crew_id": "CREW-01",
        "name": "Rapid Response High-Voltage Alpha",
        "base_hub": "North Operations Center",
        "specialty": "Transformer Diagnostics & Mobile Substation",
        "equipment": "Mobile Transformer Backup Unit & Online DGA Kit",
        "available": True,
    },
    {
        "crew_id": "CREW-02",
        "name": "Storm Line Repair Bravo",
        "base_hub": "East Metro Depot",
        "specialty": "Overhead Line & Storm Clearance",
        "equipment": "Bucket Trucks & Heavy Vegetation Clears",
        "available": True,
    },
    {
        "crew_id": "CREW-03",
        "name": "Substation Protection Delta",
        "base_hub": "West Valley Station",
        "specialty": "Switchgear & Surge Protection",
        "equipment": "Relay Testers & Surge Arrestor Spares",
        "available": True,
    },
    {
        "crew_id": "CREW-04",
        "name": "Emergency Standby Echo",
        "base_hub": "North Operations Center",
        "specialty": "General Grid Maintenance",
        "equipment": "Rapid Deployment Service Van",
        "available": False,
    },
]

STAGING_HUBS = [
    {
        "hub_id": "HUB-NORTH",
        "name": "North Operations Center",
        "zone": "North Cascade",
        "serves": ["SUB-001", "TX-001", "TX-002", "FD-001", "CF-001"],
        "assigned_crews": ["CREW-01", "CREW-04"],
    },
    {
        "hub_id": "HUB-EAST",
        "name": "East Metro Depot",
        "zone": "Metro Harbor & East Valley",
        "serves": ["SUB-002", "TX-003", "FD-002"],
        "assigned_crews": ["CREW-02"],
    },
    {
        "hub_id": "HUB-WEST",
        "name": "West Valley Station",
        "zone": "Valley Solar Intertie",
        "serves": ["TX-004", "FD-003"],
        "assigned_crews": ["CREW-03"],
    },
]


def _determine_staging_hub(asset_id: str) -> Dict[str, str]:
    """Finds matching staging hub for asset based on operational zone."""
    for hub in STAGING_HUBS:
        if asset_id in hub["serves"]:
            return {"hub_id": hub["hub_id"], "hub_name": hub["name"], "zone": hub["zone"]}
    return {"hub_id": "HUB-NORTH", "hub_name": "North Operations Center", "zone": "North Cascade"}


def _determine_equipment_needs(dominant_hazard: str, is_critical: bool, is_transformer: bool) -> str:
    """Returns required specialized equipment based on hazard and asset profile."""
    if dominant_hazard == "lightning":
        return "Surge Arrestor Kit & Substation Relay Testing Rig"
    elif dominant_hazard == "wind":
        return "High-reach Bucket Truck & Line Tensioning Winch"
    elif dominant_hazard == "flood" or dominant_hazard == "rainfall":
        return "Submersible Pumps & Sandbagging Staging Unit"
    elif is_transformer and is_critical:
        return "Mobile Transformer Backup Unit & Oil Degassing System"
    return "Standard Diagnostic Van & Protective PPE"


def generate_crew_preposition_plan(
    assets: List[Dict[str, Any]],
    crews: Optional[List[Dict[str, Any]]] = None,
    forecast_hours: int = 48
) -> Dict[str, Any]:
    """
    Generate a 48-hour crew pre-positioning plan.

    Args:
        assets: List of dicts with:
            - asset_id (str)
            - vulnerability_score (float, 0-1) or final_risk_score (float, 0-1)
            - critical_facility (bool)
            - dominant_hazard (str)
            - optional: asset_name, facility_type
        crews: Optional list of available crews. Defaults to DEFAULT_CREWS.
        forecast_hours: Planning horizon (default 48).

    Returns:
        Structured plan with priority_assets, crew_assignments, staging_hubs, and operational summary.
    """
    if crews is None or len(crews) == 0:
        active_crews = [dict(c) for c in DEFAULT_CREWS]
    else:
        active_crews = [dict(c) for c in crews]

    priority_assets = []

    for asset in assets:
        # Accept vulnerability_score or final_risk_score or risk_score
        score = asset.get("vulnerability_score", asset.get("final_risk_score", asset.get("risk_score", 0.0)))
        critical_facility = asset.get("critical_facility", False)

        priority_score = float(score)
        if critical_facility and "vulnerability_score" in asset and "final_risk_score" not in asset:
            priority_score += 0.10

        priority_score = min(max(priority_score, 0.0), 1.0)

        if priority_score >= 0.75:
            priority = "CRITICAL"
            staging_window = "T+0 to T+6 hours (Immediate)"
        elif priority_score >= 0.50:
            priority = "HIGH"
            staging_window = "T+6 to T+24 hours (Pre-storm staging)"
        elif priority_score >= 0.25:
            priority = "MEDIUM"
            staging_window = "T+24 to T+48 hours (Standby)"
        else:
            priority = "LOW"
            staging_window = "Routine monitoring"

        dominant_hazard = asset.get("dominant_hazard", "wind")
        asset_id = asset.get("asset_id", "UNKNOWN")
        asset_name = asset.get("asset_name", asset.get("name", asset_id))
        is_tx = "TX" in asset_id or "transformer" in asset_name.lower()

        hub_info = _determine_staging_hub(asset_id)
        equipment = _determine_equipment_needs(dominant_hazard, critical_facility, is_tx)

        priority_assets.append({
            "asset_id": asset_id,
            "asset_name": asset_name,
            "priority_score": round(priority_score, 2),
            "priority": priority,
            "dominant_hazard": dominant_hazard,
            "critical_facility": critical_facility,
            "facility_type": asset.get("facility_type"),
            "staging_hub": hub_info["hub_name"],
            "staging_window": staging_window,
            "required_equipment": equipment,
        })

    # Sort descending by priority score
    priority_assets.sort(key=lambda a: a["priority_score"], reverse=True)

    # Assign available crews
    available_crews = [c for c in active_crews if c.get("available", False)]
    crew_assignments = []

    # Assign available crews to highest priority assets (CRITICAL and HIGH)
    for crew, asset in zip(available_crews, priority_assets):
        if asset["priority"] in ("CRITICAL", "HIGH"):
            reason = (
                f"Pre-position for {asset['dominant_hazard']} risk on {asset['asset_id']}"
                f"{' (supplies critical facility)' if asset['critical_facility'] else ''}"
            )
            crew_assignments.append({
                "crew_id": crew.get("crew_id", "CREW"),
                "crew_name": crew.get("name", crew.get("crew_id", "CREW")),
                "asset_id": asset["asset_id"],
                "asset_name": asset["asset_name"],
                "priority": asset["priority"],
                "risk_score": asset["priority_score"],
                "weather_threat": asset["dominant_hazard"],
                "staging_hub": asset["staging_hub"],
                "staging_window": asset["staging_window"],
                "required_equipment": asset["required_equipment"],
                "reason": reason,
            })

    # Summarize deployments per hub
    hub_deployments: Dict[str, int] = {}
    for assignment in crew_assignments:
        h = assignment["staging_hub"]
        hub_deployments[h] = hub_deployments.get(h, 0) + 1

    hubs_summary = []
    for hub in STAGING_HUBS:
        hubs_summary.append({
            "hub_id": hub["hub_id"],
            "name": hub["name"],
            "zone": hub["zone"],
            "deployments_needed": hub_deployments.get(hub["name"], 0),
        })

    summary = (
        f"48-hour horizon: {len(priority_assets)} assets evaluated. "
        f"{len(crew_assignments)} crew(s) pre-positioned across {len(hub_deployments)} hub(s). "
        f"{sum(1 for a in priority_assets if a['priority'] == 'CRITICAL')} critical asset(s) prioritized."
    )

    return {
        "planning_horizon_hours": forecast_hours,
        "priority_assets": priority_assets,
        "crew_assignments": crew_assignments,
        "staging_hubs": hubs_summary,
        "total_available_crews": len(available_crews),
        "summary": summary,
    }


if __name__ == "__main__":
    sample_assets = [
        {"asset_id": "TX-001", "vulnerability_score": 0.85, "critical_facility": True, "dominant_hazard": "wind"},
        {"asset_id": "TX-002", "vulnerability_score": 0.62, "critical_facility": False, "dominant_hazard": "lightning"},
        {"asset_id": "TX-003", "vulnerability_score": 0.20, "critical_facility": False, "dominant_hazard": "rainfall"},
    ]
    print(generate_crew_preposition_plan(sample_assets))