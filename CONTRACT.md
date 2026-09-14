# GridPulse AI — API Contract & Data Schemas

> **Version:** 2.0.0  
> **Base URL:** `http://localhost:8000/api/v1`  
> **Format:** All request and response bodies are JSON (`Content-Type: application/json`)

---

## Table of Contents
1. [Data Schemas](#data-schemas)
2. [API Endpoints](#api-endpoints)
3. [Error Responses](#error-responses)
4. [Graph Model](#graph-model)

---

## Data Schemas

### Asset
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "name": "North Cascade Primary Transformer",
  "asset_type": "transformer",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "capacity": 250.0,
  "critical_facility": true,
  "facility_type": "hospital",
  "status": "active",
  "installation_date": "2011-06-15"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | integer | Auto-increment PK |
| `asset_id` | string | Unique business key (e.g. `TX-001`) |
| `name` | string | Human-readable asset name |
| `asset_type` | enum | `transformer` \| `substation` \| `feeder` |
| `latitude` | float | WGS-84 latitude |
| `longitude` | float | WGS-84 longitude |
| `capacity` | float | Capacity in MVA |
| `critical_facility` | bool | Whether downstream facility is critical |
| `facility_type` | string \| null | `hospital` \| `water_plant` \| `airport` \| `data_center` \| null |
| `status` | enum | `active` \| `maintenance` \| `offline` |
| `installation_date` | date string | ISO 8601 date |

---

### SensorReading
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "temperature": 92.4,
  "vibration": 4.8,
  "partial_discharge": 540.0
}
```

| Field | Type | Units | Normal Range |
|---|---|---|---|
| `temperature` | float | °C | < 75 |
| `vibration` | float | mm/s | < 2.0 |
| `partial_discharge` | float | pC | < 200 |

---

### DGAReading (Dissolved Gas Analysis)
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "h2": 120.0,
  "ch4": 45.0,
  "c2h2": 4.2,
  "c2h4": 68.0,
  "c2h6": 12.0,
  "co": 250.0,
  "co2": 2800.0
}
```

| Field | Gas | Type | Units | IEEE C57.104 Limit |
|---|---|---|---|---|
| `h2` | Hydrogen | float | ppm | < 100 |
| `ch4` | Methane | float | ppm | < 120 |
| `c2h2` | Acetylene | float | ppm | < 3 (arcing indicator) |
| `c2h4` | Ethylene | float | ppm | < 50 |
| `c2h6` | Ethane | float | ppm | < 65 |
| `co` | Carbon Monoxide | float | ppm | < 350 |
| `co2` | Carbon Dioxide | float | ppm | < 2500 |

---

### WeatherReading
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "wind_speed": 68.5,
  "rainfall": 22.0,
  "lightning_probability": 0.75,
  "flood_risk": 0.3,
  "temperature": 38.2
}
```

| Field | Type | Units | High-risk Threshold |
|---|---|---|---|
| `wind_speed` | float | km/h | > 70 |
| `rainfall` | float | mm/h | > 30 |
| `lightning_probability` | float | 0–1 | > 0.6 |
| `flood_risk` | float | 0–1 | > 0.5 |
| `temperature` | float | °C | > 40 |

---

### Incident
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "timestamp": "2024-01-10T14:22:00Z",
  "failure_type": "thermal",
  "severity": "high",
  "description": "Oil temperature exceeded 95°C during peak load"
}
```

| Field | Type | Values |
|---|---|---|
| `failure_type` | enum | `thermal` \| `arcing` \| `partial_discharge` \| `mechanical` \| `weather` \| `overload` |
| `severity` | enum | `low` \| `medium` \| `high` \| `critical` |

---

### RiskScore
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "failure_probability": 0.82,
  "asset_health_risk": 0.75,
  "weather_risk": 0.65,
  "grid_impact": 0.90,
  "cascade_risk": 0.70,
  "critical_multiplier": 1.5,
  "final_risk_score": 0.92,
  "risk_level": "CRITICAL"
}
```

**Risk Formula:**
```
base_risk = 0.30 * failure_probability
          + 0.20 * asset_health_risk
          + 0.15 * weather_risk
          + 0.20 * grid_impact
          + 0.15 * cascade_risk

final_risk_score = clamp(base_risk * critical_multiplier, 0, 1)
```

**Risk Levels:**
| Score | Level |
|---|---|
| 0.00 – 0.39 | LOW |
| 0.40 – 0.69 | MEDIUM |
| 0.70 – 0.84 | HIGH |
| 0.85 – 1.00 | CRITICAL |

**Critical Multipliers:**
| Facility Type | Multiplier |
|---|---|
| Normal | 1.0 |
| Important | 1.2 |
| Critical (hospital, water, airport) | 1.5 |

---

### WorkOrder
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "priority": "critical",
  "status": "pending",
  "assigned_crew": "Rapid Response Unit #1",
  "scheduled_time": "2024-01-15T12:00:00Z",
  "description": "Immediate inspection: arcing fault detected in DGA analysis"
}
```

| Field | Type | Values |
|---|---|---|
| `priority` | enum | `low` \| `medium` \| `high` \| `critical` |
| `status` | enum | `pending` \| `assigned` \| `in_progress` \| `completed` \| `cancelled` |

---

### AIAdvisory
```json
{
  "id": 1,
  "asset_id": "TX-001",
  "question": "Why is this asset critical?",
  "response": "{ structured JSON response }",
  "provider": "IBM Granite",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Advisory Response Structure:**
```json
{
  "summary": "TX-001 is at CRITICAL risk due to elevated acetylene levels indicating active arcing fault combined with severe weather conditions.",
  "risk_factors": [
    "Acetylene levels at 4.2 ppm (threshold: 3 ppm) — active arcing fault",
    "Oil temperature at 92.4°C — thermal stress",
    "Wind speed 68.5 km/h — structural risk"
  ],
  "potential_consequences": [
    "Transformer failure within 24–48 hours without intervention",
    "Power outage affecting 42,000 customers",
    "Cascade failure to 3 downstream feeders"
  ],
  "recommended_actions": [
    "Deploy emergency inspection crew immediately",
    "Pre-position mobile transformer backup unit",
    "Initiate contingency load transfer to SUB-EAST-04"
  ],
  "urgency": "IMMEDIATE",
  "provider": "IBM Granite"
}
```

---

### Grid Node (Neo4j)
```json
{
  "id": "TX-001",
  "type": "Transformer",
  "name": "North Cascade Primary Transformer",
  "status": "active",
  "capacity": 250.0,
  "critical_facility": true,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "risk_level": "CRITICAL",
  "final_risk_score": 0.92
}
```

### Grid Relationship
```json
{
  "source": "SUB-001",
  "target": "TX-001",
  "type": "CONTAINS"
}
```

**Relationship Types:**
| Type | Description |
|---|---|
| `CONTAINS` | Substation contains transformer |
| `CONNECTS_TO` | Transformer-to-transformer connection |
| `FEEDS` | Transformer feeds feeder line |
| `SUPPLIES` | Feeder supplies critical facility |

---

## API Endpoints

### Health

#### `GET /api/v1/health`
Returns service status and dependency health.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "postgres": "connected",
    "neo4j": "connected",
    "watsonx": "available"
  }
}
```

---

### Assets

#### `GET /api/v1/assets`
Returns all assets with their latest risk scores.

**Query Parameters:**
| Param | Type | Description |
|---|---|---|
| `risk_level` | string | Filter by `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `asset_type` | string | Filter by `transformer`, `substation`, `feeder` |
| `limit` | integer | Max results (default: 100) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:**
```json
{
  "assets": [
    {
      "asset_id": "TX-001",
      "name": "North Cascade Primary Transformer",
      "asset_type": "transformer",
      "status": "active",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "capacity": 250.0,
      "critical_facility": true,
      "risk_level": "CRITICAL",
      "final_risk_score": 0.92
    }
  ],
  "total": 10
}
```

#### `GET /api/v1/assets/{asset_id}`
Returns full asset detail including latest sensor, DGA, weather readings and risk score.

**Response:**
```json
{
  "asset": { "...full Asset schema..." },
  "latest_sensor": { "...SensorReading..." },
  "latest_dga": { "...DGAReading..." },
  "latest_weather": { "...WeatherReading..." },
  "latest_risk": { "...RiskScore..." },
  "incidents": [ "...list of Incident..." ]
}
```

#### `GET /api/v1/assets/{asset_id}/risk`
Returns current risk score for a single asset (triggers recalculation).

**Response:** Full `RiskScore` schema

---

### Risk

#### `GET /api/v1/risk`
Returns risk scores for all assets sorted by `final_risk_score` descending.

**Response:**
```json
{
  "risk_scores": [
    {
      "asset_id": "TX-001",
      "asset_name": "North Cascade Primary Transformer",
      "asset_type": "transformer",
      "final_risk_score": 0.92,
      "risk_level": "CRITICAL",
      "failure_probability": 0.82,
      "grid_impact": 0.90,
      "cascade_risk": 0.70,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "critical_count": 2,
  "high_count": 3,
  "medium_count": 3,
  "low_count": 2
}
```

---

### Grid Topology

#### `GET /api/v1/grid/topology`
Returns full grid graph for visualization.

**Response:**
```json
{
  "nodes": [
    {
      "id": "TX-001",
      "type": "Transformer",
      "name": "North Cascade Primary Transformer",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "risk_level": "CRITICAL",
      "final_risk_score": 0.92,
      "status": "active",
      "capacity": 250.0,
      "critical_facility": true
    }
  ],
  "edges": [
    {
      "source": "SUB-001",
      "target": "TX-001",
      "type": "CONTAINS"
    }
  ],
  "total_nodes": 10,
  "total_edges": 12
}
```

#### `GET /api/v1/grid/assets/{asset_id}/impact`
Returns full cascade failure analysis for the given asset.

**Response:**
```json
{
  "failed_asset": {
    "asset_id": "TX-001",
    "name": "North Cascade Primary Transformer",
    "risk_level": "CRITICAL"
  },
  "affected_assets": [
    {
      "asset_id": "FD-001",
      "name": "North Feeder Line 1",
      "type": "feeder",
      "depth": 1
    }
  ],
  "affected_facilities": [
    {
      "asset_id": "CF-001",
      "name": "City General Hospital",
      "facility_type": "hospital",
      "depth": 2
    }
  ],
  "cascade_risk": 0.78,
  "grid_impact": 0.85,
  "cascade_path": ["TX-001", "FD-001", "CF-001"],
  "dependency_depth": 2,
  "affected_asset_count": 3,
  "critical_facility_count": 1,
  "explanation": "Failure of TX-001 cascades through 3 assets reaching 1 critical facility."
}
```

---

### Weather

#### `GET /api/v1/weather`
Returns latest weather readings for all assets with weather risk scores.

**Response:**
```json
{
  "weather_data": [
    {
      "asset_id": "TX-001",
      "asset_name": "North Cascade Primary Transformer",
      "wind_speed": 68.5,
      "rainfall": 22.0,
      "lightning_probability": 0.75,
      "flood_risk": 0.3,
      "temperature": 38.2,
      "weather_risk_score": 0.65,
      "dominant_hazard": "wind",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /api/v1/weather/{asset_id}`
Returns weather history and risk for a single asset.

---

### Advisory

#### `POST /api/v1/advisory`
Ask the AI advisor about a specific asset.

**Request:**
```json
{
  "asset_id": "TX-001",
  "question": "Why is this asset critical and what should we do?"
}
```

**Response:** Full `AIAdvisory` response (see AIAdvisory schema above)

#### `POST /api/v1/advisory/chat`
Free-form chat with the grid AI advisor.

**Request:**
```json
{
  "message": "Which asset should we inspect first?",
  "context": {}
}
```

**Response:**
```json
{
  "response": "Based on current risk analysis, TX-001 (North Cascade Primary Transformer) should be your immediate priority...",
  "provider": "IBM Granite",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### Recommendations & Work Orders

#### `GET /api/v1/recommendations`
Auto-generates work orders from current risk scores.

**Response:**
```json
{
  "work_orders": [
    {
      "asset_id": "TX-001",
      "asset_name": "North Cascade Primary Transformer",
      "priority": "critical",
      "action": "Immediate inspection and crew pre-positioning required",
      "risk_level": "CRITICAL",
      "final_risk_score": 0.92
    }
  ],
  "total": 10
}
```

#### `GET /api/v1/assets/{asset_id}/workorders`
Returns work orders for a specific asset.

#### `POST /api/v1/assets/{asset_id}/workorders`
Creates a work order for an asset.

**Request:**
```json
{
  "priority": "high",
  "description": "Thermal inspection required",
  "assigned_crew": "Team Alpha",
  "scheduled_time": "2024-01-16T08:00:00Z"
}
```

#### `PATCH /api/v1/workorders/{id}`
Updates work order status.

**Request:**
```json
{
  "status": "in_progress",
  "assigned_crew": "Team Alpha"
}
```

---

### Dashboard

#### `GET /api/v1/dashboard`
Returns aggregated data for the main dashboard.

**Response:**
```json
{
  "summary": {
    "total_assets": 10,
    "critical_count": 2,
    "high_count": 3,
    "medium_count": 3,
    "low_count": 2,
    "active_work_orders": 5
  },
  "top_risk_assets": [ "...top 5 assets by risk..." ],
  "recent_incidents": [ "...last 5 incidents..." ],
  "weather_alerts": [ "...assets with high weather risk..." ],
  "risk_distribution": {
    "CRITICAL": 2,
    "HIGH": 3,
    "MEDIUM": 3,
    "LOW": 2
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Asset TX-999 not found",
  "status_code": 404,
  "error_type": "NOT_FOUND"
}
```

| HTTP Status | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request — invalid input |
| 404 | Not Found — resource does not exist |
| 422 | Unprocessable Entity — validation error |
| 500 | Internal Server Error |
| 503 | Service Unavailable — database/AI offline |

---

## Graph Model

```
(:Substation {asset_id, name, capacity, status, latitude, longitude})
    -[:CONTAINS]->
(:Transformer {asset_id, name, capacity, status, critical_facility, latitude, longitude})
    -[:CONNECTS_TO]->
(:Transformer)

(:Transformer)
    -[:FEEDS]->
(:Feeder {asset_id, name, status})

(:Feeder)
    -[:SUPPLIES]->
(:CriticalFacility {asset_id, name, facility_type, latitude, longitude})
```

**Topology for Seed Data (10 assets):**
```
SUB-001
  └─[CONTAINS]─> TX-001 ──[FEEDS]──> FD-001 ──[SUPPLIES]──> CF-001 (Hospital)
  └─[CONTAINS]─> TX-002 ──[FEEDS]──> FD-002 ──[SUPPLIES]──> CF-002 (Water Plant)

SUB-002
  └─[CONTAINS]─> TX-003 ──[CONNECTS_TO]──> TX-004
               TX-004 ──[FEEDS]──> FD-003
```
