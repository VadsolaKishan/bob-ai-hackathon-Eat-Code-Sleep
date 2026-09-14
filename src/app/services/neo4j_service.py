"""
GridPulse AI — Neo4j Service Layer
All graph queries via Cypher for grid topology and cascade analysis.
"""
from neo4j import AsyncSession
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Total assets in system (for normalization)
TOTAL_ASSETS = 10
TOTAL_FACILITIES = 1  # critical facilities in seed data


class Neo4jService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ─── Seeding ──────────────────────────────────────────────────────────────

    async def seed_grid(self, assets: List[Dict]) -> None:
        """Create nodes and relationships from asset data."""
        # Clear existing graph
        await self.session.run("MATCH (n) DETACH DELETE n")

        for asset in assets:
            asset_type = asset.get("asset_type", "").replace("_", "").title()
            if asset_type == "Criticalfacility":
                asset_type = "CriticalFacility"

            query = f"""
            MERGE (n:{asset_type} {{asset_id: $asset_id}})
            SET n.name = $name,
                n.status = $status,
                n.capacity = $capacity,
                n.critical_facility = $critical_facility,
                n.facility_type = $facility_type,
                n.latitude = $latitude,
                n.longitude = $longitude
            """
            await self.session.run(query, **{
                "asset_id": asset["asset_id"],
                "name": asset["name"],
                "status": asset.get("status", "active"),
                "capacity": asset.get("capacity"),
                "critical_facility": asset.get("critical_facility", False),
                "facility_type": asset.get("facility_type"),
                "latitude": asset.get("latitude"),
                "longitude": asset.get("longitude"),
            })

        # Create relationships based on seed topology
        relationships = [
            # SUB-001 contains TX-001, TX-002
            ("MATCH (a:Substation {asset_id:'SUB-001'}), (b:Transformer {asset_id:'TX-001'}) MERGE (a)-[:CONTAINS]->(b)", {}),
            ("MATCH (a:Substation {asset_id:'SUB-001'}), (b:Transformer {asset_id:'TX-002'}) MERGE (a)-[:CONTAINS]->(b)", {}),
            # SUB-002 contains TX-003, TX-004
            ("MATCH (a:Substation {asset_id:'SUB-002'}), (b:Transformer {asset_id:'TX-003'}) MERGE (a)-[:CONTAINS]->(b)", {}),
            ("MATCH (a:Substation {asset_id:'SUB-002'}), (b:Transformer {asset_id:'TX-004'}) MERGE (a)-[:CONTAINS]->(b)", {}),
            # TX-003 connects to TX-004
            ("MATCH (a:Transformer {asset_id:'TX-003'}), (b:Transformer {asset_id:'TX-004'}) MERGE (a)-[:CONNECTS_TO]->(b)", {}),
            # TX-001 feeds FD-001
            ("MATCH (a:Transformer {asset_id:'TX-001'}), (b:Feeder {asset_id:'FD-001'}) MERGE (a)-[:FEEDS]->(b)", {}),
            # TX-002 feeds FD-002
            ("MATCH (a:Transformer {asset_id:'TX-002'}), (b:Feeder {asset_id:'FD-002'}) MERGE (a)-[:FEEDS]->(b)", {}),
            # TX-003 feeds FD-003
            ("MATCH (a:Transformer {asset_id:'TX-003'}), (b:Feeder {asset_id:'FD-003'}) MERGE (a)-[:FEEDS]->(b)", {}),
            # FD-001 supplies CF-001 (hospital)
            ("MATCH (a:Feeder {asset_id:'FD-001'}), (b:CriticalFacility {asset_id:'CF-001'}) MERGE (a)-[:SUPPLIES]->(b)", {}),
        ]
        for query, params in relationships:
            await self.session.run(query, **params)

        logger.info("Neo4j grid seeded successfully.")

    # ─── Topology ─────────────────────────────────────────────────────────────

    async def get_topology(self) -> Dict[str, Any]:
        """Return full graph (nodes + relationships)."""
        # Nodes
        node_result = await self.session.run(
            "MATCH (n) RETURN n, labels(n) as labels"
        )
        nodes = []
        async for record in node_result:
            node = dict(record["n"])
            node["id"] = node.get("asset_id", "")
            node["type"] = record["labels"][0] if record["labels"] else "Unknown"
            nodes.append(node)

        # Edges
        edge_result = await self.session.run(
            "MATCH (a)-[r]->(b) RETURN a.asset_id as source, b.asset_id as target, type(r) as rel_type"
        )
        edges = []
        async for record in edge_result:
            edges.append({
                "source": record["source"],
                "target": record["target"],
                "type": record["rel_type"],
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    # ─── Connectivity ──────────────────────────────────────────────────────────

    async def get_connected_assets(self, asset_id: str) -> List[Dict]:
        """Returns directly connected assets (1-hop)."""
        result = await self.session.run(
            """
            MATCH (a {asset_id: $asset_id})-[r]-(b)
            RETURN b.asset_id as asset_id, b.name as name, labels(b)[0] as type, type(r) as rel_type
            """,
            asset_id=asset_id
        )
        rows = []
        async for record in result:
            rows.append(dict(record))
        return rows

    async def get_downstream_assets(self, asset_id: str) -> List[Dict]:
        """Returns all downstream assets via BFS traversal."""
        result = await self.session.run(
            """
            MATCH (a {asset_id: $asset_id})-[*1..5]->(b)
            WHERE b.asset_id <> $asset_id
            RETURN DISTINCT b.asset_id as asset_id, b.name as name,
                   labels(b)[0] as type,
                   length(shortestPath((a)-[*]->(b))) as depth
            ORDER BY depth
            """,
            asset_id=asset_id
        )
        rows = []
        async for record in result:
            rows.append(dict(record))
        return rows

    async def get_affected_facilities(self, asset_id: str) -> List[Dict]:
        """Returns critical facilities downstream of the given asset."""
        result = await self.session.run(
            """
            MATCH (a {asset_id: $asset_id})-[*1..5]->(b:CriticalFacility)
            RETURN DISTINCT b.asset_id as asset_id, b.name as name,
                   b.facility_type as facility_type,
                   length(shortestPath((a)-[*]->(b))) as depth
            """,
            asset_id=asset_id
        )
        rows = []
        async for record in result:
            rows.append(dict(record))
        return rows

    async def get_cascade_paths(self, asset_id: str) -> List[List[str]]:
        """Returns full cascade paths with depth."""
        result = await self.session.run(
            """
            MATCH path = (a {asset_id: $asset_id})-[*1..5]->(b)
            RETURN [node IN nodes(path) | node.asset_id] as path_ids
            ORDER BY length(path) DESC
            LIMIT 10
            """,
            asset_id=asset_id
        )
        paths = []
        async for record in result:
            paths.append(record["path_ids"])
        return paths

    async def calculate_graph_impact(self, asset_id: str) -> float:
        """Returns normalized graph impact score (0-1) dynamically derived from Neo4j."""
        downstream = await self.get_downstream_assets(asset_id)
        facilities = await self.get_affected_facilities(asset_id)

        asset_count = len(downstream)
        facility_count = len(facilities)

        try:
            total_assets = await self.get_total_assets() or TOTAL_ASSETS
            total_facilities = await self.get_total_facilities() or TOTAL_FACILITIES
        except Exception:
            total_assets = TOTAL_ASSETS
            total_facilities = TOTAL_FACILITIES

        # Weighted normalized score
        asset_score = min(1.0, asset_count / max(total_assets, 1)) * 0.5
        facility_score = min(1.0, facility_count / max(total_facilities, 1)) * 0.5

        return round(asset_score + facility_score, 3)

    async def get_asset_node(self, asset_id: str) -> Optional[Dict]:
        """Returns a single node by asset_id."""
        result = await self.session.run(
            "MATCH (n {asset_id: $asset_id}) RETURN n, labels(n) as labels LIMIT 1",
            asset_id=asset_id
        )
        record = await result.single()
        if not record:
            return None
        node = dict(record["n"])
        node["type"] = record["labels"][0] if record["labels"] else "Unknown"
        return node

    async def get_total_assets(self) -> int:
        result = await self.session.run("MATCH (n) RETURN count(n) as total")
        record = await result.single()
        return record["total"] if record else 0

    async def get_total_facilities(self) -> int:
        result = await self.session.run("MATCH (n:CriticalFacility) RETURN count(n) as total")
        record = await result.single()
        return record["total"] if record else 0
