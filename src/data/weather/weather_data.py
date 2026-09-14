"""
GridPulse AI - Weather Data Loader
Loads weather sensor telemetry streams for grid equipment risk evaluation.
"""
from typing import List, Dict, Any


DEFAULT_WEATHER_DATA: List[Dict[str, Any]] = [
    {
        "asset_id": "TX-001",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 72.0,
        "rainfall": 25.0,
        "lightning_probability": 0.80,
        "flood_risk": 0.35,
        "temperature": 39.1,
    },
    {
        "asset_id": "TX-002",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 55.0,
        "rainfall": 14.0,
        "lightning_probability": 0.45,
        "flood_risk": 0.22,
        "temperature": 32.0,
    },
    {
        "asset_id": "TX-003",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 40.0,
        "rainfall": 6.0,
        "lightning_probability": 0.22,
        "flood_risk": 0.11,
        "temperature": 29.0,
    },
    {
        "asset_id": "TX-004",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 25.0,
        "rainfall": 0.0,
        "lightning_probability": 0.05,
        "flood_risk": 0.05,
        "temperature": 30.0,
    },
    {
        "asset_id": "SUB-001",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 68.0,
        "rainfall": 22.0,
        "lightning_probability": 0.72,
        "flood_risk": 0.30,
        "temperature": 37.5,
    },
    {
        "asset_id": "SUB-002",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 53.0,
        "rainfall": 12.0,
        "lightning_probability": 0.38,
        "flood_risk": 0.20,
        "temperature": 31.0,
    },
    {
        "asset_id": "FD-001",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 70.0,
        "rainfall": 24.0,
        "lightning_probability": 0.78,
        "flood_risk": 0.33,
        "temperature": 38.5,
    },
    {
        "asset_id": "FD-002",
        "timestamp": "2024-01-15T10:00:00Z",
        "wind_speed": 54.0,
        "rainfall": 13.0,
        "lightning_probability": 0.42,
        "flood_risk": 0.21,
        "temperature": 31.5,
    },
]


def load_weather_data() -> List[Dict[str, Any]]:
    """Return mock weather data stream for the 8 primary monitored grid assets."""
    return [dict(item) for item in DEFAULT_WEATHER_DATA]
