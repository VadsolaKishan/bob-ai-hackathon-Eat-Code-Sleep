from src.app.core.weather_risk import (
    calculate_weather_risk,
    calculate_asset_vulnerability,
    analyze_storm_asset_vulnerability,
)


def test_high_lightning_risk():
    weather = {
        "wind_speed": 20,
        "rainfall": 10,
        "lightning_probability": 0.9,
        "flood_risk": 0.1,
        "temperature": 30,
    }

    result = calculate_weather_risk(weather)

    assert result["dominant_hazard"] == "lightning"


def test_high_wind_risk():
    weather = {
        "wind_speed": 100,
        "rainfall": 20,
        "lightning_probability": 0.1,
        "flood_risk": 0.1,
        "temperature": 30,
    }

    result = calculate_weather_risk(weather)

    assert result["dominant_hazard"] == "wind"


def test_high_temperature_risk():
    weather = {
        "wind_speed": 10,
        "rainfall": 10,
        "lightning_probability": 0.1,
        "flood_risk": 0.1,
        "temperature": 45,
    }

    result = calculate_weather_risk(weather)

    assert result["dominant_hazard"] == "temperature"


def test_low_weather_risk():
    weather = {
        "wind_speed": 10,
        "rainfall": 5,
        "lightning_probability": 0.05,
        "flood_risk": 0.05,
        "temperature": 30,
    }

    result = calculate_weather_risk(weather)

    assert result["weather_risk_score"] < 0.2

def test_high_vulnerability_for_degraded_asset():
    result = calculate_asset_vulnerability(
        weather_risk_score=0.8,
        health_index=30,
        critical_facility=False
    )

    assert result["vulnerability_score"] >= 0.6
    assert result["vulnerability_level"] in ["HIGH", "CRITICAL"]


def test_low_vulnerability_for_healthy_asset():
    result = calculate_asset_vulnerability(
        weather_risk_score=0.1,
        health_index=90,
        critical_facility=False
    )

    assert result["vulnerability_score"] < 0.25
    assert result["vulnerability_level"] == "LOW"


def test_critical_facility_gets_higher_vulnerability():
    normal_asset = calculate_asset_vulnerability(
        weather_risk_score=0.6,
        health_index=70,
        critical_facility=False
    )

    critical_asset = calculate_asset_vulnerability(
        weather_risk_score=0.6,
        health_index=70,
        critical_facility=True
    )

    assert critical_asset["vulnerability_score"] > normal_asset["vulnerability_score"]

def test_storm_asset_vulnerability():
    weather = {
        "wind_speed": 90.0,
        "rainfall": 32.0,
        "lightning_probability": 0.90,
        "flood_risk": 0.70,
        "temperature": 42.5,
    }

    result = analyze_storm_asset_vulnerability(
        weather=weather,
        health_index=40,
        critical_facility=True,
    )

    assert result["weather_risk_score"] > 0.7
    assert result["health_index"] == 40
    assert result["vulnerability_score"] > 0.7
    assert result["vulnerability_level"] == "CRITICAL"