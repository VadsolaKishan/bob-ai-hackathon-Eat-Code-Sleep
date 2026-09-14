"""
GridPulse AI — Chatbot, Intent Detection, Entity Resolution & Local Fallback Tests
Tests all Phase 15 required questions, intent routing, asset resolution, and fallback quality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.app.core.chat_intent import (
    ChatIntent,
    detect_chat_intent,
    resolve_asset_ids,
)
from src.app.core.chat_context import ChatContextBuilder
from src.app.core.advisory import AdvisoryEngine
from src.app.core.risk_engine import compute_failure_probability


# ─── 1. Asset Entity Resolution Tests ────────────────────────────────────────

def test_asset_resolution_exact_id():
    ids = resolve_asset_ids("What is the status of TX-001?")
    assert ids == ["TX-001"]


def test_asset_resolution_case_insensitive_and_compact():
    ids1 = resolve_asset_ids("tell me about tx-001")
    assert ids1 == ["TX-001"]

    ids2 = resolve_asset_ids("check tx001 immediately")
    assert ids2 == ["TX-001"]


def test_asset_resolution_aliases():
    ids = resolve_asset_ids("What is the condition of T-101?")
    assert ids == ["TX-001"]

    ids2 = resolve_asset_ids("Inspect feeder F-101")
    assert ids2 == ["FD-001"]


def test_asset_resolution_names():
    ids = resolve_asset_ids("What is the condition of North Cascade Primary Transformer?")
    assert "TX-001" in ids

    ids2 = resolve_asset_ids("Tell me about the primary transformer in North Cascade.")
    assert "TX-001" in ids2

    ids3 = resolve_asset_ids("Is City General Hospital at risk?")
    assert "CF-001" in ids3


def test_asset_resolution_multiple():
    ids = resolve_asset_ids("Compare TX-001 and TX-004.")
    assert "TX-001" in ids
    assert "TX-004" in ids
    assert len(ids) == 2


# ─── 2. Intent Detection Tests ───────────────────────────────────────────────

def test_intent_top_risk():
    intent = detect_chat_intent("Which asset has the highest risk?", [])
    assert intent == ChatIntent.TOP_RISK_ASSETS

    intent2 = detect_chat_intent("What asset should we inspect first?", [])
    assert intent2 == ChatIntent.TOP_RISK_ASSETS


def test_intent_asset_health():
    intent = detect_chat_intent("What is the health index of TX-001?", ["TX-001"])
    assert intent == ChatIntent.ASSET_HEALTH


def test_intent_dga():
    intent = detect_chat_intent("What does the DGA indicate for TX-001?", ["TX-001"])
    assert intent == ChatIntent.DGA_ANALYSIS


def test_intent_weather():
    intent = detect_chat_intent("How is the current weather affecting TX-001?", ["TX-001"])
    assert intent == ChatIntent.WEATHER_RISK

    intent2 = detect_chat_intent("Which transformer is most vulnerable to the storm?", [])
    assert intent2 == ChatIntent.WEATHER_RISK


def test_intent_cascade():
    intent = detect_chat_intent("What happens if TX-001 fails?", ["TX-001"])
    assert intent == ChatIntent.CASCADE_IMPACT


def test_intent_critical_facility():
    intent = detect_chat_intent("Which critical facilities are affected if TX-001 fails?", ["TX-001"])
    assert intent in (ChatIntent.CRITICAL_FACILITY, ChatIntent.CASCADE_IMPACT)


def test_intent_crew_dispatch():
    intent = detect_chat_intent("Where should crews be positioned for the next 48 hours?", [])
    assert intent == ChatIntent.CREW_DISPATCH


def test_intent_compare():
    intent = detect_chat_intent("Compare TX-001 and TX-004.", ["TX-001", "TX-004"])
    assert intent == ChatIntent.COMPARE_ASSETS

    intent2 = detect_chat_intent("Why is TX-001 prioritized over TX-004?", ["TX-001", "TX-004"])
    assert intent2 == ChatIntent.COMPARE_ASSETS


def test_intent_lightning():
    intent = detect_chat_intent("Which assets are affected by lightning?", [])
    assert intent == ChatIntent.LIGHTNING_ASSETS


def test_intent_dga_warning():
    intent = detect_chat_intent("Which assets have DGA warning signs?", [])
    assert intent == ChatIntent.DGA_WARNING_ASSETS


def test_intent_compound_risk():
    intent = detect_chat_intent("Which assets have both poor health and severe weather exposure?", [])
    assert intent == ChatIntent.COMPOUND_RISK


# ─── 3. Local Chat Fallback Authoritative Output Tests ───────────────────────

@pytest.fixture
def mock_context_data():
    """Builds representative context data matching live PostgreSQL & Neo4j schema."""
    return {
        "intent": "RISK_ANALYSIS",
        "queried_assets": ["TX-001"],
        "user_question": "Why is TX-001 high risk?",
        "primary_asset": {
            "asset_id": "TX-001",
            "name": "North Cascade Primary Transformer T-101",
            "found": True,
            "critical_facility": True,
            "facility_type": "hospital",
            "health": {
                "health_index": 51.9,
                "health_band": "WARNING",
                "dominant_risk": "vibration",
                "dga_fault_type": "ARCING",
                "dga_severity": "CRITICAL",
                "explanation": "Acetylene spike indicates active arcing fault.",
                "recommended_action": "Immediate inspection and degassing.",
            },
            "weather": {
                "wind_speed": 72.0,
                "temperature": 39.1,
                "lightning_probability": 0.80,
                "flood_risk": 0.35,
                "weather_risk_score": 0.68,
                "dominant_hazard": "wind",
            },
            "risk": {
                "final_risk_score": 0.92,
                "risk_level": "CRITICAL",
                "failure_probability": 0.82,
                "asset_health_risk": 0.48,
                "weather_risk": 0.68,
                "grid_impact": 0.90,
                "cascade_risk": 0.70,
                "critical_multiplier": 1.5,
            },
            "cascade": {
                "affected_asset_count": 2,
                "critical_facility_count": 1,
                "cascade_path": ["TX-001", "FD-001", "CF-001"],
                "affected_facilities": [{"asset_id": "CF-001", "name": "City General Hospital Complex"}],
                "explanation": "Cascades through FD-001 to City General Hospital.",
            },
            "incidents": [
                {"failure_type": "arcing", "severity": "critical", "description": "Acetylene spike detected at 3.8 ppm"}
            ],
            "crew": {
                "staging_hub": "North Operations Center",
                "required_equipment": "Mobile Transformer Backup Unit & Oil Degassing System",
            },
        },
        "ranked_assets": [
            {
                "asset_id": "TX-001",
                "name": "North Cascade Primary Transformer T-101",
                "final_risk_score": 0.92,
                "risk_level": "CRITICAL",
                "dominant_hazard": "wind",
                "critical_facility": True,
                "facility_type": "hospital",
            },
            {
                "asset_id": "TX-002",
                "name": "Harbor View Distribution Transformer",
                "final_risk_score": 0.75,
                "risk_level": "HIGH",
                "dominant_hazard": "wind",
                "critical_facility": True,
                "facility_type": "water_plant",
            },
            {
                "asset_id": "TX-004",
                "name": "Valley Solar Intertie Transformer",
                "final_risk_score": 0.15,
                "risk_level": "LOW",
                "dominant_hazard": "none",
                "critical_facility": False,
            },
        ],
        "top_asset": {
            "asset_id": "TX-001",
            "name": "North Cascade Primary Transformer T-101",
            "final_risk_score": 0.92,
            "risk_level": "CRITICAL",
            "dominant_hazard": "wind",
            "critical_facility": True,
            "facility_type": "hospital",
        },
        "crew_plan": {
            "crew_assignments": [
                {
                    "crew_id": "CREW-01",
                    "crew_name": "Rapid Response High-Voltage Alpha",
                    "asset_id": "TX-001",
                    "asset_name": "North Cascade Primary Transformer T-101",
                    "priority": "CRITICAL",
                    "staging_hub": "North Operations Center",
                    "staging_window": "T+0 to T+6 hours (Immediate)",
                    "required_equipment": "Mobile Transformer Backup Unit",
                }
            ]
        },
    }


@pytest.mark.asyncio
async def test_chat_top_risk(mock_context_data):
    """Answers 'What asset should we inspect first?' with real data."""
    mock_context_data["intent"] = "TOP_RISK_ASSETS"
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("What asset should we inspect first?", mock_context_data)
        assert provider == "Local Fallback"
        assert "TX-001" in result["response"]
        assert "CRITICAL" in result["response"]
        assert result["risk_score"] == 0.92


@pytest.mark.asyncio
async def test_chat_risk_explanation(mock_context_data):
    """Answers 'Why is TX-001 high risk?' with concrete factors."""
    mock_context_data["intent"] = "RISK_ANALYSIS"
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("Why is TX-001 high risk?", mock_context_data)
        assert provider == "Local Fallback"
        text = result["response"]
        assert "TX-001" in text
        assert "BOTTOM LINE:" in text
        assert "WHY:" in text
        assert "ACTION:" in text
        assert "0.92" in text or "CRITICAL" in text


@pytest.mark.asyncio
async def test_chat_dga_query(mock_context_data):
    """Answers 'What does the DGA indicate for TX-001?'."""
    mock_context_data["intent"] = "DGA_ANALYSIS"
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("What does the DGA indicate for TX-001?", mock_context_data)
        text = result["response"]
        assert "ARCING" in text
        assert "C2H2" in text or "Acetylene" in text


@pytest.mark.asyncio
async def test_chat_cascade_query(mock_context_data):
    """Answers 'What happens if TX-001 fails?'."""
    mock_context_data["intent"] = "CASCADE_IMPACT"
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("What happens if TX-001 fails?", mock_context_data)
        text = result["response"]
        assert "FD-001" in text or "City General Hospital" in text
        assert "cascade" in text.lower()


@pytest.mark.asyncio
async def test_chat_crew_dispatch_query(mock_context_data):
    """Answers 'Where should crews be positioned for the next 48 hours?'."""
    mock_context_data["intent"] = "CREW_DISPATCH"
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("Where should crews be positioned for the next 48 hours?", mock_context_data)
        text = result["response"]
        assert "CREW-01" in text
        assert "North Operations Center" in text


@pytest.mark.asyncio
async def test_chat_asset_comparison():
    """Answers 'Compare TX-001 and TX-004.' with differential analysis."""
    context = {
        "intent": "COMPARE_ASSETS",
        "comparison": [
            {
                "asset_id": "TX-001",
                "name": "North Cascade Primary Transformer",
                "facility_type": "hospital",
                "risk": {"final_risk_score": 0.92, "risk_level": "CRITICAL", "critical_multiplier": 1.5, "weather_risk": 0.68},
                "health": {"health_index": 51.9, "dga_fault_type": "ARCING"},
            },
            {
                "asset_id": "TX-004",
                "name": "Valley Solar Intertie Transformer",
                "facility_type": None,
                "risk": {"final_risk_score": 0.15, "risk_level": "LOW", "critical_multiplier": 1.0, "weather_risk": 0.05},
                "health": {"health_index": 98.0, "dga_fault_type": "NORMAL"},
            }
        ]
    }
    engine = AdvisoryEngine()

    with patch.object(engine.watsonx, "is_available", return_value=False):
        result, provider = await engine.chat("Compare TX-001 and TX-004.", context)
        text = result["response"]
        assert "TX-001" in text
        assert "TX-004" in text
        assert "prioritized over" in text.lower() or "0.92" in text


@pytest.mark.asyncio
async def test_chat_watsonx_active():
    """When Watsonx is available, provider is 'IBM Granite'."""
    engine = AdvisoryEngine()
    fake_granite_resp = (
        "BOTTOM LINE: TX-001 is in critical condition.\n"
        "WHY: - Elevated arcing fault detected in DGA.\n"
        "ACTION: 1. Deploy inspection crew.\nURGENCY: CRITICAL"
    )

    with patch.object(engine.watsonx, "is_available", return_value=True), \
         patch.object(engine.watsonx, "generate", return_value=fake_granite_resp):
        result, provider = await engine.chat("Status of TX-001", {"primary_asset": {"asset_id": "TX-001"}})
        assert provider == "IBM Granite"
        assert "TX-001" in result["response"]


def test_dga_affects_final_risk():
    """Proves DGA classification affects failure probability and final risk."""
    normal_dga = MagicMock(c2h2=0.1, c2h4=5.0, h2=15.0, ch4=10.0, c2h6=2.0, co=30.0, co2=400.0)
    arcing_dga = MagicMock(c2h2=4.5, c2h4=68.0, h2=350.0, ch4=120.0, c2h6=22.0, co=450.0, co2=3200.0)
    sensor = MagicMock(temperature=75.0, vibration=2.0, partial_discharge=180.0)

    prob_normal = compute_failure_probability(sensor, normal_dga)
    prob_arcing = compute_failure_probability(sensor, arcing_dga)

    assert prob_arcing > prob_normal, f"Expected arcing ({prob_arcing}) > normal ({prob_normal})"
    assert prob_arcing >= 0.70


def test_unknown_asset_intent_resolution():
    """Verifies that non-existent / arbitrary asset queries are resolved as UNKNOWN_ASSET."""
    from src.app.core.chat_intent import resolve_asset_ids, detect_chat_intent, ChatIntent

    resolved = resolve_asset_ids("give detqails of dd-2")
    assert "DD-2" in resolved
    intent = detect_chat_intent("give detqails of dd-2", resolved)
    assert intent == ChatIntent.UNKNOWN_ASSET

    resolved_xyz = resolve_asset_ids("what is the status of asset XYZ-99")
    assert "XYZ-99" in resolved_xyz
    intent_xyz = detect_chat_intent("what is the status of asset XYZ-99", resolved_xyz)
    assert intent_xyz == ChatIntent.UNKNOWN_ASSET


@pytest.mark.asyncio
async def test_unknown_asset_advisory_response():
    """Verifies that unknown asset returns structured not-found response with None risk score/level."""
    from src.app.core.chat_intent import ChatIntent
    engine = AdvisoryEngine()

    context = {
        "intent": ChatIntent.UNKNOWN_ASSET.value,
        "unknown_asset_id": "DD-2",
        "primary_asset": {"asset_id": "DD-2", "found": False}
    }

    result, provider = await engine.chat("give detqails of dd-2", context)
    assert "DD-2" in result["response"]
    assert "not found in the GridPulse AI active network registry" in result["response"]
    assert result["risk_level"] is None
    assert result["risk_score"] is None
    assert result["asset_id"] is None
    assert "TX-001" in result["response"]


def test_intent_new_prompts():
    """Verifies that all standard prompt suggestions route to distinct correct intents."""
    # 1. Immediate inspection
    assert detect_chat_intent("Which asset needs immediate inspection?", []) == ChatIntent.TOP_RISK_ASSETS

    # 2. Weather risk
    assert detect_chat_intent("How does current weather affect risk?", []) == ChatIntent.WEATHER_RISK

    # 3. Critical facilities
    assert detect_chat_intent("Which critical facilities are at risk?", []) == ChatIntent.CRITICAL_FACILITY

    # 4. Maintenance team
    assert detect_chat_intent("What should the maintenance team do today?", []) == ChatIntent.MAINTENANCE
    assert detect_chat_intent("Give me maintenance suggestions", []) == ChatIntent.MAINTENANCE

    # 5. Cascade risk
    assert detect_chat_intent("What is the cascade risk for this asset?", []) == ChatIntent.CASCADE_IMPACT

    # 6. Greeting / Help
    assert detect_chat_intent("Hello", []) == ChatIntent.GREETING
    assert detect_chat_intent("What can you do?", []) == ChatIntent.GREETING


@pytest.mark.asyncio
async def test_advisory_distinct_responses():
    """Verifies that each query type produces distinct, authoritative control-room advice."""
    engine = AdvisoryEngine()

    mock_top = {
        "asset_id": "TX-001",
        "name": "North Cascade Primary Transformer T-101",
        "final_risk_score": 1.00,
        "risk_level": "CRITICAL",
        "health_index": 48.5,
    }

    # 1. Greeting response
    ctx_greet = {"intent": ChatIntent.GREETING.value}
    res_greet, _ = await engine.chat("hello", ctx_greet)
    assert "GridPulse AI" in res_greet["response"]
    assert "intelligent power grid operational advisor" in res_greet["response"]

    # 2. Maintenance response
    ctx_maint = {
        "intent": ChatIntent.MAINTENANCE.value,
        "top_asset": mock_top,
        "work_orders": [{"id": 1, "asset_id": "TX-001", "title": "Oil degassing", "priority": "CRITICAL", "status": "pending"}]
    }
    res_maint, _ = await engine.chat("What should the maintenance team do today?", ctx_maint)
    assert "maintenance team must immediately prioritize" in res_maint["response"]
    assert "TX-001" in res_maint["response"]

    # 3. Weather grid-wide response
    ctx_weather = {
        "intent": ChatIntent.WEATHER_RISK.value,
        "weather_overview": {
            "high_risk_weather_assets": [mock_top],
            "lightning_alert_assets": [mock_top],
        }
    }
    res_weather, _ = await engine.chat("How does current weather affect risk?", ctx_weather)
    assert "ELEVATED RISK" in res_weather["response"]
    assert "across the grid corridor" in res_weather["response"]

    # 4. Critical facilities response
    ctx_cf = {
        "intent": ChatIntent.CRITICAL_FACILITY.value,
        "top_asset": mock_top,
    }
    res_cf, _ = await engine.chat("Which critical facilities are at risk?", ctx_cf)
    assert "City General Hospital Complex" in res_cf["response"]
    assert "CF-001" in res_cf["response"]


