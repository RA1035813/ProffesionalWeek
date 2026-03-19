import os
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
        node_id = payload.get("node_id")
        farmer_phone = payload.get("farmer_id")
        lat = payload["location"]["lat"]
        lon = payload["location"]["lon"]
        sensors = payload["sensors"]

        log.info(f"Data ontvangen van Node {node_id} (Boer: {farmer_phone})")

        # 1. Haal Weer op
        weather = get_weather(lat, lon)

        # 2. Genereer Advies (Lokaal of Cloud)
        advice = generate_ai_advice(sensors, weather)

        # 3. Log het resultaat (Simulatie van SMS verzenden)
        log.info(f"*** FINALE SMS VERZONDEN NAAR {farmer_phone} ***")
        log.info(f"INHOUD: {advice}")

        return jsonify({
            "status": "success",
            "mode": "LocalAI" if USE_LOCAL_AI else f"OpenRouter/{OPENROUTER_MODEL}",
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
        "local_ai_enabled": USE_LOCAL_AI,
        "openrouter_model": OPENROUTER_MODEL if not USE_LOCAL_AI else None
    }), 200

if __name__ == "__main__":
    mode = "LocalAI (Ollama)" if USE_LOCAL_AI else f"OpenRouter ({OPENROUTER_MODEL})"
    log.info(f"SoilSMS Analysis Server Gestart op :5000 (Mode: {mode})")
    app.run(host="0.0.0.0", port=5000)
