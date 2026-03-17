import os
import json
import requests
import pandas as pd
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
API_KEY     = os.getenv("httpsms_api_key", "").strip()
FROM_NUMBER = os.getenv("Ward_phone")

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
        print(f"Geocoding error: {e}")
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
    except:
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

# ── SMS helper ────────────────────────────────────────────────────────────────
def send_sms(to: str, body: str):
    requests.post(
        "https://api.httpsms.com/v1/messages/send",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        data=json.dumps({"content": body, "from": FROM_NUMBER, "to": to, "skip_rcs": True}),
    )

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/incoming_sms", methods=["POST"])
def incoming_sms():
    payload = request.get_json(force=True, silent=True)
    data = payload.get("data", {})
    
    # Determine sender
    contact = data.get("contact")
    sender = contact if isinstance(contact, str) else contact.get("mobile_number")
    text = (data.get("content") or "").strip()

    if not sender: 
        return jsonify({"status": "ok"}), 200

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
            send_sms(sender, "🌱 Soil quality: pH 6.5, moisture good (Location-independent)")
        else:
            help_msg = "Reply with:\n1️⃣ Today's weather\n2️⃣ Weekly weather\n3️⃣ Soil quality"
            send_sms(sender, help_msg)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)