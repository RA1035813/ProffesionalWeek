from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database
from .database import engine, SessionLocal
from .integration import process_reading_and_notify

# Create tables if they don't exist
# Note: In production, you'd use migrations like Alembic
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoilSMS Logging API",
    docs_url="/docsMischienHandigMischienNIET"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to SoilSMS Logging API"}

# Farmers
@app.post("/farmers/", response_model=schemas.Farmer)
def create_farmer(farmer: schemas.FarmerCreate, db: Session = Depends(database.get_db)):
    db_farmer = db.query(models.Farmer).filter(models.Farmer.id == farmer.id).first()
    if db_farmer:
        # Update existing farmer if information changed
        db_farmer.phone_number = farmer.phone_number
        db_farmer.name = farmer.name
        db.commit()
        db.refresh(db_farmer)
        return db_farmer

    db_farmer = models.Farmer(**farmer.dict())
    db.add(db_farmer)
    db.commit()
    db.refresh(db_farmer)
    return db_farmer

@app.get("/farmers/", response_model=List[schemas.Farmer])
def read_farmers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    farmers = db.query(models.Farmer).offset(skip).limit(limit).all()
    return farmers

# Farm Nodes
@app.post("/nodes/", response_model=schemas.FarmNode)
def create_node(node: schemas.FarmNodeCreate, db: Session = Depends(database.get_db)):
    db_node = db.query(models.FarmNode).filter(models.FarmNode.node_id == node.node_id).first()
    if db_node:
        # Update existing node (location or crop type)
        db_node.latitude = node.latitude
        db_node.longitude = node.longitude
        db_node.crop_type = node.crop_type
        db_node.farmer_id = node.farmer_id
        db.commit()
        db.refresh(db_node)
        return db_node

    db_node = models.FarmNode(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node

@app.get("/nodes/", response_model=List[schemas.FarmNode])
def read_nodes(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    nodes = db.query(models.FarmNode).offset(skip).limit(limit).all()
    return nodes

# Sensor Readings
@app.post("/readings/", response_model=schemas.SensorReading)
def create_reading(reading: schemas.SensorReadingCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    db_reading = models.SensorReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    # Trigger AI analysis and SMS notification in background
    # We pass SessionLocal to create a new session in the background thread
    background_tasks.add_task(process_reading_and_notify, SessionLocal, db_reading.id)
    
    return db_reading

@app.get("/readings/", response_model=List[schemas.SensorReading])
def read_readings(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    readings = db.query(models.SensorReading).offset(skip).limit(limit).all()
    return readings

# Weather Logs
@app.post("/weather/", response_model=schemas.WeatherLog)
def create_weather(weather: schemas.WeatherLogCreate, db: Session = Depends(database.get_db)):
    db_weather = models.WeatherLog(**weather.dict())
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather

# Advisories
@app.post("/advisories/", response_model=schemas.Advisory)
def create_advisory(advisory: schemas.AdvisoryCreate, db: Session = Depends(database.get_db)):
    db_advisory = models.Advisory(**advisory.dict())
    db.add(db_advisory)
    db.commit()
    db.refresh(db_advisory)
    return db_advisory

@app.get("/health")
def health_check():
    return {"status": "ok"}
