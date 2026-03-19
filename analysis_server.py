import os
import re
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Importeer de lokale AI logica
from localAI.local_inference import get_local_ai_advice

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.server")

app = Flask(__name__)

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

# --- CONFIG ---
# ZET DIT OP TRUE OM OLLAMA/MISTRAL TE GEBRUIKEN, FALSE VOOR OPENROUTER
USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "true").lower() == "true"

# OpenRouter config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert tropical agronomist helping smallholder farmers in Tanzania.
Analyze the provided soil sensor data and 7-day weather forecast.
Output ONLY a direct, actionable SMS advisory in English.
Max 160 characters. No jargon, no intro, no polite greetings.
Focus on: watering, fertilizing, or crop rotation based on NPK and pH.
Example: 'Soil is dry. Rain is expected tomorrow. Delay maize planting by one week. Add a small amount of DAP fertilizer.'"""

def mask_phone(phone: str) -> str:
    """Mask phone number for safe logging (M5)."""
    if not phone or len(phone) < 6:
        return "***"
    return phone[:4] + "***" + phone[-3:]

def validate_sensor_value(value, min_val, max_val) -> bool:
    """Check that a sensor value is numeric and within expected range."""
    try:
        v = float(value)
        return min_val <= v <= max_val
    except (TypeError, ValueError):
        return False

def get_weather(lat, lon):
    """Haal 7-daagse voorspelling op van Open-Meteo."""
    # Validate coordinates (H5)
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        log.error("Invalid lat/lon type")
        return {}
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        log.error(f"Coordinates out of range: lat={lat}, lon={lon}")
        return {}

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("daily", {})
    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {}

def generate_ai_advice(sensor_data, weather_data):
    """Kiest tussen Lokale AI (Ollama) of OpenRouter API."""
    if USE_LOCAL_AI:
        log.info("Gebruik maken van LOKALE AI (Ollama/Mistral)...")
        return get_local_ai_advice(sensor_data, weather_data)

    try:
        log.info(f"Gebruik maken van OPENROUTER ({OPENROUTER_MODEL})...")
        user_prompt = f"Sensors: {sensor_data}\nForecast: {weather_data}\nAdvice:"

        resp = requests.post(
            OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "SoilSMS Server",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 200,
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        advice = data["choices"][0]["message"]["content"].strip()
        return advice[:160]
    except Exception as e:
        log.error(f"OpenRouter API Error: {e}")
        return "Bora uongeze mbolea kidogo na usubiri mvua wiki ijayo."

@app.route('/api/data', methods=['POST'])
def handle_incoming_data():
    """Ontvang data van de Farm Node (via HTTP voor prototype)."""
    try:
        payload = request.json
        if not payload or not isinstance(payload, dict):
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        node_id = payload.get("node_id")
        farmer_phone = payload.get("farmer_id")

        # Validate location (H4, H5)
        location = payload.get("location")
        if not isinstance(location, dict) or "lat" not in location or "lon" not in location:
            return jsonify({"status": "error", "message": "Missing location data"}), 400

        lat = location["lat"]
        lon = location["lon"]

        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid coordinate format"}), 400

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({"status": "error", "message": "Coordinates out of range"}), 400

        sensors = payload.get("sensors")
        if not isinstance(sensors, dict):
            return jsonify({"status": "error", "message": "Missing or invalid sensors data"}), 400

        # Validate sensor values are numeric (H4, M4)
        for key, value in sensors.items():
            if value is not None:
                try:
                    float(value)
                except (TypeError, ValueError):
                    return jsonify({"status": "error", "message": f"Sensor '{key}' must be numeric"}), 400

        log.info(f"Data ontvangen van Node {node_id} (Boer: {mask_phone(farmer_phone)})")

        # 1. Haal Weer op
        weather = get_weather(lat, lon)

        # 2. Genereer Advies (Lokaal of Cloud)
        advice = generate_ai_advice(sensors, weather)

        # 3. Log het resultaat (Simulatie van SMS verzenden)
        log.info(f"*** FINALE SMS VERZONDEN NAAR {mask_phone(farmer_phone)} ***")
        log.info(f"Advisory generated ({len(advice)} chars)")

        return jsonify({
            "status": "success",
            "mode": "LocalAI" if USE_LOCAL_AI else f"OpenRouter/{OPENROUTER_MODEL}",
            "advisory": advice,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        log.error(f"Server error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "local_ai_enabled": USE_LOCAL_AI,
        "openrouter_model": OPENROUTER_MODEL if not USE_LOCAL_AI else None
    }), 200

if __name__ == "__main__":
    mode = "LocalAI (Ollama)" if USE_LOCAL_AI else f"OpenRouter ({OPENROUTER_MODEL})"
    log.info(f"SoilSMS Analysis Server Gestart op :5000 (Mode: {mode})")
    app.run(host="0.0.0.0", port=5000)
