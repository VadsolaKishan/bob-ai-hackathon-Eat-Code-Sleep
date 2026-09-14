"""
Tests for asset schema validation and PostgresService logic.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.schemas.asset import AssetResponse, SensorReadingResponse


def test_asset_response_schema():
    """AssetResponse schema should serialize correctly."""
    data = {
        "id": 1,
        "asset_id": "TX-001",
        "name": "North Cascade Transformer",
        "asset_type": "transformer",
        "latitude": 37.8044,
        "longitude": -122.2712,
        "capacity": 250.0,
        "critical_facility": True,
        "facility_type": "hospital",
        "status": "active",
        "installation_date": None,
        "risk_level": "CRITICAL",
        "final_risk_score": 0.92,
    }
    schema = AssetResponse(**data)
    assert schema.asset_id == "TX-001"
    assert schema.risk_level == "CRITICAL"
    assert schema.final_risk_score == 0.92


def test_sensor_reading_schema():
    """SensorReadingResponse schema should serialize correctly."""
    data = {
        "id": 1,
        "asset_id": "TX-001",
        "timestamp": datetime.now(timezone.utc),
        "temperature": 92.4,
        "vibration": 4.8,
        "partial_discharge": 540.0,
    }
    schema = SensorReadingResponse(**data)
    assert schema.temperature == 92.4
    assert schema.vibration == 4.8


def test_asset_schema_default_risk():
    """Asset without risk data should have null risk fields."""
    data = {
        "id": 1,
        "asset_id": "FD-001",
        "name": "North Feeder",
        "asset_type": "feeder",
        "latitude": 37.82,
        "longitude": -122.28,
        "capacity": 50.0,
        "critical_facility": False,
        "status": "active",
    }
    schema = AssetResponse(**data)
    assert schema.risk_level is None
    assert schema.final_risk_score is None
