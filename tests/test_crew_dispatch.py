from src.app.core.crew_dispatch import generate_crew_preposition_plan


def test_crew_plan_uses_48_hour_horizon():
    result = generate_crew_preposition_plan(
        assets=[],
        crews=[],
        forecast_hours=48
    )

    assert result["planning_horizon_hours"] == 48


def test_assets_are_sorted_by_priority():
    assets = [
        {
            "asset_id": "TX-LOW",
            "vulnerability_score": 0.20,
            "critical_facility": False,
            "dominant_hazard": "rainfall",
        },
        {
            "asset_id": "TX-HIGH",
            "vulnerability_score": 0.80,
            "critical_facility": False,
            "dominant_hazard": "wind",
        },
    ]

    result = generate_crew_preposition_plan(
        assets=assets,
        crews=[]
    )

    assert result["priority_assets"][0]["asset_id"] == "TX-HIGH"
    assert result["priority_assets"][1]["asset_id"] == "TX-LOW"


def test_available_crew_is_assigned_to_high_priority_asset():
    assets = [
        {
            "asset_id": "TX-001",
            "vulnerability_score": 0.80,
            "critical_facility": False,
            "dominant_hazard": "wind",
        }
    ]

    crews = [
        {
            "crew_id": "CREW-01",
            "available": True,
        }
    ]

    result = generate_crew_preposition_plan(
        assets=assets,
        crews=crews
    )

    assert len(result["crew_assignments"]) == 1
    assert result["crew_assignments"][0]["crew_id"] == "CREW-01"
    assert result["crew_assignments"][0]["asset_id"] == "TX-001"


def test_unavailable_crew_is_not_assigned():
    assets = [
        {
            "asset_id": "TX-001",
            "vulnerability_score": 0.90,
            "critical_facility": False,
            "dominant_hazard": "wind",
        }
    ]

    crews = [
        {
            "crew_id": "CREW-01",
            "available": False,
        }
    ]

    result = generate_crew_preposition_plan(
        assets=assets,
        crews=crews
    )

    assert len(result["crew_assignments"]) == 0


def test_low_priority_asset_does_not_get_crew():
    assets = [
        {
            "asset_id": "TX-001",
            "vulnerability_score": 0.20,
            "critical_facility": False,
            "dominant_hazard": "rainfall",
        }
    ]

    crews = [
        {
            "crew_id": "CREW-01",
            "available": True,
        }
    ]

    result = generate_crew_preposition_plan(
        assets=assets,
        crews=crews
    )

    assert len(result["crew_assignments"]) == 0

def test_weather_vulnerability_drives_crew_prepositioning():
    from src.app.core.weather_risk import (
        analyze_storm_asset_vulnerability
    )
    from src.app.core.crew_dispatch import (
        generate_crew_preposition_plan
    )

    weather = {
        "wind_speed": 90.0,
        "rainfall": 32.0,
        "lightning_probability": 0.90,
        "flood_risk": 0.70,
        "temperature": 42.5,
    }

    vulnerability = analyze_storm_asset_vulnerability(
        weather=weather,
        health_index=40,
        critical_facility=True,
    )

    assets = [
        {
            "asset_id": "TX-001",
            "vulnerability_score": vulnerability["vulnerability_score"],
            "critical_facility": True,
            "dominant_hazard": vulnerability["dominant_hazard"],
        }
    ]

    crews = [
        {
            "crew_id": "CREW-01",
            "available": True,
        }
    ]

    result = generate_crew_preposition_plan(
        assets,
        crews,
        forecast_hours=48,
    )

    assert result["planning_horizon_hours"] == 48
    assert result["priority_assets"][0]["asset_id"] == "TX-001"
    assert result["priority_assets"][0]["priority"] == "CRITICAL"
    assert result["crew_assignments"][0]["crew_id"] == "CREW-01"
    assert result["crew_assignments"][0]["asset_id"] == "TX-001"