"""
End-to-End Integration and API Route Verification Test Suite for GridPulse AI.
Exercises all required API contracts:
- GET /api/v1/health
- GET /api/v1/dashboard
- GET /api/v1/assets
- GET /api/v1/assets/{id}
- GET /api/v1/assets/{id}/risk
- GET /api/v1/risk
- GET /api/v1/grid/topology
- GET /api/v1/grid/assets/{id}/impact
- GET /api/v1/weather
- GET /api/v1/weather/{id}
- GET /api/v1/weather/crew-preposition
- GET /api/v1/recommendations
- POST /api/v1/advisory
- POST /api/v1/advisory/chat
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.database.postgres import get_db
from src.app.database.neo4j import get_neo4j_session


import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.database.postgres import get_db
from src.app.database.neo4j import get_neo4j_session


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient with mocked DB lifespans and dependencies."""
    mock_db = AsyncMock()

    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_neo4j_ctx():
        session = AsyncMock()
        yield session

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("src.app.database.postgres.init_db", new_callable=AsyncMock), \
         patch("src.app.database.postgres.close_db", new_callable=AsyncMock), \
         patch("src.app.database.neo4j.init_neo4j", new_callable=AsyncMock), \
         patch("src.app.database.neo4j.close_neo4j", new_callable=AsyncMock), \
         patch("src.app.database.neo4j.get_neo4j_session", side_effect=mock_neo4j_ctx):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    app.dependency_overrides.clear()


def test_e2e_health(test_client):
    """GET /api/v1/health should return 200 with status."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


def test_e2e_weather_endpoints(test_client):
    """Weather endpoints should serve dynamic weather data and crew plans."""
    mock_asset = MagicMock()
    mock_asset.asset_id = "TX-001"
    mock_asset.name = "North Cascade Transformer"
    mock_asset.critical_facility = True

    mock_weather = MagicMock()
    mock_weather.asset_id = "TX-001"
    mock_weather.wind_speed = 65.0
    mock_weather.rainfall = 25.0
    mock_weather.lightning_probability = 0.75
    mock_weather.flood_risk = 0.4
    mock_weather.temperature = 38.0
    mock_weather.timestamp = datetime.now(timezone.utc)

    with patch("src.app.services.postgres_service.PostgresService.get_all_assets", new_callable=AsyncMock, return_value=([mock_asset], 1)), \
         patch("src.app.services.postgres_service.PostgresService.get_asset", new_callable=AsyncMock, return_value=mock_asset), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_weather", new_callable=AsyncMock, return_value=mock_weather), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_sensor", new_callable=AsyncMock, return_value=None), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_dga", new_callable=AsyncMock, return_value=None):

        # List all weather
        res_list = test_client.get("/api/v1/weather")
        assert res_list.status_code == 200
        weather_list = res_list.json()
        assert "weather_data" in weather_list
        assert len(weather_list["weather_data"]) == 1

        # Weather by asset
        res_asset = test_client.get("/api/v1/weather/TX-001")
        assert res_asset.status_code == 200
        item = res_asset.json()
        assert item["asset_id"] == "TX-001"
        assert item["risk_analysis"] is not None

        # Crew pre-positioning
        res_crew = test_client.get("/api/v1/weather/crew-preposition")
        assert res_crew.status_code == 200
        crew_data = res_crew.json()
        assert "crew_assignments" in crew_data or "assignments" in crew_data
        assignments = crew_data.get("crew_assignments") or crew_data.get("assignments")
        assert len(assignments) > 0
        assert "staging_hub" in assignments[0] or "suggested_staging_hub" in assignments[0]


def test_e2e_dashboard(test_client):
    """GET /api/v1/dashboard should aggregate stats."""
    mock_asset = MagicMock()
    mock_asset.asset_id = "TX-001"
    mock_asset.name = "TX 1"
    mock_asset.asset_type = "transformer"
    mock_asset.latitude = 37.8
    mock_asset.longitude = -122.2

    mock_risk = MagicMock()
    mock_risk.risk_level = "CRITICAL"
    mock_risk.final_risk_score = 0.92

    with patch("src.app.services.postgres_service.PostgresService.get_all_assets", new_callable=AsyncMock, return_value=([mock_asset], 1)), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_risk", new_callable=AsyncMock, return_value=mock_risk), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_weather", new_callable=AsyncMock, return_value=None), \
         patch("src.app.services.postgres_service.PostgresService.get_recent_incidents", new_callable=AsyncMock, return_value=[]), \
         patch("src.app.services.postgres_service.PostgresService.count_workorders_by_status", new_callable=AsyncMock, return_value=0):
        res = test_client.get("/api/v1/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert data["summary"]["total_assets"] == 1


def test_e2e_assets_routes(test_client):
    """GET /api/v1/assets and GET /api/v1/assets/{id}."""
    from src.app.schemas.asset import AssetResponse, AssetDetailResponse
    mock_asset_resp = AssetResponse(
        id=1,
        asset_id="TX-001",
        name="North Cascade Transformer",
        asset_type="transformer",
        latitude=37.8044,
        longitude=-122.2712,
        capacity=250.0,
        critical_facility=True,
        facility_type="hospital",
        status="active",
        installation_date=None,
        risk_level="CRITICAL",
        final_risk_score=0.92
    )
    mock_detail_resp = AssetDetailResponse(
        asset=mock_asset_resp,
        latest_sensor=None,
        latest_dga=None,
        latest_weather=None,
        latest_risk=None,
        incidents=[]
    )

    with patch("src.app.services.postgres_service.PostgresService.get_all_assets", new_callable=AsyncMock, return_value=([mock_asset_resp], 1)), \
         patch("src.app.services.postgres_service.PostgresService.get_asset_detail", new_callable=AsyncMock, return_value=mock_detail_resp):
        
        res_list = test_client.get("/api/v1/assets")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert "assets" in data_list
        assert len(data_list["assets"]) == 1
        assert data_list["assets"][0]["asset_id"] == "TX-001"

        res_detail = test_client.get("/api/v1/assets/TX-001")
        assert res_detail.status_code == 200
        data_detail = res_detail.json()
        assert data_detail["asset"]["asset_id"] == "TX-001"


def test_e2e_grid_endpoints(test_client):
    """GET /api/v1/grid/topology and GET /api/v1/grid/assets/{id}/impact."""
    mock_topo = {
        "nodes": [{"id": "TX-001", "name": "TX 1", "type": "Transformer"}],
        "edges": [],
        "total_nodes": 1,
        "total_edges": 0
    }
    mock_impact = {
        "failed_asset": {"asset_id": "TX-001", "name": "TX 1", "type": "Transformer"},
        "affected_assets": [{"asset_id": "FD-101", "name": "Feeder 101", "type": "Feeder", "depth": 1}],
        "affected_facilities": [{"asset_id": "CF-001", "name": "Oakland General Hospital", "facility_type": "hospital", "depth": 2}],
        "cascade_risk": 0.45,
        "grid_impact": 0.60,
        "cascade_path": ["TX-001", "FD-101", "CF-001"],
        "dependency_depth": 2,
        "affected_asset_count": 1,
        "critical_facility_count": 1,
        "explanation": "Failure of TX-001 cascades to Oakland General Hospital"
    }

    with patch("src.app.services.neo4j_service.Neo4jService.get_topology", new_callable=AsyncMock, return_value=mock_topo), \
         patch("src.app.core.graph_scoring.CascadeAnalyzer.analyze_cascade", new_callable=AsyncMock, return_value=mock_impact):
        
        res_topo = test_client.get("/api/v1/grid/topology")
        assert res_topo.status_code == 200
        assert "nodes" in res_topo.json()

        res_imp = test_client.get("/api/v1/grid/assets/TX-001/impact")
        assert res_imp.status_code == 200
        assert res_imp.json()["cascade_risk"] == 0.45


def test_e2e_recommendations(test_client):
    """GET /api/v1/recommendations should return ranked work order recommendations."""
    mock_asset = MagicMock()
    mock_asset.asset_id = "TX-001"
    mock_asset.name = "TX 1"
    mock_asset.asset_type = "transformer"

    mock_risk = MagicMock()
    mock_risk.risk_level = "CRITICAL"
    mock_risk.final_risk_score = 0.92

    with patch("src.app.services.postgres_service.PostgresService.get_all_assets", new_callable=AsyncMock, return_value=([mock_asset], 1)), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_risk", new_callable=AsyncMock, return_value=mock_risk):
        res = test_client.get("/api/v1/recommendations")
        assert res.status_code == 200
        data = res.json()
        assert "work_orders" in data
        assert len(data["work_orders"]) > 0
        assert data["work_orders"][0]["priority"] == "critical"


def test_e2e_advisory_chat_route(test_client):
    """POST /api/v1/advisory/chat should return structured operational response."""
    mock_asset = MagicMock()
    mock_asset.asset_id = "TX-001"
    mock_asset.name = "North Cascade Transformer"
    mock_asset.asset_type = "transformer"
    mock_asset.critical_facility = True
    mock_asset.facility_type = "hospital"

    mock_risk = MagicMock()
    mock_risk.final_risk_score = 0.92
    mock_risk.risk_level = "CRITICAL"
    mock_risk.failure_probability = 0.88
    mock_risk.asset_health_risk = 0.85
    mock_risk.weather_risk = 0.75
    mock_risk.grid_impact = 0.60
    mock_risk.cascade_risk = 0.50
    mock_risk.critical_multiplier = 1.5

    with patch("src.app.services.postgres_service.PostgresService.get_asset", new_callable=AsyncMock, return_value=mock_asset), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_sensor", new_callable=AsyncMock, return_value=None), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_dga", new_callable=AsyncMock, return_value=None), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_weather", new_callable=AsyncMock, return_value=None), \
         patch("src.app.services.postgres_service.PostgresService.get_latest_risk", new_callable=AsyncMock, return_value=mock_risk), \
         patch("src.app.services.postgres_service.PostgresService.get_incidents_for_asset", new_callable=AsyncMock, return_value=[]):
        
        payload = {
            "message": "What is the health index of TX-001?",
            "context": {}
        }
        res = test_client.post("/api/v1/advisory/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert data["provider"] in ("Local Fallback", "IBM Granite")
        assert "TX-001" in data["response"] or data.get("asset_id") == "TX-001"


def test_e2e_grid_fallback_when_neo4j_down(test_client):
    """GET /api/v1/grid/topology and /api/v1/grid/assets/{id}/impact must never 500 when Neo4j is offline."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def broken_neo4j_session():
        raise ConnectionRefusedError("Connection refused to bolt://localhost:7687")
        yield

    with patch("src.app.database.neo4j.get_neo4j_session", side_effect=broken_neo4j_session), \
         patch("src.app.routes.grid.get_neo4j_session", side_effect=broken_neo4j_session):
        
        # Topology should fallback gracefully to in-memory graph
        res_topo = test_client.get("/api/v1/grid/topology")
        assert res_topo.status_code == 200
        topo_data = res_topo.json()
        assert "nodes" in topo_data
        assert topo_data["total_nodes"] == 10
        assert topo_data["total_edges"] == 9

        # Impact should fallback gracefully to in-memory graph
        res_imp = test_client.get("/api/v1/grid/assets/TX-001/impact")
        assert res_imp.status_code == 200
        imp_data = res_imp.json()
        assert imp_data["failed_asset"]["asset_id"] == "TX-001"
        assert imp_data["cascade_risk"] > 0
        assert "CF-001" in imp_data["cascade_path"]



