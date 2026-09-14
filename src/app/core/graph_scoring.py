"""
GridPulse AI — Cascading Failure Engine
Analyzes grid cascade failure impact using Neo4j graph data.
"""
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CascadeAnalyzer:
    """
    Analyzes cascading failure impact when an asset fails.
    Uses Neo4j graph queries to traverse downstream topology.
    """

    def __init__(self, neo4j_svc):
        self.neo4j_svc = neo4j_svc

    async def analyze_cascade(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Performs full cascade analysis for a given asset.

        Returns:
        - failed_asset: the failing asset info
        - affected_assets: downstream assets with depth
        - affected_facilities: critical facilities impacted
        - cascade_risk: normalized 0-1 score
        - grid_impact: normalized 0-1 score
        - cascade_path: list of asset IDs in cascade path
        - dependency_depth: maximum cascade depth
        - affected_asset_count / critical_facility_count
        - explanation text
        """
        # Get the asset node
        asset_node = await self.neo4j_svc.get_asset_node(asset_id)
        if not asset_node:
            return None

        # Get downstream affected assets
        downstream = await self.neo4j_svc.get_downstream_assets(asset_id)

        # Get affected critical facilities
        facilities = await self.neo4j_svc.get_affected_facilities(asset_id)

        # Get cascade paths
        paths = await self.neo4j_svc.get_cascade_paths(asset_id)

        # Get total counts for normalization
        total_assets = await self.neo4j_svc.get_total_assets()
        total_facilities = await self.neo4j_svc.get_total_facilities()

        affected_count = len(downstream)
        facility_count = len(facilities)
        max_depth = max((a.get("depth", 0) for a in downstream), default=0)

        # cascade_risk formula
        cascade_risk = min(1.0,
            (affected_count / max(total_assets, 1)) * 0.4 +
            (facility_count / max(total_facilities, 1)) * 0.6
        )
        cascade_risk = round(cascade_risk, 3)

        # grid_impact
        grid_impact = await self.neo4j_svc.calculate_graph_impact(asset_id)

        # Primary cascade path (longest)
        primary_path = paths[0] if paths else [asset_id]

        # Build explanation
        facility_names = [f["name"] for f in facilities]
        if facility_count > 0:
            facility_text = f"reaching {facility_count} critical facilit{'y' if facility_count == 1 else 'ies'} ({', '.join(facility_names[:3])})"
        else:
            facility_text = "with no critical facilities directly impacted"
        explanation = (
            f"Failure of {asset_node.get('name', asset_id)} would cascade through "
            f"{affected_count} downstream asset{'s' if affected_count != 1 else ''} "
            f"to a depth of {max_depth}, {facility_text}. "
            f"Cascade risk score: {cascade_risk:.2f}, Grid impact: {grid_impact:.2f}."
        )

        return {
            "failed_asset": {
                "asset_id": asset_id,
                "name": asset_node.get("name", asset_id),
                "type": asset_node.get("type", "Unknown"),
            },
            "affected_assets": [
                {
                    "asset_id": a["asset_id"],
                    "name": a.get("name", a["asset_id"]),
                    "type": a.get("type", "Unknown"),
                    "depth": a.get("depth", 1),
                }
                for a in downstream
            ],
            "affected_facilities": [
                {
                    "asset_id": f["asset_id"],
                    "name": f.get("name", f["asset_id"]),
                    "facility_type": f.get("facility_type"),
                    "depth": f.get("depth", 1),
                }
                for f in facilities
            ],
            "cascade_risk": cascade_risk,
            "grid_impact": grid_impact,
            "cascade_path": primary_path,
            "dependency_depth": max_depth,
            "affected_asset_count": affected_count,
            "critical_facility_count": facility_count,
            "explanation": explanation,
        }
