"""
GridPulse AI — SQLAlchemy Risk, WorkOrder, and AIAdvisory Models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.app.database.postgres import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    failure_probability = Column(Float, nullable=False)
    asset_health_risk = Column(Float, nullable=False)
    weather_risk = Column(Float, nullable=False)
    grid_impact = Column(Float, nullable=False)
    cascade_risk = Column(Float, nullable=False)
    critical_multiplier = Column(Float, nullable=False, default=1.0)
    final_risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)

    asset = relationship("Asset", back_populates="risk_scores")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    assigned_crew = Column(String(100), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    description = Column(String(500), nullable=False)

    asset = relationship("Asset", back_populates="work_orders")


class AIAdvisory(Base):
    __tablename__ = "ai_advisories"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    question = Column(String(500), nullable=False)
    response = Column(String(5000), nullable=False)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    asset = relationship("Asset", back_populates="advisories")
