from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, BigInteger, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    nodes = relationship("FarmNode", back_populates="farmer")

class FarmNode(Base):
    __tablename__ = "farm_nodes"

    node_id = Column(String(255), primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    latitude = Column(Numeric(8, 2), nullable=False)
    longitude = Column(Numeric(8, 2), nullable=False)
    crop_type = Column(String(255), nullable=True)
    installed_at = Column(DateTime, default=datetime.datetime.utcnow)

    farmer = relationship("Farmer", back_populates="nodes")
    readings = relationship("SensorReading", back_populates="node")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(BigInteger, primary_key=True, index=True)
    node_id = Column(String(255), ForeignKey("farm_nodes.node_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    moisture_pct = Column(Numeric(8, 2), nullable=False)
    ph = Column(Numeric(8, 2), nullable=False)
    nitrogen_mg_kg = Column(Integer, nullable=False)
    phosphorus_mg_kg = Column(Integer, nullable=False)
    potassium_mg_kg = Column(Integer, nullable=False)
    soil_temp_c = Column(Numeric(8, 2), nullable=False)
    air_temp_c = Column(Numeric(8, 2), nullable=False)
    air_humid_pct = Column(Numeric(8, 2), nullable=False)

    node = relationship("FarmNode", back_populates="readings")
    weather = relationship("WeatherLog", back_populates="reading")
    advisories = relationship("Advisory", back_populates="reading")

class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    reading_id = Column(BigInteger, ForeignKey("sensor_readings.id"), nullable=False)
    forecast_rain_7d_mm = Column(Numeric(8, 2), nullable=False)
    forecast_avg_temp_c = Column(Numeric(8, 2), nullable=False)

    reading = relationship("SensorReading", back_populates="weather")

class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(BigInteger, primary_key=True, index=True)
    reading_id = Column(BigInteger, ForeignKey("sensor_readings.id"), nullable=False)
    ai_model = Column(String(255), nullable=False)
    message_content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(255), nullable=False)

    reading = relationship("SensorReading", back_populates="advisories")
