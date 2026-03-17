import os
import requests
import logging
import time
import datetime
from sqlalchemy.orm import Session
from . import models, schemas
import serial

log = logging.getLogger("soilsms.integration")

def get_weather(lat, lon):
    """Haal 7-daagse voorspelling op van Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("daily", {})
    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {}

def generate_ai_advice(sensor_data, weather_data):
    """Genereert AI-advies gebaseerd op sensor data en weersvoorspelling."""
    USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "true").lower() == "true"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
    
    # Load system prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "systemprompt.md")
    if not os.path.exists(prompt_path):
        prompt_path = "systemprompt.md" # Fallback
    
    try:
        with open(prompt_path, "r") as f:
            system_prompt = f.read()
    except Exception as e:
        log.error(f"Failed to read systemprompt.md: {e}")
        system_prompt = "You are an agronomist assistant. Provide brief soil advice."

    ai_model = "LocalAI" if USE_LOCAL_AI else f"OpenRouter/{OPENROUTER_MODEL}"
    
    if USE_LOCAL_AI:
        try:
            # We assume localAI is in the PYTHONPATH or current dir
            # In Docker, we will ensure it's copied.
            from localAI.local_inference import get_local_ai_advice
            return get_local_ai_advice(sensor_data, weather_data), ai_model
        except ImportError:
            log.error("localAI.local_inference not found. Falling back to simple advice.")
            return "Soil PH is low. Add lime.", ai_model
        except Exception as e:
            log.error(f"Local AI Error: {e}")
            return "Error: Local AI failed.", ai_model

    # OpenRouter Logic
    try:
        user_prompt = f"Sensors: {sensor_data}\nForecast: {weather_data}\nAdvice:"
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 200,
            },
            timeout=30,
        )
        resp.raise_for_status()
        advice = resp.json()["choices"][0]["message"]["content"].strip()
        return advice[:600], ai_model # Allowed up to 600 chars as per systemprompt.md
    except Exception as e:
        log.error(f"AI Generation failed: {e}")
        return "Please check your soil and weather manually.", ai_model

def send_sms(phone_number, message):
    """Verstuurt SMS via modem, Africa's Talking of httpSMS."""
    SMS_MODE = os.getenv("SMS_MODE", "modem")
    if SMS_MODE == "modem":
        GSM_PORT = os.getenv("GSM_PORT", "/dev/ttyAMA0")
        try:
            # Simple serial logic (like in SimCardSMSapi.py)
            ser = serial.Serial(GSM_PORT, 9600, timeout=5)
            ser.write(b"AT+CMGF=1\r\n")
            time.sleep(1)
            ser.write(f'AT+CMGS="{phone_number}"\r\n'.encode())
            time.sleep(0.5)
            ser.write((message + chr(26)).encode())
            time.sleep(3)
            ser.close()
            log.info(f"SMS Sent via Modem to {phone_number}")
            return True
        except Exception as e:
            log.error(f"Modem SMS failed: {e}")
            return False
    elif SMS_MODE == "africas_talking":
        try:
            from SMS.CloudSMSapi import send_via_africas_talking
            return send_via_africas_talking(phone_number, message)
        except ImportError:
            log.error("SMS.CloudSMSapi not found.")
            return False
        except Exception as e:
            log.error(f"AT SMS failed: {e}")
            return False
    elif SMS_MODE == "httpsms":
        API_KEY = os.getenv("httpsms_api_key", "").strip()
        FROM_NUMBER = os.getenv("Ward_phone")
        try:
            resp = requests.post(
                "https://api.httpsms.com/v1/messages/send",
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                json={"content": message, "from": FROM_NUMBER, "to": phone_number, "skip_rcs": True},
                timeout=15
            )
            resp.raise_for_status()
            log.info(f"SMS Sent via httpSMS to {phone_number}")
            return True
        except Exception as e:
            log.error(f"httpSMS failed: {e}")
            return False
    return False

def process_reading_and_notify(db_session_factory, reading_id: int):
    """Achtergrond taak om AI advies te genereren en SMS te sturen."""
    db = db_session_factory()
    try:
        # 1. Fetch reading
        reading = db.query(models.SensorReading).filter(models.SensorReading.id == reading_id).first()
        if not reading: 
            log.error(f"Reading {reading_id} not found in background task.")
            return

        # 2. Fetch Node and Farmer
        node = db.query(models.FarmNode).filter(models.FarmNode.node_id == reading.node_id).first()
        if not node: 
            log.error(f"Node {reading.node_id} not found.")
            return
        
        farmer = db.query(models.Farmer).filter(models.Farmer.id == node.farmer_id).first()
        if not farmer: 
            log.error(f"Farmer {node.farmer_id} not found.")
            return

        # 3. Get Weather
        weather = get_weather(float(node.latitude), float(node.longitude))

        # 4. Generate AI Advice
        sensor_data = {
            "moisture_pct": float(reading.moisture_pct),
            "ph": float(reading.ph),
            "nitrogen": reading.nitrogen_mg_kg,
            "phosphorus": reading.phosphorus_mg_kg,
            "potassium": reading.potassium_mg_kg,
            "soil_temp": float(reading.soil_temp_c),
            "air_temp": float(reading.air_temp_c),
            "air_humidity": float(reading.air_humid_pct)
        }
        advice, model_name = generate_ai_advice(sensor_data, weather)

        # 5. Send SMS
        status = "SENT" if send_sms(farmer.phone_number, advice) else "FAILED"

        # 6. Save Advisory
        advisory_id = int(time.time() * 1000)
        advisory = models.Advisory(
            id=advisory_id,
            reading_id=reading_id,
            ai_model=model_name,
            message_content=advice,
            sent_at=datetime.datetime.utcnow(),
            status=status
        )
        db.add(advisory)
        db.commit()
        log.info(f"Advisory {advisory_id} saved for node {node.node_id} with status {status}")
    except Exception as e:
        log.error(f"Error in process_reading_and_notify: {e}")
        db.rollback()
    finally:
        db.close()
