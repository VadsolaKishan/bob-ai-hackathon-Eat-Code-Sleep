// GridPulse AI — TypeScript Type Definitions
// Mirrors Pydantic schemas from the FastAPI backend

export type AssetType = 'transformer' | 'substation' | 'feeder' | 'critical_facility';
export type AssetStatus = 'active' | 'maintenance' | 'offline';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type WorkOrderStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
export type WorkOrderPriority = 'low' | 'medium' | 'high' | 'critical';
export type Urgency = 'ROUTINE' | 'MONITOR' | 'URGENT' | 'IMMEDIATE';

export interface Asset {
  id: number;
  asset_id: string;
  name: string;
  asset_type: AssetType;
  latitude: number;
  longitude: number;
  capacity?: number;
  critical_facility: boolean;
  facility_type?: string;
  status: AssetStatus;
  installation_date?: string;
  risk_level?: RiskLevel;
  final_risk_score?: number;
}

export interface SensorReading {
  id: number;
  asset_id: string;
  timestamp: string;
  temperature: number;
  vibration: number;
  partial_discharge: number;
}

export interface DGAReading {
  id: number;
  asset_id: string;
  timestamp: string;
  h2: number;
  ch4: number;
  c2h2: number;
  c2h4: number;
  c2h6: number;
  co: number;
  co2: number;
}

export interface WeatherReading {
  id: number;
  asset_id: string;
  timestamp: string;
  wind_speed: number;
  rainfall: number;
  lightning_probability: number;
  flood_risk: number;
  temperature: number;
}

export interface Incident {
  id: number;
  asset_id: string;
  timestamp: string;
  failure_type: string;
  severity: string;
  description: string;
}

export interface RiskScore {
  id: number;
  asset_id: string;
  timestamp: string;
  failure_probability: number;
  asset_health_risk: number;
  weather_risk: number;
  grid_impact: number;
  cascade_risk: number;
  critical_multiplier: number;
  final_risk_score: number;
  risk_level: RiskLevel;
}

export interface WorkOrder {
  id: number;
  asset_id: string;
  priority: WorkOrderPriority;
  status: WorkOrderStatus;
  assigned_crew?: string;
  scheduled_time?: string;
  description: string;
}

export interface AssetDetail {
  asset: Asset;
  latest_sensor?: SensorReading;
  latest_dga?: DGAReading;
  latest_weather?: WeatherReading;
  latest_risk?: RiskScore;
  incidents: Incident[];
}

export interface GridNode {
  id: string;
  type: string;
  name: string;
  latitude?: number;
  longitude?: number;
  risk_level?: RiskLevel;
  final_risk_score?: number;
  status: string;
  capacity?: number;
  critical_facility: boolean;
  facility_type?: string;
}

export interface GridEdge {
  source: string;
  target: string;
  type: string;
}

export interface GridTopology {
  nodes: GridNode[];
  edges: GridEdge[];
  total_nodes: number;
  total_edges: number;
}

export interface CascadeImpact {
  failed_asset: { asset_id: string; name: string; type: string };
  affected_assets: Array<{ asset_id: string; name: string; type: string; depth: number }>;
  affected_facilities: Array<{ asset_id: string; name: string; facility_type?: string; depth: number }>;
  cascade_risk: number;
  grid_impact: number;
  cascade_path: string[];
  dependency_depth: number;
  affected_asset_count: number;
  critical_facility_count: number;
  explanation: string;
}

export interface AdvisoryResponse {
  asset_id: string;
  question: string;
  summary: string;
  risk_factors: string[];
  potential_consequences: string[];
  recommended_actions: string[];
  urgency: Urgency;
  provider: string;
  created_at: string;
}

export interface ChatResponse {
  response: string;
  provider: string;
  timestamp: string;
  asset_id?: string;
  risk_level?: RiskLevel;
  risk_score?: number;
  recommended_actions?: string[];
  data_sources?: string[];
}

export interface DashboardData {
  summary: {
    total_assets: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    active_work_orders: number;
  };
  top_risk_assets: Array<Asset & { final_risk_score: number; risk_level: RiskLevel }>;
  recent_incidents: Incident[];
  weather_alerts: Array<{
    asset_id: string;
    asset_name: string;
    wind_speed: number;
    lightning_probability: number;
    flood_risk: number;
    temperature: number;
  }>;
  risk_distribution: Record<RiskLevel, number>;
}

export interface RiskSummaryItem {
  asset_id: string;
  asset_name: string;
  asset_type: AssetType;
  final_risk_score: number;
  risk_level: RiskLevel;
  failure_probability: number;
  grid_impact: number;
  cascade_risk: number;
  timestamp?: string;
}

export interface WeatherRiskItem {
  asset_id: string;
  asset_name: string;
  wind_speed: number;
  rainfall: number;
  lightning_probability: number;
  flood_risk: number;
  temperature: number;
  weather_risk_score: number;
  dominant_hazard: string;
  timestamp?: string;
}
