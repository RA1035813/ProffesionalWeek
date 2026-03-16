import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Importeer de lokale AI logica
from localAI.local_inference import get_local_ai_advice

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.server")

app = Flask(__name__)

# --- CONFIG ---
# ZET DIT OP TRUE OM OLLAMA/MISTRAL TE GEBRUIKEN, FALSE VOOR GEMINI
USE_LOCAL_AI = True 

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Requirement 4: De Systeem Prompt (ook gebruikt voor Gemini)
SYSTEM_PROMPT = """You are an expert tropical agronomist helping smallholder farmers in Tanzania.
Analyze the provided soil sensor data and 7-day weather forecast.
Output ONLY a direct, actionable SMS advisory in Swahili (or simple English if needed).
Max 160 characters. No jargon, no intro, no polite greetings.
Focus on: watering, fertilizing, or crop rotation based on NPK and pH.
Example: 'Udongo ni mkavu. Mvua inakuja kesho. Subiri kupanda mahindi wiki iyayo. Ongeza mbolea ya DAP.'"""

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
    """Kiest tussen Lokale AI (Ollama) of Gemini API."""
    if USE_LOCAL_AI:
        log.info("Gebruik maken van LOKALE AI (Ollama/Mistral)...")
        return get_local_ai_advice(sensor_data, weather_data)
    
    try:
        log.info("Gebruik maken van GEMINI CLOUD AI...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        user_prompt = f"Sensors: {sensor_data}\nForecast: {weather_data}\nAdvice:"
        response = model.generate_content(SYSTEM_PROMPT + "\n\n" + user_prompt)
        advice = response.text.strip()
        return advice[:160]
    except Exception as e:
        log.error(f"Gemini API Error: {e}")
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
            "mode": "LocalAI" if USE_LOCAL_AI else "Gemini",
            "advisory": advice,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        log.error(f"Server error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running", "local_ai_enabled": USE_LOCAL_AI}), 200

if __name__ == "__main__":
    log.info(f"SoilSMS Analysis Server Gestart op :5000 (LocalAI={USE_LOCAL_AI})")
    app.run(host="0.0.0.0", port=5000)
