"""
GridPulse AI — SQLAlchemy Asset Model
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.app.database.postgres import Base
import enum


class AssetTypeEnum(str, enum.Enum):
    transformer = "transformer"
    substation = "substation"
    feeder = "feeder"
    critical_facility = "critical_facility"


class AssetStatusEnum(str, enum.Enum):
    active = "active"
    maintenance = "maintenance"
    offline = "offline"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SAEnum(AssetTypeEnum), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Float, nullable=True)
    critical_facility = Column(Boolean, default=False)
    facility_type = Column(String(50), nullable=True)
    status = Column(SAEnum(AssetStatusEnum), default=AssetStatusEnum.active)
    installation_date = Column(Date, nullable=True)

    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="asset", cascade="all, delete-orphan")
    dga_readings = relationship("DGAReading", back_populates="asset", cascade="all, delete-orphan")
    weather_readings = relationship("WeatherReading", back_populates="asset", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="asset", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="asset", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="asset", cascade="all, delete-orphan")
    advisories = relationship("AIAdvisory", back_populates="asset", cascade="all, delete-orphan")
