// GridPulse AI — API Service Layer
// All API calls to the FastAPI backend

import axios from 'axios';
import type {
  Asset, AssetDetail, GridTopology, CascadeImpact,
  DashboardData, RiskSummaryItem, WeatherRiskItem,
  AdvisoryResponse, ChatResponse, WorkOrder, WorkOrderPriority
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${API_URL}/api/v1`;

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Health ────────────────────────────────────────────────────────────────────

export const getHealth = () => api.get('/health').then(r => r.data);

// ─── Dashboard ────────────────────────────────────────────────────────────────

export const getDashboard = (): Promise<DashboardData> =>
  api.get('/dashboard').then(r => r.data);

// ─── Assets ───────────────────────────────────────────────────────────────────

export const getAssets = (params?: {
  risk_level?: string;
  asset_type?: string;
  limit?: number;
  offset?: number;
}) => api.get('/assets', { params }).then(r => r.data as { assets: Asset[]; total: number });

export const getAssetDetail = (assetId: string): Promise<AssetDetail> =>
  api.get(`/assets/${assetId}`).then(r => r.data);

export const getAssetRisk = (assetId: string) =>
  api.get(`/assets/${assetId}/risk`).then(r => r.data);

// ─── Risk ─────────────────────────────────────────────────────────────────────

export const getAllRiskScores = () =>
  api.get('/risk').then(r => r.data as {
    risk_scores: RiskSummaryItem[];
    total: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
  });

// ─── Grid Topology ────────────────────────────────────────────────────────────

export const getGridTopology = (): Promise<GridTopology> =>
  api.get('/grid/topology').then(r => r.data);

export const getCascadeImpact = (assetId: string): Promise<CascadeImpact> =>
  api.get(`/grid/assets/${assetId}/impact`).then(r => r.data);

// ─── Weather ──────────────────────────────────────────────────────────────────

export const getAllWeather = () =>
  api.get('/weather').then(r => r.data as { weather_data: WeatherRiskItem[]; total: number });

export const getAssetWeather = (assetId: string) =>
  api.get(`/weather/${assetId}`).then(r => r.data);

export const getCrewPrepositionPlan = (crews?: any[]) =>
  api.post('/weather/crew-preposition', {
    crews: crews || [
      { crew_id: 'CREW-01', available: true },
      { crew_id: 'CREW-02', available: true },
      { crew_id: 'CREW-03', available: true },
    ]
  }).then(r => r.data);

// ─── Advisory ─────────────────────────────────────────────────────────────────

export const getAssetAdvisory = (assetId: string, question: string): Promise<AdvisoryResponse> =>
  api.post('/advisory', { asset_id: assetId, question }).then(r => r.data);

export const sendChatMessage = (message: string, context = {}): Promise<ChatResponse> =>
  api.post('/advisory/chat', { message, context }).then(r => r.data);

// ─── Recommendations / Work Orders ────────────────────────────────────────────

export const getRecommendations = () =>
  api.get('/recommendations').then(r => r.data);

export const getAllWorkOrders = (): Promise<WorkOrder[]> =>
  api.get('/workorders').then(r => r.data);

export const getAssetWorkOrders = (assetId: string): Promise<WorkOrder[]> =>
  api.get(`/assets/${assetId}/workorders`).then(r => r.data);

export const createWorkOrder = (assetId: string, data: {
  priority: WorkOrderPriority;
  description: string;
  assigned_crew?: string;
  scheduled_time?: string;
}): Promise<WorkOrder> =>
  api.post(`/assets/${assetId}/workorders`, data).then(r => r.data);

export const updateWorkOrder = (workorderId: number, data: {
  status?: string;
  assigned_crew?: string;
}): Promise<WorkOrder> =>
  api.patch(`/workorders/${workorderId}`, data).then(r => r.data);
