"""
GridPulse AI — SQLAlchemy Incident Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.app.database.postgres import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    failure_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500), nullable=False)

    asset = relationship("Asset", back_populates="incidents")
