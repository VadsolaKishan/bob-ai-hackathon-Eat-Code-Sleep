"""
Shared test fixtures and configuration for GridPulse AI tests.
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy async session."""
    db = AsyncMock()
    return db


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j session."""
    session = AsyncMock()
    return session
