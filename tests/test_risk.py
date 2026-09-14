"""
Tests for the Risk Engine — weighted formula, multipliers, classification.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.app.core.risk_engine import (
    compute_failure_probability,
    compute_weather_risk,
    classify_risk_level,
    get_critical_multiplier,
    compute_asset_health_risk,
)


def test_classify_risk_level():
    """Risk classification thresholds."""
    assert classify_risk_level(0.10) == "LOW"
    assert classify_risk_level(0.39) == "LOW"
    assert classify_risk_level(0.40) == "MEDIUM"
    assert classify_risk_level(0.69) == "MEDIUM"
    assert classify_risk_level(0.70) == "HIGH"
    assert classify_risk_level(0.84) == "HIGH"
    assert classify_risk_level(0.85) == "CRITICAL"
    assert classify_risk_level(1.00) == "CRITICAL"


def test_failure_probability_high_arcing():
    """High acetylene (arcing fault) should yield high failure probability."""
    sensor = MagicMock(temperature=92.0, vibration=5.0, partial_discharge=540.0)
    dga = MagicMock(c2h2=4.2, c2h4=68.0, h2=350.0)
    prob = compute_failure_probability(sensor, dga)
    assert prob >= 0.70, f"Expected >= 0.70, got {prob}"


def test_failure_probability_normal():
    """Normal sensor readings should yield low failure probability."""
    sensor = MagicMock(temperature=62.0, vibration=1.2, partial_discharge=90.0)
    dga = MagicMock(c2h2=0.1, c2h4=8.0, h2=20.0)
    prob = compute_failure_probability(sensor, dga)
    assert prob <= 0.25, f"Expected <= 0.25, got {prob}"


def test_failure_probability_no_data():
    """Missing sensor data should return moderate default risk."""
    prob = compute_failure_probability(None, None)
    assert 0.0 < prob <= 0.5


def test_weather_risk_severe():
    """Severe weather conditions should produce high weather risk."""
    weather = MagicMock(
        wind_speed=75.0,
        temperature=42.0,
        lightning_probability=0.85,
        rainfall=35.0,
        flood_risk=0.6
    )
    risk = compute_weather_risk(weather)
    assert risk >= 0.70, f"Expected >= 0.70, got {risk}"


def test_weather_risk_calm():
    """Calm weather should produce low weather risk."""
    weather = MagicMock(
        wind_speed=15.0,
        temperature=25.0,
        lightning_probability=0.05,
        rainfall=2.0,
        flood_risk=0.05
    )
    risk = compute_weather_risk(weather)
    assert risk <= 0.10, f"Expected <= 0.10, got {risk}"


def test_weather_risk_no_data():
    """No weather data should produce a small default risk."""
    risk = compute_weather_risk(None)
    assert 0.0 < risk <= 0.2


def test_critical_multiplier_hospital():
    """Hospital critical facility should use 1.5 multiplier."""
    asset = MagicMock(critical_facility=True, facility_type="hospital")
    assert get_critical_multiplier(asset) == 1.5


def test_critical_multiplier_normal():
    """Non-critical asset should use 1.0 multiplier."""
    asset = MagicMock(critical_facility=False, facility_type=None)
    assert get_critical_multiplier(asset) == 1.0


def test_risk_formula_critical():
    """High component scores + critical multiplier should yield CRITICAL risk."""
    base = (
        0.30 * 0.90   # failure_prob
        + 0.20 * 0.85  # asset_health
        + 0.15 * 0.65  # weather
        + 0.20 * 0.80  # grid_impact
        + 0.15 * 0.70  # cascade
    )
    final = min(base * 1.5, 1.0)
    assert classify_risk_level(final) == "CRITICAL"


def test_risk_formula_low():
    """Low component scores should yield LOW risk even without multiplier."""
    base = (
        0.30 * 0.05
        + 0.20 * 0.06
        + 0.15 * 0.03
        + 0.20 * 0.10
        + 0.15 * 0.05
    )
    final = min(base * 1.0, 1.0)
    assert classify_risk_level(final) == "LOW"


def test_asset_health_risk_clamped():
    """Asset health risk should be clamped to [0, 1]."""
    result = compute_asset_health_risk(0.95)
    assert 0.0 <= result <= 1.0
