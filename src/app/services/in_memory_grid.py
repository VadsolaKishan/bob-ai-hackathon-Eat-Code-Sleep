"""
GridPulse AI — In-Memory Grid Service
Provides zero-dependency, fault-tolerant graph topology and cascade analysis
when Neo4j is offline or disconnected (e.g. cloud environments, local dev without Docker).
"""
from typing import Optional, List, Dict, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)

CANONICAL_NODES: List[Dict[str, Any]] = [
    {
        "id": "SUB-001",
        "asset_id": "SUB-001",
        "name": "North Cascade 400kV Primary Substation",
        "type": "Substation",
        "latitude": 37.8044,
        "longitude": -122.2712,
        "capacity": 400.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1833,
    },
    {
        "id": "TX-001",
        "asset_id": "TX-001",
        "name": "North Cascade Primary Transformer T-101",
        "type": "Transformer",
        "latitude": 37.8044,
        "longitude": -122.2712,
        "capacity": 250.0,
        "critical_facility": True,
        "facility_type": "hospital",
        "status": "active",
        "risk_level": "CRITICAL",
        "final_risk_score": 0.8835,
    },
    {
        "id": "TX-002",
        "asset_id": "TX-002",
        "name": "Harbor View Distribution Transformer T-202",
        "type": "Transformer",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "capacity": 180.0,
        "critical_facility": True,
        "facility_type": "water_plant",
        "status": "active",
        "risk_level": "MEDIUM",
        "final_risk_score": 0.5238,
    },
    {
        "id": "SUB-002",
        "asset_id": "SUB-002",
        "name": "Metro Harbor 220kV Distribution Substation",
        "type": "Substation",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "capacity": 220.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1518,
    },
    {
        "id": "TX-003",
        "asset_id": "TX-003",
        "name": "East Valley Industrial Transformer T-303",
        "type": "Transformer",
        "latitude": 37.6879,
        "longitude": -122.0748,
        "capacity": 150.0,
        "critical_facility": True,
        "facility_type": "airport",
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.3814,
    },
    {
        "id": "TX-004",
        "asset_id": "TX-004",
        "name": "Valley Solar Intertie Transformer T-404",
        "type": "Transformer",
        "latitude": 37.6531,
        "longitude": -122.0731,
        "capacity": 120.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1820,
    },
    {
        "id": "FD-001",
        "asset_id": "FD-001",
        "name": "North Feeder Line F-101",
        "type": "Feeder",
        "latitude": 37.8200,
        "longitude": -122.2800,
        "capacity": 50.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1893,
    },
    {
        "id": "FD-002",
        "asset_id": "FD-002",
        "name": "Harbor Distribution Feeder F-202",
        "type": "Feeder",
        "latitude": 37.7649,
        "longitude": -122.4294,
        "capacity": 40.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1548,
    },
    {
        "id": "FD-003",
        "asset_id": "FD-003",
        "name": "East Valley Feeder F-303",
        "type": "Feeder",
        "latitude": 37.6779,
        "longitude": -122.0848,
        "capacity": 35.0,
        "critical_facility": False,
        "facility_type": None,
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.1308,
    },
    {
        "id": "CF-001",
        "asset_id": "CF-001",
        "name": "City General Hospital",
        "type": "CriticalFacility",
        "latitude": 37.8150,
        "longitude": -122.2600,
        "capacity": None,
        "critical_facility": True,
        "facility_type": "hospital",
        "status": "active",
        "risk_level": "LOW",
        "final_risk_score": 0.2862,
    },
]

CANONICAL_EDGES: List[Dict[str, Any]] = [
    {"source": "SUB-001", "target": "TX-001", "type": "CONTAINS"},
    {"source": "SUB-001", "target": "TX-002", "type": "CONTAINS"},
    {"source": "SUB-002", "target": "TX-003", "type": "CONTAINS"},
    {"source": "SUB-002", "target": "TX-004", "type": "CONTAINS"},
    {"source": "TX-003", "target": "TX-004", "type": "CONNECTS_TO"},
    {"source": "TX-001", "target": "FD-001", "type": "FEEDS"},
    {"source": "TX-002", "target": "FD-002", "type": "FEEDS"},
    {"source": "TX-003", "target": "FD-003", "type": "FEEDS"},
    {"source": "FD-001", "target": "CF-001", "type": "SUPPLIES"},
]


class InMemoryGridService:
    """
    In-memory graph engine providing drop-in compatibility with Neo4jService.
    Ensures high availability and zero-downtime demo/production operation.
    """

    def __init__(self, nodes: Optional[List[Dict[str, Any]]] = None, edges: Optional[List[Dict[str, Any]]] = None):
        self._nodes = {n["id"]: dict(n) for n in (nodes or CANONICAL_NODES)}
        self._edges = [dict(e) for e in (edges or CANONICAL_EDGES)]
        
        # Build adjacency structures
        self._adj_forward: Dict[str, List[Dict[str, Any]]] = {nid: [] for nid in self._nodes}
        self._adj_undirected: Dict[str, List[Dict[str, Any]]] = {nid: [] for nid in self._nodes}

        for edge in self._edges:
            src, tgt = edge["source"], edge["target"]
            if src in self._adj_forward:
                self._adj_forward[src].append(edge)
            if src in self._adj_undirected:
                self._adj_undirected[src].append({"neighbor": tgt, "rel_type": edge["type"]})
            if tgt in self._adj_undirected:
                self._adj_undirected[tgt].append({"neighbor": src, "rel_type": edge["type"]})

    async def seed_grid(self, assets: List[Dict]) -> None:
        """No-op or in-memory update."""
        logger.info("InMemoryGridService: seed_grid called (using in-memory topology).")

    async def get_topology(self) -> Dict[str, Any]:
        """Return full graph (nodes + relationships)."""
        nodes_list = []
        for n in self._nodes.values():
            node_copy = dict(n)
            node_copy["id"] = node_copy.get("asset_id", node_copy.get("id"))
            nodes_list.append(node_copy)

        return {
            "nodes": nodes_list,
            "edges": list(self._edges),
            "total_nodes": len(nodes_list),
            "total_edges": len(self._edges),
        }

    async def get_asset_node(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Returns a single node by asset_id."""
        node = self._nodes.get(asset_id)
        if not node:
            return None
        node_copy = dict(node)
        node_copy["id"] = node_copy.get("asset_id", node_copy.get("id"))
        return node_copy

    async def get_connected_assets(self, asset_id: str) -> List[Dict[str, Any]]:
        """Returns directly connected assets (1-hop undirected)."""
        neighbors = self._adj_undirected.get(asset_id, [])
        result = []
        for item in neighbors:
            nid = item["neighbor"]
            node = self._nodes.get(nid)
            if node:
                result.append({
                    "asset_id": nid,
                    "name": node.get("name", nid),
                    "type": node.get("type", "Unknown"),
                    "rel_type": item["rel_type"],
                })
        return result

    async def get_downstream_assets(self, asset_id: str) -> List[Dict[str, Any]]:
        """Returns all downstream assets via BFS traversal with depth."""
        if asset_id not in self._nodes:
            return []

        visited = {asset_id}
        queue = deque([(asset_id, 0)])
        downstream = []

        while queue:
            curr_id, depth = queue.popleft()
            for edge in self._adj_forward.get(curr_id, []):
                tgt = edge["target"]
                if tgt not in visited:
                    visited.add(tgt)
                    node = self._nodes.get(tgt, {})
                    downstream.append({
                        "asset_id": tgt,
                        "name": node.get("name", tgt),
                        "type": node.get("type", "Unknown"),
                        "depth": depth + 1,
                    })
                    queue.append((tgt, depth + 1))

        return downstream

    async def get_affected_facilities(self, asset_id: str) -> List[Dict[str, Any]]:
        """Returns critical facilities downstream of the given asset."""
        downstream = await self.get_downstream_assets(asset_id)
        facilities = []
        for item in downstream:
            node = self._nodes.get(item["asset_id"], {})
            if node.get("type") == "CriticalFacility":
                facilities.append({
                    "asset_id": item["asset_id"],
                    "name": node.get("name", item["asset_id"]),
                    "facility_type": node.get("facility_type"),
                    "depth": item["depth"],
                })
        return facilities

    async def get_cascade_paths(self, asset_id: str) -> List[List[str]]:
        """Returns cascade paths from the given asset to downstream leaves."""
        if asset_id not in self._nodes:
            return []

        paths: List[List[str]] = []

        def dfs(curr: str, current_path: List[str]):
            children = [e["target"] for e in self._adj_forward.get(curr, [])]
            if not children:
                if len(current_path) > 1:
                    paths.append(list(current_path))
                return
            for child in children:
                if child not in current_path:  # Prevent cycles
                    dfs(child, current_path + [child])

        dfs(asset_id, [asset_id])

        if not paths:
            paths = [[asset_id]]

        paths.sort(key=len, reverse=True)
        return paths[:10]

    async def get_total_assets(self) -> int:
        return len(self._nodes)

    async def get_total_facilities(self) -> int:
        return sum(
            1 for n in self._nodes.values()
            if n.get("type") == "CriticalFacility"
        )

    async def calculate_graph_impact(self, asset_id: str) -> float:
        """Returns normalized graph impact score (0-1)."""
        downstream = await self.get_downstream_assets(asset_id)
        facilities = await self.get_affected_facilities(asset_id)

        asset_count = len(downstream)
        facility_count = len(facilities)

        total_assets = await self.get_total_assets() or 10
        total_facilities = await self.get_total_facilities() or 1

        asset_score = min(1.0, asset_count / max(total_assets, 1)) * 0.5
        facility_score = min(1.0, facility_count / max(total_facilities, 1)) * 0.5

        return round(asset_score + facility_score, 3)
