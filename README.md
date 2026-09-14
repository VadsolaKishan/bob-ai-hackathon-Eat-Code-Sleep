# ⚡ GridPulse AI — Power Outage & Grid Equipment Failure Advisor

> Proactive AI-driven resilience copilot for power utilities: fusing substation asset health telemetry with real-time weather analytics to predict catastrophic grid outages and optimize field crew dispatch.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Eat-Code-Sleep |
| **Track** | AI |
| **Team Lead** | Darshan Thummar — darshantce.059@gmail.com |
| **Members** | Shreeja Upadhyay, Kishan Vadsola, Vishv Undavia |

---

## 🎯 Problem Statement

Power transformer and substation failures cost utilities **over $1M/hour** in blackouts, yet most still rely on calendar-based maintenance. Sensor data (temperature, vibration, partial discharge, DGA) already shows failure signatures weeks ahead — but it's never combined with weather forecasts or historical incident records to act in time. The result: predictable catastrophes that nobody predicted.

---

## 💡 Solution

**GridPulse AI** is a predictive maintenance copilot built on **IBM Bob** and **watsonx.ai**. It fuses asset health telemetry, live weather forecasts, and historical failure records into a unified risk model — telling operators which equipment will fail, when, and exactly what to do before it happens.

**What makes it unique:**

- 🧬 **IEEE C57.104 DGA Intelligence** — classifies fault *type* (thermal / arcing / partial discharge) from dissolved gas ratios, not just raw thresholds
- 🌦️ **Storm-Asset Vulnerability Matrix** — cross-references weather severity with each asset's degradation state to compute compounded failure probability hours before landfall
- 📊 **Cascading Failure Graph Scoring** — ranks assets by Neo4j grid topology impact; downstream asset & facility paths dynamically determine grid impact and cascade risk
- 🚁 **48-Hour Crew Pre-Positioning Engine** — stages repair crews at optimal hubs (North Operations Center, East Metro Depot, West Valley Station) before failures occur, cutting MTTR
- 🏥 **Critical Facility Multiplier** — hospitals, water plants, and emergency services are automatically weighted to the top of the operational priority queue
- 🔁 **Historical Incident Context** — cross-references historical failure records, fault recurrence, and maintenance history to provide data-driven operational context in advisories
- 🗣️ **Natural-Language Advisory Interface** — operators ask plain-English questions; system synthesises all data layers into structured operational diagnostics with IBM Granite or deterministic local fallback

---

## ✨ Key Features

- **Asset Health Indexing** — real-time DGA, oil temperature, vibration, and partial discharge scoring (IEEE C57.104)
- **Weather-Risk Fusion** — per-asset failure probability from wind, lightning, flood, and temperature extremes
- **Severity-Ranked Work Orders** — cascading impact + critical facility weighting drives the maintenance queue
- **Pre-emptive Crew Dispatch** — 48-hour staging plan generated before failures, not after
- **Bob & watsonx.ai Copilot** — natural-language root-cause analysis and step-by-step SOPs with deterministic local fallback
- **Historical Incident Tracking** — correlates previous equipment failures and recurrence history with active asset health

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.11+, TypeScript, JavaScript (ES6+), HTML5, CSS3 |
| **Frameworks** | FastAPI, Uvicorn, Pydantic v2, React 18, Vite |
| **IBM Technologies** | IBM watsonx.ai, IBM Granite Models |
| **Data & Storage** | PostgreSQL 15, Neo4j 5 Graph Database, SQLAlchemy Async |
| **Design & Visualization**| Modern Glassmorphic CSS, Mermaid.js, Chart.js / SVG Visualizers |

---

## 📁 Repository Structure

```
├── src/                  # Complete backend API & interactive operational dashboard
│   ├── app/              # FastAPI application core, routes, and risk engines
│   ├── static/           # Responsive operator UI and monitoring views
│   ├── data/             # Asset registry, sensor telemetry, and weather mock streams
│   ├── .env.example      # Environment variable template
│   └── README.md         # Source directory documentation
├── docs/                 # Detailed architectural and operational documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demonstration artifacts
│   ├── screenshots/      # Application screenshots
│   ├── demo-video-link.txt  # Link to walkthrough video
│   └── live-demo-url.txt    # Live deployment status
├── presentation/         # Project slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

### 🐳 Method 1 — Docker (Recommended)

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# 1. Clone the repository
git clone https://github.com/ThummarDarshan/bob-ai-hackathon-Eat-Code-Sleep.git
cd bob-ai-hackathon-Eat-Code-Sleep

# 2. Create your environment file
cp .env.example .env
# Optional: open .env and add your IBM watsonx.ai credentials
# Leave WATSONX_API_KEY blank to use the built-in local heuristic AI fallback

# 3. Build and start all 4 containers (PostgreSQL + Neo4j + FastAPI Backend + React Frontend)
docker compose up --build
```

The startup command automatically creates database schemas and seeds PostgreSQL and Neo4j with asset telemetry, DGA readings, weather risks, and grid topology.

When you see:
```
gridpulse_backend  | INFO:     Application startup complete.
```

The application is ready!

```bash
# Optional: re-run database and Neo4j seeding at any time inside the container:
docker exec gridpulse_backend python -m src.app.database.seed
```

**Access the application:**

| Service | URL | Description |
|---|---|---|
| 🖥️ **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Interactive React operator dashboard |
| 📡 **API Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI documentation |
| ❤️ **Health Check** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Live service & dependency health status |
| 🔍 **Neo4j Browser** | [http://localhost:7474](http://localhost:7474) | Graph visualizer (`neo4j` / `gridpulse_neo4j`) |

```bash
# Stop all services
docker compose down

# Stop and remove all persistent data volumes
docker compose down -v
```

---

### 🛠️ Method 2 — Manual (Local Development)

> **Prerequisites:** Python 3.11+, Node.js 20+, Docker (for databases only)

```bash
# 1. Clone the repository
git clone https://github.com/ThummarDarshan/bob-ai-hackathon-Eat-Code-Sleep.git
cd bob-ai-hackathon-Eat-Code-Sleep

# 2. Start PostgreSQL and Neo4j databases via Docker
docker run -d --name gridpulse_pg \
  -e POSTGRES_USER=gridpulse \
  -e POSTGRES_PASSWORD=gridpulse_secret \
  -e POSTGRES_DB=gridpulse \
  -p 5432:5432 postgres:15

docker run -d --name gridpulse_neo4j \
  -e NEO4J_AUTH=neo4j/gridpulse_neo4j \
  -p 7474:7474 -p 7687:7687 neo4j:5-community

# 3. Set up Python virtual environment
python -m venv venv

# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Configure environment variables
cp .env.example .env
# Edit .env — ensure DATABASE_URL and NEO4J_URI point to localhost

# 6. Seed PostgreSQL and Neo4j with grid topology and telemetry
python -m src.app.database.seed

# 7. Start the FastAPI backend
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 8. In a new terminal — start the React frontend
cd frontend
npm install
npm run dev
```

Frontend available at **http://localhost:3000**, API at **http://localhost:8000/docs**.

---

### 🧪 Run Tests

```bash
# From the project root with your environment active:
pytest -v

# Expected result: 157 passed (100% green)
```

---

### 🔑 IBM watsonx.ai Configuration (Optional)

The system runs fully without watsonx credentials using a built-in rule-based fallback. To enable IBM Granite AI responses:

1. Get your [IBM Cloud API key](https://cloud.ibm.com/iam/apikeys)
2. Create a [watsonx.ai project](https://dataplatform.cloud.ibm.com/) and copy the Project ID
3. Add to `.env`:

```env
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
```

The `/api/v1/health` endpoint shows live watsonx status.

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- **Simulated Grid Telemetry**: Asset sensor metrics and weather feeds simulate real-time SCADA and meteorological APIs for repeatable demonstration environments.
- **Advisory Control**: The system outputs dispatch orders and breaker isolation advisories for human grid operators rather than directly actuating physical substation relays.
- **Offline LLM Fallback**: If an active watsonx.ai API key is not supplied in `.env`, the system automatically defaults to an intelligent local heuristic reasoning engine.

---

## 🏅 What We're Most Proud Of

The integration of the multi-factor risk fusion algorithm that links chemical dissolved gas ratios (IEEE C57.104 DGA standard) directly with approaching weather storm fronts, enabling grid operators to pre-stage emergency response crews hours ahead of line collapse.

---

