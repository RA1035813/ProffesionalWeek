import os
import json
import logging
import requests
import re
from functools import wraps
from flask import Flask, request, jsonify, abort
from datetime import datetime
from dotenv import load_dotenv

# Importeer de lokale AI logica
from localAI.local_inference import get_local_ai_advice

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.server")

app = Flask(__name__)

# --- CONFIG ---
# ZET DIT OP TRUE OM OLLAMA/MISTRAL TE GEBRUIKEN, FALSE VOOR OPENROUTER
USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "true").lower() == "true"
SERVER_API_KEY = os.getenv("SERVER_API_KEY")

# OpenRouter config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert tropical agronomist helping smallholder farmers in Tanzania.
Analyze the provided soil sensor data and 7-day weather forecast.
Output ONLY a direct, actionable SMS advisory in Swahili (or simple English if needed).
Max 160 characters. No jargon, no intro, no polite greetings.
Focus on: watering, fertilizing, or crop rotation based on NPK and pH.
Example: 'Udongo ni mkavu. Mvua inakuja kesho. Subiri kupanda mahindi wiki iyayo. Ongeza mbolea ya DAP.'"""

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SERVER_API_KEY:
            # If no API key is configured, warn but allow for dev (better to enforce in prod)
            log.warning("SERVER_API_KEY not set! Skipping authentication check.")
            return f(*args, **kwargs)
        
        provided_key = request.headers.get("X-API-Key")
        if provided_key != SERVER_API_KEY:
            log.warning(f"Unauthorized access attempt from {request.remote_addr}")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def validate_phone(number):
    """Validate phone number format."""
    if not number: return False
    return bool(re.match(r"^\+?[0-9]{7,15}$", str(number)))

def validate_lat_lon(lat, lon):
    """Validate latitude and longitude ranges."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return -90 <= lat_f <= 90 and -180 <= lon_f <= 180
    except (ValueError, TypeError):
        return False

def get_weather(lat, lon):
    """Haal 7-daagse voorspelling op van Open-Meteo."""
    if not validate_lat_lon(lat, lon):
        log.error(f"Invalid coordinates for weather fetch: {lat}, {lon}")
        return {}

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("daily", {})
    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {}

def generate_ai_advice(sensor_data, weather_data):
    """Kiest tussen Lokale AI (Ollama) of OpenRouter API."""
    # Sanitize sensor data - ensure it's numeric to prevent prompt injection
    sanitized_sensors = {}
    for k, v in sensor_data.items():
        try:
            sanitized_sensors[k] = float(v)
        except (ValueError, TypeError):
            sanitized_sensors[k] = "N/A"

    if USE_LOCAL_AI:
        log.info("Gebruik maken van LOKALE AI (Ollama/Mistral)...")
        return get_local_ai_advice(sanitized_sensors, weather_data)

    try:
        log.info(f"Gebruik maken van OPENROUTER ({OPENROUTER_MODEL})...")
        user_prompt = f"Sensors: {sanitized_sensors}\nForecast: {weather_data}\nAdvice:"

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
@require_api_key
def handle_incoming_data():
    """Ontvang data van de Farm Node (via HTTP voor prototype)."""
    try:
        payload = request.json
        if not payload:
            return jsonify({"status": "error", "message": "Missing payload"}), 400
            
        node_id = payload.get("node_id")
        farmer_phone = payload.get("farmer_id")
        location = payload.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")
        sensors = payload.get("sensors")

        if not all([node_id, farmer_phone, lat is not None, lon is not None, sensors]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        if not validate_phone(farmer_phone):
            return jsonify({"status": "error", "message": "Invalid phone format"}), 400

        if not validate_lat_lon(lat, lon):
            return jsonify({"status": "error", "message": "Invalid location"}), 400

        # Mask phone in logs for privacy
        masked_phone = f"{farmer_phone[:4]}***{farmer_phone[-3:]}" if len(farmer_phone) > 7 else farmer_phone
        log.info(f"Data ontvangen van Node {node_id} (Boer: {masked_phone})")

        # 1. Haal Weer op
        weather = get_weather(lat, lon)

        # 2. Genereer Advies (Lokaal of Cloud)
        advice = generate_ai_advice(sensors, weather)

        # 3. Log het resultaat (Simulatie van SMS verzenden)
        log.info(f"*** FINALE SMS VERZONDEN NAAR {masked_phone} ***")
        log.info(f"INHOUD: {advice}")

        return jsonify({
            "status": "success",
            "mode": "LocalAI" if USE_LOCAL_AI else f"OpenRouter/{OPENROUTER_MODEL}",
            "advisory": advice,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        log.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

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
    # In production, use a WSGI server like Gunicorn
    app.run(host="0.0.0.0", port=5000)
