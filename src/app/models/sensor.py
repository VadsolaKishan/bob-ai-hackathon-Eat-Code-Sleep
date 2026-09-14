"""
GridPulse AI — SQLAlchemy Sensor & DGA Models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.app.database.postgres import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    partial_discharge = Column(Float, nullable=False)

    asset = relationship("Asset", back_populates="sensor_readings")


class DGAReading(Base):
    __tablename__ = "dga_readings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    h2 = Column(Float, default=0.0)
    ch4 = Column(Float, default=0.0)
    c2h2 = Column(Float, default=0.0)
    c2h4 = Column(Float, default=0.0)
    c2h6 = Column(Float, default=0.0)
    co = Column(Float, default=0.0)
    co2 = Column(Float, default=0.0)

    asset = relationship("Asset", back_populates="dga_readings")
