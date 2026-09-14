"""
GridPulse AI - Weather Risk & Storm-Asset Vulnerability Module

Calculates weather-related risk for a grid asset using:
- Wind
- Rainfall
- Lightning probability
- Flood risk
- Temperature extremes
"""


def calculate_weather_risk(weather):
    """
    Calculate the overall weather risk score.

    Expected input:
        {
            "wind_speed": float,              # km/h
            "rainfall": float,                # mm/h
            "lightning_probability": float,   # 0-1
            "flood_risk": float,              # 0-1
            "temperature": float              # Celsius
        }

    Returns:
        {
            "weather_risk_score": float,
            "dominant_hazard": str
        }
    """

    # Normalize weather hazards to a 0-1 risk scale

    # Contract threshold: >70 km/h is high risk
    wind_score = min(weather["wind_speed"] / 70, 1.0)

    # Contract threshold: >30 mm/h is high risk
    rainfall_score = min(weather["rainfall"] / 30, 1.0)

    # Contract already provides this as 0-1
    lightning_score = min(max(weather["lightning_probability"], 0.0), 1.0)

    # Contract already provides this as 0-1
    flood_score = min(max(weather["flood_risk"], 0.0), 1.0)

    temperature = weather["temperature"]

    # Temperature extremes
    if temperature >= 45:
        temperature_score = 1.0
    elif temperature >= 40:
        temperature_score = 0.7
    elif temperature <= 0:
        temperature_score = 0.8
    elif temperature <= 5:
        temperature_score = 0.5
    else:
        temperature_score = 0.0

    hazards = {
        "wind": wind_score,
        "rainfall": rainfall_score,
        "lightning": lightning_score,
        "flood": flood_score,
        "temperature": temperature_score,
    }

    # Overall weather-risk weighting
    weather_risk_score = (
        wind_score * 0.25
        + rainfall_score * 0.15
        + lightning_score * 0.25
        + flood_score * 0.20
        + temperature_score * 0.15
    )

    dominant_hazard = max(
    hazards,
    key=hazards.get
)

    return {
        "weather_risk_score": round(weather_risk_score, 2),
        "dominant_hazard": dominant_hazard,
    }

def analyze_storm_asset_vulnerability(
    weather,
    health_index,
    critical_facility=False
):
    """
    Combine weather conditions and asset health
    into a storm-asset vulnerability assessment.

    Returns:
        {
            "weather_risk_score": float,
            "dominant_hazard": str,
            "health_index": float,
            "vulnerability_score": float,
            "vulnerability_level": str
        }
    """

    weather_result = calculate_weather_risk(weather)

    vulnerability_result = calculate_asset_vulnerability(
        weather_risk_score=weather_result["weather_risk_score"],
        health_index=health_index,
        critical_facility=critical_facility,
    )

    return {
        "weather_risk_score": weather_result["weather_risk_score"],
        "dominant_hazard": weather_result["dominant_hazard"],
        "health_index": health_index,
        "vulnerability_score": vulnerability_result["vulnerability_score"],
        "vulnerability_level": vulnerability_result["vulnerability_level"],
    }

if __name__ == "__main__":

    sample_weather = {
        "wind_speed": 68.5,
        "rainfall": 22.0,
        "lightning_probability": 0.75,
        "flood_risk": 0.3,
        "temperature": 38.2,
    }

    result = calculate_weather_risk(sample_weather)

    print("Weather Risk Result:")
    print(result)

def calculate_asset_vulnerability(
    weather_risk_score,
    health_index,
    critical_facility=False
):
    """
    Combine weather risk and asset degradation
    to calculate storm-asset vulnerability.

    Args:
        weather_risk_score: Weather risk score from 0 to 1.
        health_index: Asset health index from 0 to 100.
        critical_facility: Whether the asset is a critical facility.

    Returns:
        {
            "vulnerability_score": float,
            "vulnerability_level": str
        }
    """

    # Convert health index (0-100)
    # into degradation risk (0-1).
    degradation_risk = 1 - (health_index / 100)

    # Keep values within valid range.
    weather_risk_score = min(max(weather_risk_score, 0.0), 1.0)
    degradation_risk = min(max(degradation_risk, 0.0), 1.0)

    # Combine weather risk and asset degradation.
    vulnerability_score = (
        weather_risk_score * 0.6
        + degradation_risk * 0.4
    )

    # Critical facilities receive additional priority.
    if critical_facility:
        vulnerability_score += 0.1

    vulnerability_score = min(vulnerability_score, 1.0)

    # Convert score into an easy-to-understand level.
    if vulnerability_score >= 0.75:
        vulnerability_level = "CRITICAL"
    elif vulnerability_score >= 0.50:
        vulnerability_level = "HIGH"
    elif vulnerability_score >= 0.25:
        vulnerability_level = "MEDIUM"
    else:
        vulnerability_level = "LOW"

    return {
        "vulnerability_score": round(vulnerability_score, 2),
        "vulnerability_level": vulnerability_level
    }