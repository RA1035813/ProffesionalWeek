from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class FarmerBase(BaseModel):
    phone_number: str
    name: str

class FarmerCreate(FarmerBase):
    id: int

class Farmer(FarmerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FarmNodeBase(BaseModel):
    node_id: str
    farmer_id: int
    latitude: Decimal
    longitude: Decimal
    crop_type: Optional[str] = None

class FarmNodeCreate(FarmNodeBase):
    pass

class FarmNode(FarmNodeBase):
    installed_at: datetime

    class Config:
        from_attributes = True

class SensorReadingBase(BaseModel):
    id: int
    node_id: str
    timestamp: datetime
    moisture_pct: Decimal
    ph: Decimal
    nitrogen_mg_kg: int
    phosphorus_mg_kg: int
    potassium_mg_kg: int
    soil_temp_c: Decimal
    air_temp_c: Decimal
    air_humid_pct: Decimal

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReading(SensorReadingBase):
    class Config:
        from_attributes = True

class WeatherLogBase(BaseModel):
    id: int
    reading_id: int
    forecast_rain_7d_mm: Decimal
    forecast_avg_temp_c: Decimal

class WeatherLogCreate(WeatherLogBase):
    pass

class WeatherLog(WeatherLogBase):
    class Config:
        from_attributes = True

class AdvisoryBase(BaseModel):
    id: int
    reading_id: int
    ai_model: str
    message_content: str
    sent_at: datetime
    status: str

class AdvisoryCreate(AdvisoryBase):
    pass

class Advisory(AdvisoryBase):
    class Config:
        from_attributes = True
