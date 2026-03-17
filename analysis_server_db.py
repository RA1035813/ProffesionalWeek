import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Importeer de lokale AI logica
from localAI.local_inference import get_local_ai_advice
# Importeer de database handler
from database_handler import DatabaseHandler

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.server")

app = Flask(__name__)
db = DatabaseHandler()

# --- CONFIG ---
USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "true").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert tropical agronomist helping smallholder farmers in Tanzania.
Analyze the provided soil sensor data and 7-day weather forecast.
Output ONLY a direct, actionable SMS advisory in Swahili (or simple English if needed).
Max 160 characters. No jargon, no intro, no polite greetings.
Focus on: watering, fertilizing, or crop rotation based on NPK and pH.
Example: 'Udongo ni mkavu. Mvua inakuja kesho. Subiri kupanda mahindi wiki iyayo. Ongeza mbolea ya DAP.'"""

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("daily", {})
    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {}

def generate_ai_advice(sensor_data, weather_data):
    ai_model = "LocalAI (Ollama/Mistral)" if USE_LOCAL_AI else f"OpenRouter ({OPENROUTER_MODEL})"
    
    if USE_LOCAL_AI:
        log.info("Gebruik maken van LOKALE AI (Ollama/Mistral)...")
        return get_local_ai_advice(sensor_data, weather_data), ai_model

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
        return advice[:160], ai_model
    except Exception as e:
        log.error(f"OpenRouter API Error: {e}")
        return "Bora uongeze mbolea kidogo na usubiri mvua wiki ijayo.", ai_model

@app.route('/api/data', methods=['POST'])
def handle_incoming_data():
    try:
        payload = request.json
        node_id = payload.get("node_id")
        farmer_phone = payload.get("farmer_id")
        lat = payload["location"]["lat"]
        lon = payload["location"]["lon"]
        sensors = payload["sensors"]

        log.info(f"Data ontvangen van Node {node_id} (Boer: {farmer_phone})")

        # 1. Zorg dat boer en node in DB staan
        db.ensure_farmer_and_node(farmer_phone, node_id, lat, lon)

        # 2. Haal Weer op
        weather = get_weather(lat, lon)

        # 3. Genereer Advies (Lokaal of Cloud)
        advice, model_used = generate_ai_advice(sensors, weather)

        # 4. Log alles in de Database
        db.log_reading(node_id, sensors, weather, advice, model_used)

        log.info(f"*** FINALE SMS VERZONDEN NAAR {farmer_phone} ***")
        log.info(f"INHOUD: {advice}")

        return jsonify({
            "status": "success",
            "mode": model_used,
            "advisory": advice,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        log.error(f"Server error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "db_connected": db.connect() # Check connection
    }), 200

if __name__ == "__main__":
    db.connect()
    app.run(host="0.0.0.0", port=5000)
