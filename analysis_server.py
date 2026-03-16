import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.server")

app = Flask(__name__)

# --- CONFIG ---
# Ensure your GEMINI_API_KEY is in a .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Requirement 4: The System Prompt
SYSTEM_PROMPT = """You are an expert tropical agronomist helping smallholder farmers in Tanzania.
Analyze the provided soil sensor data and 7-day weather forecast.
Output ONLY a direct, actionable SMS advisory in Swahili (or simple English if needed).
Max 160 characters. No jargon, no intro, no polite greetings.
Focus on: watering, fertilizing, or crop rotation based on NPK and pH.
Example: 'Udongo ni mkavu. Mvua inakuja kesho. Subiri kupanda mahindi wiki ijayo. Ongeza mbolea ya DAP.'"""

def get_weather(lat, lon):
    """Fetch 7-day forecast from Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("daily", {})
    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {}

def generate_ai_advice(sensor_data, weather_data):
    """Uses Gemini to generate the 160-char SMS advisory."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        user_prompt = f"Sensors: {sensor_data}\nForecast: {weather_data}\nAdvice:"
        
        # Combining system prompt and user data
        response = model.generate_content(SYSTEM_PROMPT + "\n\n" + user_prompt)
        
        # Ensure we don't exceed SMS length
        advice = response.text.strip()
        return advice[:160]
    except Exception as e:
        log.error(f"AI Generation failed: {e}")
        return "Bora uongeze mbolea kidogo na usubiri mvua wiki ijayo."

@app.route('/api/data', methods=['POST'])
def handle_incoming_data():
    """Receives data from Farm Node (via HTTP for prototype)."""
    try:
        payload = request.json
        node_id = payload.get("node_id")
        farmer_phone = payload.get("farmer_id")
        lat = payload["location"]["lat"]
        lon = payload["location"]["lon"]
        sensors = payload["sensors"]
        
        log.info(f"Data received from Node {node_id} (Farmer: {farmer_phone})")
        
        # 1. Fetch Weather
        weather = get_weather(lat, lon)
        
        # 2. Generate Advice
        advice = generate_ai_advice(sensors, weather)
        
        # 3. Send SMS (Simulated for prototype)
        # In production, this would call Twilio or a local GSM modem
        log.info(f"*** FINAL ADVISORY SENT TO {farmer_phone} ***")
        log.info(f"SMS: {advice}")
        
        return jsonify({
            "status": "success",
            "advisory": advice,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        log.error(f"Server error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"}), 200

if __name__ == "__main__":
    log.info("SoilSMS Analysis Server Started on :5000")
    app.run(host="0.0.0.0", port=5000)
