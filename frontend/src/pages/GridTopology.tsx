import React, { useEffect, useState } from 'react';
import { getGridTopology, getCascadeImpact } from '../services/api';
import type { GridTopology, GridNode, GridEdge, CascadeImpact } from '../types';
import RiskBadge from '../components/RiskBadge';

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#10b981',
  undefined: '#3b82f6',
};

const TYPE_ICONS: Record<string, string> = {
  Substation: '⚡',
  Transformer: '🔄',
  Feeder: '〰',
  CriticalFacility: '🏥',
};

// Canonical schematic positions designed for transmission -> distribution hierarchy
const SCHEMATIC_COORDS: Record<string, { x: number; y: number; sub: string }> = {
  // Substations (Col 1)
  'SUB-001': { x: 105, y: 140, sub: 'North 400kV Sub' },
  'SUB-002': { x: 105, y: 380, sub: 'Harbor 220kV Sub' },

  // Transformers (Col 2)
  'TX-001': { x: 310, y: 90, sub: 'Primary T-101' },
  'TX-002': { x: 310, y: 200, sub: 'Harbor T-202' },
  'TX-003': { x: 310, y: 330, sub: 'Industrial T-303' },
  'TX-004': { x: 310, y: 440, sub: 'Solar T-404' },

  // Feeders (Col 3)
  'FD-001': { x: 550, y: 90, sub: 'North Feeder F-101' },
  'FD-002': { x: 550, y: 200, sub: 'Harbor Feeder F-202' },
  'FD-003': { x: 550, y: 330, sub: 'Valley Feeder F-303' },

  // Critical Facilities (Col 4)
  'CF-001': { x: 750, y: 90, sub: 'City Hospital ✚' },
};

function getShortSub(node: GridNode): string {
  if (SCHEMATIC_COORDS[node.id]?.sub) {
    return SCHEMATIC_COORDS[node.id].sub;
  }
  if (node.critical_facility) return 'Critical Facility ✚';
  if (node.type === 'Transformer') return `TX (${node.capacity ?? ''} MVA)`;
  if (node.type === 'Substation') return `Substation (${node.capacity ?? ''} kV)`;
  if (node.type === 'Feeder') return 'Feeder Line';
  return node.type;
}

function computeLayout(
  nodes: GridNode[],
  width: number,
  height: number,
  mode: 'schematic' | 'geographic'
): Record<string, { x: number; y: number }> {
  if (nodes.length === 0) return {};

  if (mode === 'schematic') {
    const pos: Record<string, { x: number; y: number }> = {};
    let unmappedIdx = 0;
    nodes.forEach(n => {
      if (SCHEMATIC_COORDS[n.id]) {
        pos[n.id] = { ...SCHEMATIC_COORDS[n.id] };
      } else {
        // Fallback for any unknown nodes: distribute along right side
        pos[n.id] = {
          x: width - 100,
          y: 70 + unmappedIdx * 70
        };
        unmappedIdx++;
      }
    });
    return pos;
  }

  // Geographic Mode with Force-Collision Repulsion
  const lats = nodes.map(n => n.latitude ?? 0).filter(Boolean);
  const lons = nodes.map(n => n.longitude ?? 0).filter(Boolean);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const padX = 80, padY = 70;
  const pos: Record<string, { x: number; y: number }> = {};

  nodes.forEach(n => {
    const latRange = maxLat - minLat || 0.01;
    const lonRange = maxLon - minLon || 0.01;
    const x = padX + (((n.longitude ?? minLon) - minLon) / lonRange) * (width - 2 * padX);
    const y = padY + (1 - ((n.latitude ?? minLat) - minLat) / latRange) * (height - 2 * padY);
    pos[n.id] = { x, y };
  });

  // Relaxation pass: push apart overlapping or near-identical coordinates
  const nodeIds = Object.keys(pos);
  const minDist = 80;
  for (let iter = 0; iter < 60; iter++) {
    let shifted = false;
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const id1 = nodeIds[i];
        const id2 = nodeIds[j];
        const p1 = pos[id1];
        const p2 = pos[id2];
        let dx = p2.x - p1.x;
        let dy = p2.y - p1.y;
        let dist = Math.hypot(dx, dy);

        if (dist < 1) {
          // Exactly identical coordinates (e.g. SUB-001 & TX-001)
          dx = (i % 2 === 0 ? 1 : -1) * 35;
          dy = (j % 2 === 0 ? 1 : -1) * 35;
          dist = Math.hypot(dx, dy);
        }

        if (dist < minDist) {
          shifted = true;
          const overlap = (minDist - dist) / 2;
          const nx = dx / dist;
          const ny = dy / dist;
          p1.x -= nx * overlap;
          p1.y -= ny * overlap;
          p2.x += nx * overlap;
          p2.y += ny * overlap;

          // Clamping inside canvas boundaries
          p1.x = Math.max(padX / 2, Math.min(width - padX / 2, p1.x));
          p1.y = Math.max(padY / 2, Math.min(height - padY / 2, p1.y));
          p2.x = Math.max(padX / 2, Math.min(width - padX / 2, p2.x));
          p2.y = Math.max(padY / 2, Math.min(height - padY / 2, p2.y));
        }
      }
    }
    if (!shifted) break;
  }

  return pos;
}

const FALLBACK_TOPOLOGY: GridTopology = {
  nodes: [
    { id: 'SUB-001', type: 'Substation', name: 'North Cascade 400kV Primary Substation', latitude: 37.8044, longitude: -122.2712, capacity: 400.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1833 },
    { id: 'TX-001', type: 'Transformer', name: 'North Cascade Primary Transformer T-101', latitude: 37.8044, longitude: -122.2712, capacity: 250.0, critical_facility: true, facility_type: 'hospital', status: 'active', risk_level: 'CRITICAL', final_risk_score: 0.8835 },
    { id: 'TX-002', type: 'Transformer', name: 'Harbor View Distribution Transformer T-202', latitude: 37.7749, longitude: -122.4194, capacity: 180.0, critical_facility: true, facility_type: 'water_plant', status: 'active', risk_level: 'MEDIUM', final_risk_score: 0.5238 },
    { id: 'SUB-002', type: 'Substation', name: 'Metro Harbor 220kV Distribution Substation', latitude: 37.7749, longitude: -122.4194, capacity: 220.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1518 },
    { id: 'TX-003', type: 'Transformer', name: 'East Valley Industrial Transformer T-303', latitude: 37.6879, longitude: -122.0748, capacity: 150.0, critical_facility: true, facility_type: 'airport', status: 'active', risk_level: 'LOW', final_risk_score: 0.3814 },
    { id: 'TX-004', type: 'Transformer', name: 'Valley Solar Intertie Transformer T-404', latitude: 37.6531, longitude: -122.0731, capacity: 120.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1820 },
    { id: 'FD-001', type: 'Feeder', name: 'North Feeder Line F-101', latitude: 37.8200, longitude: -122.2800, capacity: 50.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1893 },
    { id: 'FD-002', type: 'Feeder', name: 'Harbor Distribution Feeder F-202', latitude: 37.7649, longitude: -122.4294, capacity: 40.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1548 },
    { id: 'FD-003', type: 'Feeder', name: 'East Valley Feeder F-303', latitude: 37.6779, longitude: -122.0848, capacity: 35.0, critical_facility: false, status: 'active', risk_level: 'LOW', final_risk_score: 0.1308 },
    { id: 'CF-001', type: 'CriticalFacility', name: 'City General Hospital', latitude: 37.8150, longitude: -122.2600, capacity: undefined, critical_facility: true, facility_type: 'hospital', status: 'active', risk_level: 'LOW', final_risk_score: 0.2862 }
  ],
  edges: [
    { source: 'SUB-001', target: 'TX-001', type: 'CONTAINS' },
    { source: 'SUB-001', target: 'TX-002', type: 'CONTAINS' },
    { source: 'SUB-002', target: 'TX-003', type: 'CONTAINS' },
    { source: 'SUB-002', target: 'TX-004', type: 'CONTAINS' },
    { source: 'TX-003', target: 'TX-004', type: 'CONNECTS_TO' },
    { source: 'TX-001', target: 'FD-001', type: 'FEEDS' },
    { source: 'TX-002', target: 'FD-002', type: 'FEEDS' },
    { source: 'TX-003', target: 'FD-003', type: 'FEEDS' },
    { source: 'FD-001', target: 'CF-001', type: 'SUPPLIES' }
  ],
  total_nodes: 10,
  total_edges: 9
};

function computeLocalCascade(assetId: string, nodes: GridNode[], edges: GridEdge[]): CascadeImpact {
  const node = nodes.find(n => n.id === assetId) || { id: assetId, name: assetId, type: 'Unknown' };
  const visited = new Set<string>([assetId]);
  const queue: { id: string; depth: number }[] = [{ id: assetId, depth: 0 }];
  const affectedAssets: { asset_id: string; name: string; type: string; depth: number }[] = [];
  const affectedFacilities: { asset_id: string; name: string; facility_type?: string; depth: number }[] = [];

  while (queue.length > 0) {
    const curr = queue.shift()!;
    const outgoing = edges.filter(e => e.source === curr.id);
    for (const edge of outgoing) {
      if (!visited.has(edge.target)) {
        visited.add(edge.target);
        const targetNode = nodes.find(n => n.id === edge.target);
        const depth = curr.depth + 1;
        if (targetNode) {
          affectedAssets.push({
            asset_id: targetNode.id,
            name: targetNode.name,
            type: targetNode.type,
            depth,
          });
          if (targetNode.type === 'CriticalFacility' || targetNode.critical_facility) {
            affectedFacilities.push({
              asset_id: targetNode.id,
              name: targetNode.name,
              facility_type: targetNode.facility_type,
              depth,
            });
          }
        }
        queue.push({ id: edge.target, depth });
      }
    }
  }

  const cascadeRisk = Math.min(1.0, (affectedAssets.length / 10) * 0.4 + (affectedFacilities.length / 1) * 0.6);
  const path = [assetId, ...affectedAssets.map(a => a.asset_id)];
  const maxDepth = affectedAssets.reduce((max, a) => Math.max(max, a.depth), 0);

  return {
    failed_asset: { asset_id: node.id, name: node.name, type: node.type },
    affected_assets: affectedAssets,
    affected_facilities: affectedFacilities,
    cascade_risk: Math.round(cascadeRisk * 1000) / 1000,
    grid_impact: Math.round((affectedAssets.length / 10) * 1000) / 1000,
    cascade_path: path,
    dependency_depth: maxDepth,
    affected_asset_count: affectedAssets.length,
    critical_facility_count: affectedFacilities.length,
    explanation: affectedAssets.length === 0
      ? `Asset ${assetId} is a terminal node. Failure has no downstream propagation.`
      : `Failure of ${node.name} propagates through ${affectedAssets.length} downstream assets to depth ${maxDepth}${affectedFacilities.length > 0 ? ` impacting ${affectedFacilities.map(f => f.name).join(', ')}` : ''}. Cascade risk score: ${cascadeRisk.toFixed(2)}.`
  };
}

export default function GridTopologyPage() {
  const [topology, setTopology] = useState<GridTopology | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(false);
  const [selected, setSelected] = useState<GridNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [layoutMode, setLayoutMode] = useState<'schematic' | 'geographic'>('schematic');
  const [cascade, setCascade] = useState<CascadeImpact | null>(null);
  const [cascadeLoading, setCascadeLoading] = useState(false);
  const [cascadeError, setCascadeError] = useState<string | null>(null);

  const SVG_W = 860, SVG_H = 520;

  const loadTopology = () => {
    setLoading(true);
    getGridTopology()
      .then(top => {
        if (top && top.nodes && top.nodes.length > 0) {
          setTopology(top);
          setIsFallback(false);
          if (!selected) {
            const defaultNode = top.nodes.find(n => n.id === 'TX-001') || top.nodes[0];
            setSelected(defaultNode);
          }
        } else {
          setTopology(FALLBACK_TOPOLOGY);
          setIsFallback(true);
          if (!selected) {
            setSelected(FALLBACK_TOPOLOGY.nodes.find(n => n.id === 'TX-001') || FALLBACK_TOPOLOGY.nodes[0]);
          }
        }
      })
      .catch(() => {
        setTopology(FALLBACK_TOPOLOGY);
        setIsFallback(true);
        if (!selected) {
          setSelected(FALLBACK_TOPOLOGY.nodes.find(n => n.id === 'TX-001') || FALLBACK_TOPOLOGY.nodes[0]);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTopology();
  }, []);

  const handleCascade = async (node: GridNode) => {
    setCascadeError(null);
    setCascade(null);
    setCascadeLoading(true);
    try {
      const result = await getCascadeImpact(node.id);
      setCascade(result);
    } catch {
      // Graceful local fallback calculation
      const currentNodes = topology?.nodes ?? FALLBACK_TOPOLOGY.nodes;
      const currentEdges = topology?.edges ?? FALLBACK_TOPOLOGY.edges;
      const localResult = computeLocalCascade(node.id, currentNodes, currentEdges);
      setCascade(localResult);
    } finally {
      setCascadeLoading(false);
    }
  };

  if (loading) return (
    <div>
      <div className="top-bar"><h2>🗺️ Grid Topology</h2></div>
      <div className="page-content">
        <div className="loading-state"><div className="spinner" /> Loading grid topology...</div>
      </div>
    </div>
  );

  const nodes = topology?.nodes ?? [];
  const edges = topology?.edges ?? [];
  const positions = computeLayout(nodes, SVG_W, SVG_H, layoutMode);
  const cascadePath = cascade ? new Set(cascade.cascade_path) : new Set<string>();

  // Filter upstream and downstream neighbors for the selected node
  const upstreamEdges = edges.filter(e => e.target === selected?.id);
  const downstreamEdges = edges.filter(e => e.source === selected?.id);

  return (
    <div>
      <div className="top-bar">
        <h2>🗺️ Grid Topology</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {nodes.length} nodes · {edges.length} connections
          </span>
        </div>
      </div>

      <div className="page-content" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {isFallback && (
          <div style={{
            background: 'rgba(245, 158, 11, 0.10)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '8px',
            padding: '8px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '12px',
            color: '#fbbf24'
          }}>
            <span>
              ⚡ <strong>Topology Active:</strong> Rendered with synchronized in-memory grid model (Neo4j daemon disconnected).
            </span>
            <button
              type="button"
              onClick={() => loadTopology()}
              style={{
                background: 'rgba(245, 158, 11, 0.2)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                color: '#fbbf24',
                borderRadius: '4px',
                padding: '3px 10px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: 600
              }}
            >
              🔄 Check Live Neo4j
            </button>
          </div>
        )}

        <div style={{ display: 'flex', gap: '16px', flex: 1 }}>
          {/* Main Diagram Canvas */}
          <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <span className="section-title">Grid Single-Line Topology</span>
              <span className="text-sm text-muted" style={{ display: 'block' }}>
                Click any node to inspect details · Use "Analyze Cascade" to simulate propagation
              </span>
            </div>

            {/* Layout Mode Switcher */}
            <div style={{ display: 'flex', background: 'rgba(15,23,42,0.6)', padding: '3px', borderRadius: '6px', border: '1px solid var(--glass-border)' }}>
              <button
                type="button"
                onClick={() => setLayoutMode('schematic')}
                style={{
                  fontSize: '11px',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontWeight: layoutMode === 'schematic' ? 700 : 500,
                  cursor: 'pointer',
                  border: 'none',
                  background: layoutMode === 'schematic' ? 'var(--blue-glow)' : 'transparent',
                  color: layoutMode === 'schematic' ? '#ffffff' : 'var(--text-muted)',
                  transition: 'all 0.15s ease'
                }}
              >
                ⚡ Schematic Flow
              </button>
              <button
                type="button"
                onClick={() => setLayoutMode('geographic')}
                style={{
                  fontSize: '11px',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontWeight: layoutMode === 'geographic' ? 700 : 500,
                  cursor: 'pointer',
                  border: 'none',
                  background: layoutMode === 'geographic' ? 'var(--blue-glow)' : 'transparent',
                  color: layoutMode === 'geographic' ? '#ffffff' : 'var(--text-muted)',
                  transition: 'all 0.15s ease'
                }}
              >
                🗺️ Geographic Map
              </button>
            </div>
          </div>

          {/* Quick Node Selector Pills */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', margin: '8px 0 14px 0' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', alignSelf: 'center', marginRight: '4px' }}>
              Quick Select:
            </span>
            {nodes.map(n => {
              const isSel = selected?.id === n.id;
              const nColor = RISK_COLORS[n.risk_level ?? 'undefined'] || '#3b82f6';
              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => setSelected(n)}
                  style={{
                    fontSize: '11px',
                    padding: '4px 9px',
                    borderRadius: '5px',
                    fontWeight: isSel ? 700 : 500,
                    cursor: 'pointer',
                    border: isSel ? `1px solid ${nColor}` : '1px solid var(--glass-border)',
                    background: isSel ? 'rgba(59,130,246,0.25)' : 'rgba(15,23,42,0.6)',
                    color: isSel ? '#ffffff' : 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: nColor }} />
                  {n.id}
                </button>
              );
            })}
          </div>

          {/* SVG Canvas */}
          <div style={{ position: 'relative', width: '100%', overflow: 'hidden', borderRadius: '8px', border: '1px solid var(--glass-border)', background: '#0a0e1a' }}>
            <svg
              width="100%"
              viewBox={`0 0 ${SVG_W} ${SVG_H}`}
              style={{ display: 'block' }}
            >
              <defs>
                {/* Background Grid Pattern */}
                <pattern id="grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
                  <circle cx="12" cy="12" r="1" fill="rgba(148,163,184,0.08)" />
                </pattern>

                {/* Arrowhead Markers */}
                <marker id="arrow-normal" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="rgba(96,165,250,0.7)" />
                </marker>
                <marker id="arrow-cascade" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#ef4444" />
                </marker>
                <marker id="arrow-hospital" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981" />
                </marker>
                <marker id="arrow-tie" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#f59e0b" />
                </marker>
              </defs>

              {/* Grid Background */}
              <rect width={SVG_W} height={SVG_H} fill="url(#grid-dots)" />

              {/* Hierarchical Column Guidelines (in schematic mode) */}
              {layoutMode === 'schematic' && (
                <g opacity="0.4">
                  <line x1="105" y1="30" x2="105" y2="490" stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                  <text x="105" y="24" textAnchor="middle" fill="rgba(148,163,184,0.5)" fontSize="10" fontWeight="600">SUBSTATIONS</text>

                  <line x1="310" y1="30" x2="310" y2="490" stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                  <text x="310" y="24" textAnchor="middle" fill="rgba(148,163,184,0.5)" fontSize="10" fontWeight="600">TRANSFORMERS</text>

                  <line x1="550" y1="30" x2="550" y2="490" stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                  <text x="550" y="24" textAnchor="middle" fill="rgba(148,163,184,0.5)" fontSize="10" fontWeight="600">FEEDERS</text>

                  <line x1="750" y1="30" x2="750" y2="490" stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                  <text x="750" y="24" textAnchor="middle" fill="rgba(148,163,184,0.5)" fontSize="10" fontWeight="600">CRITICAL LOADS</text>
                </g>
              )}

              {/* Edges */}
              {edges.map((edge, i) => {
                const src = positions[edge.source];
                const tgt = positions[edge.target];
                if (!src || !tgt) return null;

                const isInCascade = cascadePath.has(edge.source) && cascadePath.has(edge.target);
                const isSelectedConn = selected && (selected.id === edge.source || selected.id === edge.target);
                const isSupplies = edge.type === 'SUPPLIES';
                const isConnectsTo = edge.type === 'CONNECTS_TO';

                // Offset endpoints so arrow meets the outer edge of the 22px node circle
                const dx = tgt.x - src.x;
                const dy = tgt.y - src.y;
                const dist = Math.hypot(dx, dy) || 1;
                const rSrc = 23;
                const rTgt = 26;
                const x1 = src.x + (dx / dist) * rSrc;
                const y1 = src.y + (dy / dist) * rSrc;
                const x2 = tgt.x - (dx / dist) * rTgt;
                const y2 = tgt.y - (dy / dist) * rTgt;

                let strokeColor = 'rgba(99,179,237,0.35)';
                let markerUrl = 'url(#arrow-normal)';
                let strokeWidth = 1.8;

                if (isInCascade) {
                  strokeColor = '#ef4444';
                  markerUrl = 'url(#arrow-cascade)';
                  strokeWidth = 3;
                } else if (isSelectedConn) {
                  strokeColor = '#60a5fa';
                  strokeWidth = 2.4;
                } else if (isSupplies) {
                  strokeColor = '#10b981';
                  markerUrl = 'url(#arrow-hospital)';
                  strokeWidth = 2.2;
                } else if (isConnectsTo) {
                  strokeColor = '#f59e0b';
                  markerUrl = 'url(#arrow-tie)';
                }

                // Midpoint for relationship label
                const midX = (x1 + x2) / 2;
                const midY = (y1 + y2) / 2;

                return (
                  <g key={`edge-${i}`}>
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeDasharray={isConnectsTo ? '6 4' : undefined}
                      markerEnd={markerUrl}
                      style={{ transition: 'stroke 0.2s ease, stroke-width 0.2s ease' }}
                    />
                    {/* Relationship label pill for selected or critical connections */}
                    {(isSelectedConn || isInCascade || isSupplies) && (
                      <g transform={`translate(${midX}, ${midY})`}>
                        <rect
                          x={-28}
                          y={-8}
                          width={56}
                          height={16}
                          rx={3}
                          fill="rgba(10,14,26,0.92)"
                          stroke={strokeColor}
                          strokeWidth={1}
                        />
                        <text
                          textAnchor="middle"
                          y={3}
                          fill={strokeColor}
                          fontSize="9"
                          fontWeight="700"
                          style={{ pointerEvents: 'none', userSelect: 'none' }}
                        >
                          {edge.type}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map(node => {
                const pos = positions[node.id];
                if (!pos) return null;

                const color = RISK_COLORS[node.risk_level ?? 'undefined'] || '#3b82f6';
                const isSelected = selected?.id === node.id;
                const isHovered = hoveredNode === node.id;
                const inCascade = cascadePath.has(node.id);
                const isCritical = node.risk_level === 'CRITICAL';
                const nodeIcon = TYPE_ICONS[node.type] || '⚡';
                const subLabel = getShortSub(node);

                return (
                  <g
                    key={node.id}
                    style={{ cursor: 'pointer', pointerEvents: 'all' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelected(node);
                    }}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    {/* Generous 38px invisible click hitbox */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={38}
                      fill="transparent"
                      style={{ cursor: 'pointer' }}
                    />

                    {/* Selected Glowing Outer Ring */}
                    {isSelected && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={29}
                        fill="none"
                        stroke="#60a5fa"
                        strokeWidth="2.5"
                        strokeDasharray="4 3"
                        opacity="0.9"
                      />
                    )}

                    {/* Critical Alert Pulsing Halo */}
                    {(isCritical || inCascade) && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={27}
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth="2"
                        opacity={inCascade ? '1' : '0.7'}
                      />
                    )}

                    {/* Main Node Body Circle */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={isSelected ? 21 : 18}
                      fill="#0f172a"
                      stroke={inCascade ? '#ef4444' : isSelected ? '#60a5fa' : color}
                      strokeWidth={isSelected || inCascade ? 3 : 2}
                      style={{
                        filter: isSelected ? 'drop-shadow(0 0 8px rgba(96,165,250,0.5))' : 'none',
                        transition: 'all 0.15s ease'
                      }}
                    />

                    {/* Inner Type Icon */}
                    <text
                      x={pos.x}
                      y={pos.y + 4}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize={isSelected ? '12' : '11'}
                      fontWeight="700"
                      style={{ pointerEvents: 'none', userSelect: 'none' }}
                    >
                      {nodeIcon}
                    </text>

                    {/* Readable Node ID Pill */}
                    <g transform={`translate(${pos.x}, ${pos.y + 26})`}>
                      <rect
                        x={-31}
                        y={-8}
                        width={62}
                        height={17}
                        rx={4}
                        fill="rgba(15,23,42,0.92)"
                        stroke={isSelected ? '#60a5fa' : isCritical ? '#ef4444' : 'rgba(148,163,184,0.3)'}
                        strokeWidth={isSelected ? 1.5 : 1}
                      />
                      <text
                        textAnchor="middle"
                        y={4}
                        fill={isSelected ? '#93c5fd' : '#f8fafc'}
                        fontSize="10"
                        fontWeight="700"
                        letterSpacing="0.4px"
                        style={{ pointerEvents: 'none', userSelect: 'none' }}
                      >
                        {node.id}
                      </text>
                    </g>

                    {/* Asset Subtitle */}
                    <text
                      x={pos.x}
                      y={pos.y + 46}
                      textAnchor="middle"
                      fill={isHovered || isSelected ? '#cbd5e1' : 'rgba(148,163,184,0.75)'}
                      fontSize="9"
                      fontWeight="500"
                      style={{ pointerEvents: 'none', userSelect: 'none' }}
                    >
                      {subLabel}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Canvas Footer Legend */}
          <div style={{ display: 'flex', gap: '16px', marginTop: '14px', flexWrap: 'wrap', fontSize: '11px', color: 'var(--text-muted)', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Risk Levels:</span>
            {Object.entries(RISK_COLORS).filter(([k]) => k !== 'undefined').map(([lvl, clr]) => (
              <span key={lvl} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: clr, display: 'inline-block' }} />
                {lvl}
              </span>
            ))}
            <span style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '18px', height: '2px', background: '#60a5fa', display: 'inline-block' }} />
                FEEDS / CONTAINS
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '18px', height: '2px', background: '#10b981', display: 'inline-block' }} />
                SUPPLIES (Critical)
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '18px', height: '2px', borderTop: '2px dashed #f59e0b', display: 'inline-block' }} />
                CONNECTS_TO
              </span>
            </span>
          </div>
        </div>

        {/* Selected Asset Details & Cascade Analysis Sidebar */}
        <div style={{ width: '330px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {selected ? (
            <div className="glass-card">
              <div className="section-header" style={{ marginBottom: '12px' }}>
                <div>
                  <span className="section-title" style={{ display: 'block', fontSize: '15px' }}>
                    {selected.name || selected.id}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {selected.id} · {selected.type}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '9px' }}>
                <div className="flex justify-between">
                  <span className="text-muted">Status</span>
                  <span style={{ color: selected.status === 'active' ? 'var(--green)' : 'var(--amber)', fontWeight: 600 }}>
                    ● {selected.status.toUpperCase()}
                  </span>
                </div>

                {selected.risk_level && (
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Risk Assessment</span>
                    <RiskBadge level={selected.risk_level} />
                  </div>
                )}

                {selected.final_risk_score !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-muted">Failure Probability</span>
                    <span style={{ fontWeight: 700, color: selected.final_risk_score > 0.5 ? 'var(--risk-critical)' : 'var(--text-primary)' }}>
                      {(selected.final_risk_score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}

                {selected.capacity && (
                  <div className="flex justify-between">
                    <span className="text-muted">Rated Capacity</span>
                    <span>{selected.capacity} MVA</span>
                  </div>
                )}

                {selected.latitude && selected.longitude && (
                  <div className="flex justify-between">
                    <span className="text-muted">GPS Coordinates</span>
                    <span style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                      {selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}
                    </span>
                  </div>
                )}

                {selected.critical_facility && (
                  <div style={{ padding: '8px 10px', background: 'rgba(239,68,68,0.12)', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', marginTop: '4px' }}>
                    <div style={{ color: 'var(--risk-critical)', fontWeight: 700, fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>🏥</span> Critical Facility Feeder
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Type: {selected.facility_type ?? 'Hospital / Essential Service'}
                    </div>
                  </div>
                )}

                {/* Topology Relationships */}
                <div style={{ marginTop: '8px', borderTop: '1px solid var(--glass-border)', paddingTop: '8px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Graph Connections
                  </div>
                  {upstreamEdges.length > 0 && (
                    <div style={{ fontSize: '11px', marginBottom: '4px' }}>
                      <span className="text-muted">Supplied by: </span>
                      <span style={{ color: 'var(--blue-glow)' }}>{upstreamEdges.map(e => e.source).join(', ')}</span>
                    </div>
                  )}
                  {downstreamEdges.length > 0 && (
                    <div style={{ fontSize: '11px' }}>
                      <span className="text-muted">Feeds to: </span>
                      <span style={{ color: 'var(--green)' }}>{downstreamEdges.map(e => e.target).join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>

              <button
                className="btn btn-danger"
                style={{ width: '100%', marginTop: '16px', justifyContent: 'center', fontWeight: 600 }}
                onClick={() => handleCascade(selected)}
                disabled={cascadeLoading}
              >
                {cascadeLoading ? <><div className="spinner" /> Simulating Cascade...</> : '🔗 Simulate Cascade Failure'}
              </button>
            </div>
          ) : (
            <div className="glass-card" style={{ textAlign: 'center', padding: '30px 20px' }}>
              <div className="empty-state" style={{ flexDirection: 'column', gap: '8px' }}>
                <div style={{ fontSize: '28px' }}>🗺️</div>
                <div style={{ fontWeight: 600 }}>Select a Node</div>
                <div className="text-sm text-muted">Click any node on the map to inspect its real-time telemetry, risk, and connections.</div>
              </div>
            </div>
          )}

          {/* Cascade Failure Simulation Result */}
          {cascadeError && (
            <div className="glass-card">
              <div className="error-state" style={{ height: 'auto', padding: '12px' }}>⚠ {cascadeError}</div>
            </div>
          )}

          {cascade && (
            <div className="glass-card" style={{ border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.04)' }}>
              <div className="section-header">
                <span className="section-title" style={{ color: 'var(--risk-critical)' }}>
                  🔴 Cascade Propagation Impact
                </span>
              </div>
              <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ padding: '8px 10px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  {cascade.explanation}
                </div>

                <div className="grid-2 gap-2">
                  {[
                    ['Affected Assets', cascade.affected_asset_count, 'var(--risk-high)'],
                    ['Critical Facilities', cascade.critical_facility_count, 'var(--risk-critical)'],
                    ['Cascade Risk', `${(cascade.cascade_risk * 100).toFixed(0)}%`, 'var(--amber)'],
                    ['Grid Impact', `${(cascade.grid_impact * 100).toFixed(0)}%`, 'var(--blue-glow)'],
                    ['Dependency Depth', cascade.dependency_depth, 'var(--text-secondary)'],
                  ].map(([lbl, val, clr]) => (
                    <div key={lbl as string} style={{ padding: '7px 6px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px', textAlign: 'center' }}>
                      <div className="text-muted" style={{ fontSize: '10px' }}>{lbl}</div>
                      <div style={{ color: clr as string, fontWeight: 700, fontSize: '13px' }}>{val}</div>
                    </div>
                  ))}
                </div>

                {cascade.affected_facilities.length > 0 && (
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--risk-critical)', fontWeight: 600, marginBottom: '4px' }}>
                      Hospital / Critical Facilities at Risk:
                    </div>
                    {cascade.affected_facilities.map(f => (
                      <div key={f.asset_id} style={{ fontSize: '11px', padding: '5px 8px', background: 'rgba(239,68,68,0.1)', borderRadius: '4px', marginBottom: '3px', border: '1px solid rgba(239,68,68,0.2)' }}>
                        🏥 {f.name} ({f.facility_type ?? f.asset_id})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}
