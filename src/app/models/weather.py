"""
GridPulse AI — SQLAlchemy Weather Reading Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.app.database.postgres import Base


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    wind_speed = Column(Float, default=0.0)
    rainfall = Column(Float, default=0.0)
    lightning_probability = Column(Float, default=0.0)
    flood_risk = Column(Float, default=0.0)
    temperature = Column(Float, default=25.0)

    asset = relationship("Asset", back_populates="weather_readings")
