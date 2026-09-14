# GridPulse AI — Setup Guide

## Prerequisites

- Docker 24+ and Docker Compose V2
- OR: Python 3.11+, Node.js 20+, PostgreSQL 15, Neo4j 5

---

## Quick Start with Docker (Recommended)

### 1. Clone and Configure

```bash
git clone https://github.com/ThummarDarshan/bob-ai-hackathon-Eat-Code-Sleep.git
cd bob-ai-hackathon-Eat-Code-Sleep

# Create .env from template
cp .env.example .env

# Edit .env and add your IBM watsonx.ai credentials (optional)
# Leave WATSONX_API_KEY blank to use the local fallback AI
```

### 2. Start All Services

```bash
docker compose up --build
```

This will:
1. Start PostgreSQL (port 5432)
2. Start Neo4j (ports 7474 HTTP, 7687 Bolt)
3. Seed the database with sample data
4. Start the FastAPI backend (port 8000)
5. Build and serve the React frontend (port 3000)

### 3. Access the Application

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:3000 |
| API Documentation | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Health Check | http://localhost:8000/api/v1/health |

---

## Manual Setup (Development)

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database URLs

# Start PostgreSQL and Neo4j (via Docker or locally)
docker run -d --name gridpulse_pg -e POSTGRES_USER=gridpulse -e POSTGRES_PASSWORD=gridpulse_secret -e POSTGRES_DB=gridpulse -p 5432:5432 postgres:15
docker run -d --name gridpulse_neo4j -e NEO4J_AUTH=neo4j/gridpulse_neo4j -p 7474:7474 -p 7687:7687 neo4j:5-community

# Seed the database
python -m src.app.database.seed

# Start the backend
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at http://localhost:3000 and proxies `/api` to http://localhost:8000.

---

## Seeding the Neo4j Grid

After starting the backend, seed the Neo4j grid topology by calling:

```bash
curl -X POST http://localhost:8000/api/v1/grid/seed
```

Or it runs automatically on startup if the grid is empty.

---

## IBM watsonx.ai Configuration

The system works **without** watsonx credentials using the local rule-based fallback. To enable IBM Granite:

1. Get your IBM Cloud API key
2. Create a watsonx.ai project and get the project ID
3. Add to `.env`:
   ```
   WATSONX_API_KEY=your-key
   WATSONX_PROJECT_ID=your-project-id
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
   ```

The health endpoint shows current watsonx status: `GET /api/v1/health`

---

## Running Tests

```bash
# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_risk.py -v

# Run with coverage
pytest --cov=src/app --cov-report=term-missing
```

---

## Project Structure

```
GridPulse_AI/
├── frontend/              # React + TypeScript frontend
│   ├── src/pages/         # 8 pages (Dashboard, Assets, Risk, Grid, Weather, Crew, AI)
│   ├── src/components/    # RiskBadge, AssetCard, Charts, AdvisorChat...
│   └── src/services/api.ts # All API calls
│
├── src/app/
│   ├── main.py            # FastAPI app with lifespan
│   ├── core/              # Risk engine, graph scoring, watsonx, advisory
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic v2 schemas
│   ├── routes/            # FastAPI routers
│   ├── services/          # PostgresService, Neo4jService, IntegrationAdapters
│   └── database/          # Postgres + Neo4j drivers + seed script
│
├── seeds/                 # JSON seed data (assets, telemetry, DGA, weather, incidents, work orders)
├── tests/                 # Pytest test suite
├── alembic/               # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── CONTRACT.md            # Full API contract & schemas
└── .env.example
```
