"""
GridPulse AI — Application Configuration
Loads all environment variables using pydantic-settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # App settings
    app_name: str = "GridPulse AI"
    app_version: str = "2.0.0"
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://gridpulse:gridpulse_secret@localhost:5432/gridpulse",
        alias="DATABASE_URL"
    )
    postgres_user: str = Field(default="gridpulse", alias="POSTGRES_USER")
    postgres_password: str = Field(default="gridpulse_secret", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="gridpulse", alias="POSTGRES_DB")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="gridpulse_neo4j", alias="NEO4J_PASSWORD")

    # IBM watsonx.ai
    watsonx_api_key: str = Field(default="", alias="WATSONX_API_KEY")
    watsonx_project_id: str = Field(default="", alias="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        alias="WATSONX_URL"
    )
    watsonx_model_id: str = Field(
        default="ibm/granite-13b-instruct-v2",
        alias="WATSONX_MODEL_ID"
    )

    # Risk engine weights (configurable)
    weight_failure_probability: float = 0.30
    weight_asset_health: float = 0.20
    weight_weather: float = 0.15
    weight_grid_impact: float = 0.20
    weight_cascade: float = 0.15

    # Critical multipliers
    multiplier_normal: float = 1.0
    multiplier_important: float = 1.2
    multiplier_critical: float = 1.5

    # Risk thresholds
    threshold_low_max: float = 0.39
    threshold_medium_max: float = 0.69
    threshold_high_max: float = 0.84

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
