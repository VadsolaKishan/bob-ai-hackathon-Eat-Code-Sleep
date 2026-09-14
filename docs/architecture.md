# GridPulse AI — System Architecture

**GridPulse AI** is a predictive maintenance and power outage mitigation platform built for electric utilities. It fuses substation sensor telemetry, dissolved gas analysis (DGA), severe weather forecasts, and graph-based cascade failure simulations to deliver AI-driven risk advisories and emergency crew dispatch plans.

---

## 1. System Architecture

```mermaid
flowchart TD
    %% Styling
    classDef client fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef backend fill:#0f172a,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef data fill:#022c22,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef ai fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#f8fafc;

    %% Data Inputs
    subgraph INPUTS["External Data Sources"]
        SENSORS["📡 Substation SCADA<br/>Temp, Vibration, DGA Gases"]:::client
        WEATHER["🌩️ Meteorological Feeds<br/>Wind, Lightning, Heatwave"]:::client
    end

    %% Frontend UI
    subgraph UI["Operator Control Room (React 18 + Vite)"]
        WEB["📊 Single-Page Application (SPA)<br/>Dashboard • Grid Topology • Risk Matrix • Crew Staging • AI Copilot"]:::client
    end

    %% FastAPI Backend
    subgraph CORE["Backend Gateway & Engines (FastAPI)"]
        API["⚡ FastAPI Application Server"]:::backend
        DGA["🔬 IEEE C57 DGA Engine<br/>Rogers Ratios & Health Index"]:::backend
        RISK["⚖️ Multi-Factor Risk Correlator<br/>Failure Prob + Weather Stress"]:::backend
        CASCADE["🕸️ Graph Cascade Analyzer<br/>BFS Impact on Hospitals & Water"]:::backend
    end

    %% Storage
    subgraph STORAGE["Persistence Layer"]
        PG[("🐘 PostgreSQL 15<br/>Telemetry, Assets, Work Orders")]:::data
        NEO[("🔷 Neo4j 5<br/>Grid Network Topology Graph")]:::data
    end

    %% AI
    subgraph AI_LAYER["AI Reasoning Layer"]
        GRANITE["🧠 IBM watsonx.ai (Granite)<br/>Natural Language Diagnostics & Runbooks"]:::ai
        LOCAL_AI["🛡️ Deterministic Rule-Based Fallback"]:::ai
    end

    %% Data Flow Connections
    SENSORS & WEATHER -->|"REST / Ingestion"| API
    WEB <-->|"HTTP / JSON REST APIs"| API

    API --> DGA
    API --> RISK
    API --> CASCADE

    DGA & CASCADE --> RISK

    RISK <-->|"SQLAlchemy Async"| PG
    CASCADE <-->|"Cypher Queries (Bolt)"| NEO

    RISK -->|"Asset Context"| GRANITE
    RISK -.->|"Offline Fallback"| LOCAL_AI
    GRANITE & LOCAL_AI --> API
```

---

## 2. End-to-End Prediction Pipeline

```mermaid
flowchart LR
    classDef step fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;

    A["1. Sensor & Weather Ingestion"]:::step --> B["2. IEEE C57 Health Index (0-100)"]:::step
    B --> C["3. Neo4j Cascade Propagation"]:::step
    C --> D["4. Composite Outage Risk Score"]:::step
    D --> E["5. IBM Granite Advisory & Crew Staging"]:::step
```

---

## 3. Technology Stack

| Layer | Technologies | Role |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite, Chart.js | Responsive operator dashboard & interactive grid schematic |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic v2 | High-concurrency async REST API and calculation engines |
| **Relational DB** | PostgreSQL 15, SQLAlchemy Async | Stores time-series telemetry, DGA samples, assets, and work orders |
| **Graph DB** | Neo4j 5, Cypher (Async Driver) | Models transmission network topology & cascade failure propagation |
| **AI / Foundation Model** | IBM watsonx.ai + IBM Granite | Generates explainable root-cause briefs and mitigation runbooks |
| **Testing & Deployment** | Pytest (157 tests), Docker Compose | Fully automated test suite and containerized orchestration |

---

## 4. Risk Engine Formula

$$\text{Base Risk} = 0.30 \times P_f + 0.20 \times \text{HI}_{\text{risk}} + 0.15 \times W_{\text{risk}} + 0.20 \times \text{Grid}_{\text{impact}} + 0.15 \times \text{Cascade}_{\text{risk}}$$

$$\text{Final Risk Score} = \min\left(1.0, \text{Base Risk} \times \text{Critical Multiplier}\right)$$

- **Normal Asset**: $\times 1.0$
- **Important Infrastructure**: $\times 1.2$
- **Critical Facility** *(Hospital, Water Treatment, Airport)*: $\times 1.5$

---

## 5. Key API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **System** | `GET` | `/api/v1/health` | Health check for PostgreSQL, Neo4j, and watsonx |
| **Overview** | `GET` | `/api/v1/dashboard` | Fleet risk KPIs, critical alerts, and weather status |
| **Assets & Risk** | `GET` | `/api/v1/assets` | Monitored transformer fleet with health and risk ranks |
| **Topology** | `GET` | `/api/v1/grid/topology` | Full grid single-line schematic and GIS layout |
| **Cascade** | `GET` | `/api/v1/grid/assets/{id}/impact` | Real-time graph cascade failure simulation |
| **Weather** | `GET` | `/api/v1/weather/crew-preposition` | 48-Hour field crew staging and hub pre-positioning |
| **AI Advisory** | `POST` | `/api/v1/advisory` | Asset-specific IEEE DGA diagnosis and runbook |
| **AI Chat** | `POST` | `/api/v1/advisory/chat` | Context-aware natural language copilot |
| **Work Orders** | `GET` | `/api/v1/workorders` | Open and completed maintenance work orders |
