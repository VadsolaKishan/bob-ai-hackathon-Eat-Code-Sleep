"""
GridPulse AI — Database Seeder
Loads all seed JSON files into PostgreSQL.
Run: python -m src.app.database.seed
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert

from src.app.core.config import settings

SEEDS_DIR = Path(__file__).parent.parent.parent.parent / "seeds"


async def load_json(filename: str) -> list:
    path = SEEDS_DIR / filename
    if not path.exists():
        print(f"Warning: seed file {path} not found, skipping.")
        return []
    with open(path) as f:
        return json.load(f)


def parse_ts(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp string to UTC datetime."""
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)


async def seed_database():
    from src.app.database.postgres import Base
    from src.app.models import asset, sensor, weather, incident, risk  # noqa: register models

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSession_ = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession_() as db:
        await seed_assets(db)
        await seed_telemetry(db)
        await seed_dga(db)
        await seed_weather(db)
        await seed_incidents(db)
        await seed_work_orders(db)
        await db.commit()

    # Seed Neo4j grid if connected
    try:
        from src.app.database.neo4j import get_neo4j_session
        from src.app.services.neo4j_service import Neo4jService
        assets_data = await load_json("assets.json")
        async with get_neo4j_session() as neo4j_session:
            neo4j_svc = Neo4jService(neo4j_session)
            await neo4j_svc.seed_grid(assets_data)
            print("✅ Neo4j grid seeded successfully!")
    except Exception as e:
        print(f"Notice: Neo4j seeding skipped ({e}).")

    # Compute and persist initial risk scores
    try:
        from src.app.core.risk_engine import RiskEngine
        async with AsyncSession_() as db:
            neo4j_svc = None
            try:
                from src.app.database.neo4j import get_neo4j_session
                from src.app.services.neo4j_service import Neo4jService
                async with get_neo4j_session() as neo4j_session:
                    neo4j_svc = Neo4jService(neo4j_session)
            except Exception:
                pass
            risk_engine = RiskEngine(db, neo4j_svc)
            assets_data = await load_json("assets.json")
            print(f"Computing initial risk scores for {len(assets_data)} assets...")
            for a in assets_data:
                try:
                    await risk_engine.compute_risk(a["asset_id"])
                except Exception as e:
                    print(f"Warning computing risk for {a['asset_id']}: {e}")
            await db.commit()
            print("[OK] Initial risk scores computed and saved!")
    except Exception as e:
        print(f"Notice: Initial risk computation skipped ({e}).")

    await engine.dispose()
    print("[OK] Seeding complete!")


async def seed_assets(db: AsyncSession):
    from src.app.models.asset import Asset
    assets = await load_json("assets.json")
    print(f"Seeding {len(assets)} assets...")
    for a in assets:
        existing = await db.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(Asset).where(Asset.asset_id == a["asset_id"])
        )
        if existing.scalar_one_or_none():
            continue
        inst_date = None
        if a.get("installation_date"):
            from datetime import date
            inst_date = date.fromisoformat(a["installation_date"])
        db.add(Asset(
            asset_id=a["asset_id"],
            name=a["name"],
            asset_type=a["asset_type"],
            latitude=a["latitude"],
            longitude=a["longitude"],
            capacity=a.get("capacity"),
            critical_facility=a.get("critical_facility", False),
            facility_type=a.get("facility_type"),
            status=a.get("status", "active"),
            installation_date=inst_date,
        ))
    await db.flush()


async def seed_telemetry(db: AsyncSession):
    from src.app.models.sensor import SensorReading
    rows = await load_json("telemetry.json")
    print(f"Seeding {len(rows)} sensor readings...")
    for r in rows:
        db.add(SensorReading(
            asset_id=r["asset_id"],
            timestamp=parse_ts(r["timestamp"]),
            temperature=r["temperature"],
            vibration=r["vibration"],
            partial_discharge=r["partial_discharge"],
        ))
    await db.flush()


async def seed_dga(db: AsyncSession):
    from src.app.models.sensor import DGAReading
    rows = await load_json("dga.json")
    print(f"Seeding {len(rows)} DGA readings...")
    for r in rows:
        db.add(DGAReading(
            asset_id=r["asset_id"],
            timestamp=parse_ts(r["timestamp"]),
            h2=r.get("h2", 0.0),
            ch4=r.get("ch4", 0.0),
            c2h2=r.get("c2h2", 0.0),
            c2h4=r.get("c2h4", 0.0),
            c2h6=r.get("c2h6", 0.0),
            co=r.get("co", 0.0),
            co2=r.get("co2", 0.0),
        ))
    await db.flush()


async def seed_weather(db: AsyncSession):
    from src.app.models.weather import WeatherReading
    rows = await load_json("weather.json")
    print(f"Seeding {len(rows)} weather readings...")
    for r in rows:
        db.add(WeatherReading(
            asset_id=r["asset_id"],
            timestamp=parse_ts(r["timestamp"]),
            wind_speed=r.get("wind_speed", 0.0),
            rainfall=r.get("rainfall", 0.0),
            lightning_probability=r.get("lightning_probability", 0.0),
            flood_risk=r.get("flood_risk", 0.0),
            temperature=r.get("temperature", 25.0),
        ))
    await db.flush()


async def seed_incidents(db: AsyncSession):
    from src.app.models.incident import Incident
    rows = await load_json("incidents.json")
    print(f"Seeding {len(rows)} incidents...")
    for r in rows:
        db.add(Incident(
            asset_id=r["asset_id"],
            timestamp=parse_ts(r["timestamp"]),
            failure_type=r["failure_type"],
            severity=r["severity"],
            description=r["description"],
        ))
async def seed_work_orders(db: AsyncSession):
    from sqlalchemy import select
    from src.app.models.risk import WorkOrder
    rows = await load_json("work_orders.json")
    print(f"Seeding {len(rows)} work orders...")
    for r in rows:
        existing = await db.execute(
            select(WorkOrder).where(
                WorkOrder.asset_id == r["asset_id"],
                WorkOrder.description == r["description"]
            )
        )
        if not existing.scalar_one_or_none():
            db.add(WorkOrder(
                asset_id=r["asset_id"],
                priority=r["priority"],
                status=r["status"],
                assigned_crew=r.get("assigned_crew"),
                scheduled_time=parse_ts(r.get("scheduled_time")) if r.get("scheduled_time") else None,
                description=r["description"],
            ))
    await db.flush()


if __name__ == "__main__":
    asyncio.run(seed_database())
