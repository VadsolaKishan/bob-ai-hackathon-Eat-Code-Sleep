"""
GridPulse AI — Neo4j Async Database Driver
"""
from neo4j import AsyncGraphDatabase, AsyncDriver
from contextlib import asynccontextmanager
import logging

from src.app.core.config import settings

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None


async def init_neo4j():
    """Initialize Neo4j async driver."""
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    # Verify connectivity
    await _driver.verify_connectivity()
    logger.info(f"Neo4j connected to {settings.neo4j_uri}")


async def close_neo4j():
    """Close Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


def get_driver() -> AsyncDriver:
    """Return the Neo4j driver instance."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
    return _driver


@asynccontextmanager
async def get_neo4j_session():
    """Async context manager that provides a Neo4j session."""
    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        yield session


async def get_neo4j_status() -> str:
    """Check Neo4j connectivity."""
    try:
        driver = get_driver()
        await driver.verify_connectivity()
        return "connected"
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")
        return "disconnected"
