"""
GridPulse AI — FastAPI Application Entry Point
Power Grid Equipment Risk Advisor powered by IBM watsonx + Granite
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from src.app.core.config import settings
from src.app.database.postgres import init_db, close_db
from src.app.database.neo4j import init_neo4j, close_neo4j

# Routers
from src.app.routes.assets import router as assets_router
from src.app.routes.risk import router as risk_router
from src.app.routes.grid import router as grid_router
from src.app.routes.weather import router as weather_router
from src.app.routes.advisory import router as advisory_router
from src.app.routes.recommendations import router as recommendations_router
from src.app.routes.dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup and shutdown."""
    logger.info("GridPulse AI starting up...")

    # Initialize PostgreSQL
    try:
        await init_db()
        logger.info("PostgreSQL connected and tables ready.")
    except Exception as e:
        logger.warning(f"PostgreSQL initialization warning: {e}")

    # Initialize Neo4j
    try:
        await init_neo4j()
        logger.info("Neo4j connected.")
    except Exception as e:
        logger.warning(f"Neo4j initialization warning: {e}")

    yield

    # Shutdown
    logger.info("GridPulse AI shutting down...")
    try:
        await close_db()
    except Exception:
        pass
    try:
        await close_neo4j()
    except Exception:
        pass


app = FastAPI(
    title="GridPulse AI",
    description="Power Grid Equipment Risk Advisor powered by IBM watsonx + Granite",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "error_type": "INTERNAL_SERVER_ERROR"
        }
    )


# Include all routers under /api/v1
API_PREFIX = "/api/v1"

app.include_router(assets_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
app.include_router(grid_router, prefix=API_PREFIX)
app.include_router(weather_router, prefix=API_PREFIX)
app.include_router(advisory_router, prefix=API_PREFIX)
app.include_router(recommendations_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "service": "GridPulse AI — Power Grid Equipment Risk Advisor",
        "version": settings.app_version,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": API_PREFIX,
    }


@app.api_route("/health", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route(f"{API_PREFIX}/health", methods=["GET", "HEAD"])
async def health_check():
    """Service health check with dependency status."""
    from src.app.database.postgres import get_postgres_status
    from src.app.database.neo4j import get_neo4j_status
    from src.app.core.watsonx_integration import WatsonxClient
    from src.app.core.config import settings as cfg

    pg_status = await get_postgres_status()
    neo4j_status = await get_neo4j_status()

    wx_client = WatsonxClient(
        api_key=cfg.watsonx_api_key,
        project_id=cfg.watsonx_project_id,
        url=cfg.watsonx_url,
        model_id=cfg.watsonx_model_id
    )
    watsonx_status = "available" if wx_client.is_available() else "unavailable (using local fallback)"

    overall = "healthy" if pg_status == "connected" else "degraded"

    return {
        "status": overall,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "postgres": pg_status,
            "neo4j": neo4j_status,
            "watsonx": watsonx_status,
        }
    }
