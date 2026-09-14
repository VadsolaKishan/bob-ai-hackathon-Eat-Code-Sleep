"""
Tests for cascade scoring and graph impact calculation logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.app.core.graph_scoring import CascadeAnalyzer


@pytest.mark.asyncio
async def test_cascade_analysis_no_asset():
    """analyze_cascade should return None if asset not in graph."""
    mock_svc = MagicMock()
    mock_svc.get_asset_node = AsyncMock(return_value=None)

    analyzer = CascadeAnalyzer(mock_svc)
    result = await analyzer.analyze_cascade("NONEXISTENT-99")
    assert result is None


@pytest.mark.asyncio
async def test_cascade_analysis_no_downstream():
    """Asset with no downstream connections should have zero cascade risk."""
    mock_svc = MagicMock()
    mock_svc.get_asset_node = AsyncMock(return_value={
        "asset_id": "CF-001",
        "name": "City Hospital",
        "type": "CriticalFacility",
    })
    mock_svc.get_downstream_assets = AsyncMock(return_value=[])
    mock_svc.get_affected_facilities = AsyncMock(return_value=[])
    mock_svc.get_cascade_paths = AsyncMock(return_value=[])
    mock_svc.get_total_assets = AsyncMock(return_value=10)
    mock_svc.get_total_facilities = AsyncMock(return_value=1)
    mock_svc.calculate_graph_impact = AsyncMock(return_value=0.0)

    analyzer = CascadeAnalyzer(mock_svc)
    result = await analyzer.analyze_cascade("CF-001")

    assert result is not None
    assert result["cascade_risk"] == 0.0
    assert result["affected_asset_count"] == 0


@pytest.mark.asyncio
async def test_cascade_analysis_with_critical_facility():
    """Asset feeding a critical facility should have high cascade risk."""
    mock_svc = MagicMock()
    mock_svc.get_asset_node = AsyncMock(return_value={
        "asset_id": "TX-001",
        "name": "North Cascade Transformer",
        "type": "Transformer",
    })
    mock_svc.get_downstream_assets = AsyncMock(return_value=[
        {"asset_id": "FD-001", "name": "Feeder 1", "type": "Feeder", "depth": 1},
        {"asset_id": "CF-001", "name": "Hospital", "type": "CriticalFacility", "depth": 2},
    ])
    mock_svc.get_affected_facilities = AsyncMock(return_value=[
        {"asset_id": "CF-001", "name": "City Hospital", "facility_type": "hospital", "depth": 2}
    ])
    mock_svc.get_cascade_paths = AsyncMock(return_value=[["TX-001", "FD-001", "CF-001"]])
    mock_svc.get_total_assets = AsyncMock(return_value=10)
    mock_svc.get_total_facilities = AsyncMock(return_value=1)
    mock_svc.calculate_graph_impact = AsyncMock(return_value=0.7)

    analyzer = CascadeAnalyzer(mock_svc)
    result = await analyzer.analyze_cascade("TX-001")

    assert result is not None
    assert result["affected_asset_count"] == 2
    assert result["critical_facility_count"] == 1
    # cascade_risk formula: (2/10)*0.4 + (1/1)*0.6 = 0.08 + 0.6 = 0.68
    assert abs(result["cascade_risk"] - 0.68) < 0.01
    assert result["grid_impact"] == 0.7
    assert "TX-001" in result["cascade_path"]
    assert "Hospital" in result["explanation"] or "City Hospital" in result["explanation"]


@pytest.mark.asyncio
async def test_cascade_risk_clamped():
    """cascade_risk must never exceed 1.0."""
    mock_svc = MagicMock()
    mock_svc.get_asset_node = AsyncMock(return_value={"asset_id": "SUB-001", "name": "Substation", "type": "Substation"})
    # Massive downstream
    mock_svc.get_downstream_assets = AsyncMock(return_value=[
        {"asset_id": f"X-{i}", "name": f"Asset {i}", "type": "Feeder", "depth": 1}
        for i in range(100)
    ])
    mock_svc.get_affected_facilities = AsyncMock(return_value=[
        {"asset_id": "CF-001", "name": "Hospital", "facility_type": "hospital", "depth": 2}
    ])
    mock_svc.get_cascade_paths = AsyncMock(return_value=[])
    mock_svc.get_total_assets = AsyncMock(return_value=10)
    mock_svc.get_total_facilities = AsyncMock(return_value=1)
    mock_svc.calculate_graph_impact = AsyncMock(return_value=1.0)

    analyzer = CascadeAnalyzer(mock_svc)
    result = await analyzer.analyze_cascade("SUB-001")
    assert result["cascade_risk"] <= 1.0


@pytest.mark.asyncio
async def test_in_memory_grid_topology():
    """Verify InMemoryGridService returns complete canonical topology."""
    from src.app.services.in_memory_grid import InMemoryGridService
    svc = InMemoryGridService()
    topo = await svc.get_topology()
    assert topo["total_nodes"] == 10
    assert topo["total_edges"] == 9
    assert len(topo["nodes"]) == 10
    assert len(topo["edges"]) == 9
    node_ids = {n["id"] for n in topo["nodes"]}
    assert "TX-001" in node_ids
    assert "CF-001" in node_ids
    assert "SUB-001" in node_ids


@pytest.mark.asyncio
async def test_in_memory_grid_cascade_tx001():
    """Verify TX-001 cascade analysis through in-memory graph correctly identifies hospital."""
    from src.app.services.in_memory_grid import InMemoryGridService
    svc = InMemoryGridService()
    analyzer = CascadeAnalyzer(svc)
    res = await analyzer.analyze_cascade("TX-001")

    assert res is not None
    assert res["failed_asset"]["asset_id"] == "TX-001"
    assert res["affected_asset_count"] == 2
    assert res["critical_facility_count"] == 1
    assert res["cascade_path"] == ["TX-001", "FD-001", "CF-001"]
    assert res["cascade_risk"] == 0.68
    assert res["dependency_depth"] == 2
    assert "City General Hospital" in res["explanation"]


@pytest.mark.asyncio
async def test_in_memory_grid_cascade_leaf():
    """Verify leaf node CF-001 has zero cascade downstream."""
    from src.app.services.in_memory_grid import InMemoryGridService
    svc = InMemoryGridService()
    analyzer = CascadeAnalyzer(svc)
    res = await analyzer.analyze_cascade("CF-001")

    assert res is not None
    assert res["affected_asset_count"] == 0
    assert res["critical_facility_count"] == 0
    assert res["cascade_risk"] == 0.0

