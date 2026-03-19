import os
import json
import requests
import pandas as pd
import logging
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Ensure project root is in sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SMS.sms_handler import send_sms
from FastAPI import database, models, integration

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
log = logging.getLogger("soilsms.incoming")

# Sessions to track the user's last choice: { 'phone_number': 'choice' }
user_sessions = {}

# ── Geocoding Logic ───────────────────────────────────────────────────────────
def get_coords(location_name):
    """Convert a city name to latitude and longitude."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1&language=en&format=json"
    try:
        res = requests.get(url).json()
        if "results" in res:
            result = res["results"][0]
            return result["latitude"], result["longitude"], result["name"]
    except Exception as e:
        log.error(f"Geocoding error: {e}")
    return None, None, None

# ── Weather Logic ─────────────────────────────────────────────────────────────
def get_weather_data(lat, lon, days=1):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,rain",
        "forecast_days": days,
        "timezone": "auto",
    }
    try:
        response = requests.get(url, params=params).json()
        df = pd.DataFrame({
            "time_local": pd.to_datetime(response['hourly']['time']),
            "temp": response['hourly']['temperature_2m'],
            "rain": response['hourly']['rain']
        })
        return df
    except Exception as e:
        log.error(f"Weather data error: {e}")
        return None

def format_weather_sms(df, title, location_name):
    if df is None: 
        return "⚠️ Error retrieving weather data."
    
    sms_lines = [f"🌤️ {title} weather for {location_name}:"]
    current_date = None
    for _, row in df.iloc[::3].iterrows():
        date_str = row['time_local'].strftime('%d/%m/%Y')
        if date_str != current_date:
            sms_lines.append(f"\n📅 {date_str}")
            current_date = date_str
        sms_lines.append(f"{row['time_local'].strftime('%H:%M')} | {row['temp']:.1f}°C | 🌧️ {row['rain']:.1f}mm")
    return "\n".join(sms_lines)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/incoming_sms", methods=["POST"])
def incoming_sms():
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"status": "no payload"}), 400
        
    data = payload.get("data", {})
    
    # Determine sender
    contact = data.get("contact")
    sender = contact if isinstance(contact, str) else contact.get("mobile_number")
    text = (data.get("content") or "").strip()

    if not sender: 
        return jsonify({"status": "no sender"}), 200

    # STEP 2: If the user is in a session (waiting for location)
    if sender in user_sessions:
        choice = user_sessions.pop(sender)  # Get choice and remove session
        lat, lon, city = get_coords(text)
        
        if lat:
            if choice == "1":
                df = get_weather_data(lat, lon, days=1)
                msg = format_weather_sms(df, "Today", city)
            else:  # choice 2
                df = get_weather_data(lat, lon, days=7)
                msg = format_weather_sms(df, "Weekly forecast", city)
        else:
            msg = f"❌ Could not find the location '{text}'. Please try again via the menu."
        
        send_sms(sender, msg)

    # STEP 1: User makes a choice from the menu
    else:
        if text == "1" or text == "2":
            user_sessions[sender] = text  # Remember that we are waiting for a location
            send_sms(sender, "📍 For which city or town do you want the weather?")
        elif text == "3":
            # Real Soil Quality Logic
            db = next(database.get_db())
            try:
                # Find farmer by phone number (match last 9 digits to handle country code variants)
                search_num = sender[-9:]
                farmer = db.query(models.Farmer).filter(models.Farmer.phone_number.contains(search_num)).first()
                if not farmer:
                    send_sms(sender, "❌ Farmer record not found for this number.")
                    return jsonify({"status": "ok"}), 200
                
                # Find latest reading for this farmer's nodes
                node_ids = [node.node_id for node in farmer.nodes]
                reading = db.query(models.SensorReading).filter(models.SensorReading.node_id.in_(node_ids)).order_by(models.SensorReading.timestamp.desc()).first()
                
                if not reading:
                    send_sms(sender, "🌱 No sensor data found for your farm yet.")
                else:
                    # Get Weather
                    node = db.query(models.FarmNode).filter(models.FarmNode.node_id == reading.node_id).first()
                    weather = integration.get_weather(float(node.latitude), float(node.longitude))
                    
                    # Generate Advice
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
                    advice, _ = integration.generate_ai_advice(sensor_data, weather)
                    send_sms(sender, advice)
            except Exception as e:
                log.error(f"Error handling soil quality request: {e}")
                send_sms(sender, "⚠️ Error processing your request. Please try again later.")
            finally:
                db.close()
        else:
            help_msg = "Reply with:\n1️⃣ Today's weather\n2️⃣ Weekly weather\n3️⃣ Soil quality"
            send_sms(sender, help_msg)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
