"""
Tests for AI Advisory Engine — fallback logic, provider labeling, DGA classification.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.app.core.advisory import local_fallback_advisory, AdvisoryEngine
from src.app.services.integration_service import DGAAdapter, WeatherAdapter


# ─── Local Fallback Advisory ─────────────────────────────────────────────────

def test_fallback_immediate_critical():
    """Score >= 0.85 should produce IMMEDIATE urgency with correct provider."""
    result = local_fallback_advisory(risk_score=0.92, asset_name="TX-001")
    assert result["urgency"] == "IMMEDIATE"
    assert result["provider"] == "Local Fallback"
    assert len(result["recommended_actions"]) > 0
    assert len(result["potential_consequences"]) > 0


def test_fallback_urgent_high():
    """Score 0.70-0.84 should produce URGENT urgency."""
    result = local_fallback_advisory(risk_score=0.75, asset_name="TX-002")
    assert result["urgency"] == "URGENT"
    assert result["provider"] == "Local Fallback"


def test_fallback_monitor_medium():
    """Score 0.40-0.69 should produce MONITOR urgency."""
    result = local_fallback_advisory(risk_score=0.55, asset_name="TX-003")
    assert result["urgency"] == "MONITOR"
    assert result["provider"] == "Local Fallback"


def test_fallback_routine_low():
    """Score < 0.40 should produce ROUTINE urgency."""
    result = local_fallback_advisory(risk_score=0.15, asset_name="TX-004")
    assert result["urgency"] == "ROUTINE"
    assert result["provider"] == "Local Fallback"


def test_fallback_includes_dga_risk_factor():
    """High acetylene DGA should appear in risk factors."""
    dga = MagicMock(c2h2=4.5)
    sensor = MagicMock(temperature=94.0, partial_discharge=560.0)
    result = local_fallback_advisory(0.92, "TX-001", sensor=sensor, dga=dga)
    risk_text = " ".join(result["risk_factors"])
    assert "acetylene" in risk_text.lower() or "4.5" in risk_text


def test_fallback_always_has_summary():
    """Fallback response always has a non-empty summary."""
    result = local_fallback_advisory(0.50, "Some Asset")
    assert result["summary"]
    assert len(result["summary"]) > 10


# ─── DGA Adapter ─────────────────────────────────────────────────────────────

def test_dga_arcing_fault():
    """Acetylene > 3 ppm should classify as ARCING."""
    dga = MagicMock(h2=350.0, ch4=120.0, c2h2=4.2, c2h4=68.0, c2h6=22.0, co=450.0)
    result = DGAAdapter.classify_fault_type(dga)
    assert result["fault_type"] in ("ARCING", "MULTIPLE_FAULT")
    assert result["severity"] == "critical"


def test_dga_thermal_fault():
    """High ethylene with no arcing should classify as THERMAL_HIGH."""
    dga = MagicMock(h2=50.0, ch4=60.0, c2h2=0.2, c2h4=55.0, c2h6=10.0, co=200.0)
    result = DGAAdapter.classify_fault_type(dga)
    assert result["fault_type"] in ("THERMAL_HIGH", "THERMAL_LOW", "MULTIPLE_FAULT")


def test_dga_normal():
    """Low gas levels should be NORMAL."""
    dga = MagicMock(h2=10.0, ch4=8.0, c2h2=0.05, c2h4=4.0, c2h6=1.0, co=20.0)
    result = DGAAdapter.classify_fault_type(dga)
    assert result["fault_type"] == "NORMAL"
    assert result["severity"] == "low"


# ─── Weather Adapter ─────────────────────────────────────────────────────────

def test_weather_severe_risk():
    """All severe weather conditions should produce high risk score."""
    weather = MagicMock(
        wind_speed=80.0, rainfall=40.0,
        lightning_probability=0.85, flood_risk=0.7, temperature=42.0
    )
    result = WeatherAdapter.calculate_weather_risk(weather)
    assert result["weather_risk_score"] >= 0.7
    assert result["dominant_hazard"] in ("wind", "heat", "lightning", "flood")
    assert len(result["risk_factors"]) > 0


def test_weather_calm():
    """Calm conditions should produce low weather risk."""
    weather = MagicMock(
        wind_speed=10.0, rainfall=0.5,
        lightning_probability=0.02, flood_risk=0.02, temperature=22.0
    )
    result = WeatherAdapter.calculate_weather_risk(weather)
    assert result["weather_risk_score"] == 0.0


def test_weather_crew_positioning():
    """Crew positioning should return a staging plan."""
    assets = [
        {"asset_id": "TX-001", "asset_name": "Transformer 1", "risk_level": "CRITICAL", "final_risk_score": 0.92},
        {"asset_id": "TX-002", "asset_name": "Transformer 2", "risk_level": "HIGH",     "final_risk_score": 0.75},
        {"asset_id": "TX-003", "asset_name": "Transformer 3", "risk_level": "LOW",      "final_risk_score": 0.15},
    ]
    result = WeatherAdapter.generate_crew_positioning(assets)
    assert "crew_hubs" in result
    assert "deployment_schedule" in result
    assert "asset_assignments" in result
    assert result["total_assets"] == 3
    # TX-001 should be rank 1
    assert result["asset_assignments"][0]["asset_id"] == "TX-001"


# ─── AdvisoryEngine fallback (when watsonx unavailable) ──────────────────────

@pytest.mark.asyncio
async def test_advisory_engine_uses_fallback_when_no_watsonx():
    """AdvisoryEngine should use local fallback when watsonx is unavailable."""
    with patch("src.app.core.advisory.WatsonxClient.is_available", return_value=False):
        engine = AdvisoryEngine()
        asset = MagicMock(name="TX-001", asset_id="TX-001", asset_type="transformer")
        risk = MagicMock(final_risk_score=0.88, risk_level="CRITICAL")

        result = await engine.get_asset_advisory(
            asset=asset, sensor=None, dga=None,
            weather=None, risk=risk, cascade={},
            question="What should we do?"
        )

        assert result["provider"] == "Local Fallback"
        assert result["urgency"] == "IMMEDIATE"
