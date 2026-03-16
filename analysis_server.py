#!/usr/bin/env python3
"""
SoilSMS - Analysis Server
Receives sensor data via SMS, fetches weather predictions,
runs AI-powered soil + crop analysis, replies to farmer via SMS.

Stack:
  - Flask web server (optional webhook for hosted SMS APIs like Africa's Talking)
  - Alternatively: GSM modem on server via AT commands (same GSMModem class)
  - Open-Meteo API for weather (free, no key required)
  - Anthropic Claude for agronomic analysis

Install:
  pip install flask requests anthropic pyserial

Environment variables:
  ANTHROPIC_API_KEY      - Claude API key
  AT_API_KEY             - Africa's Talking API key (if using AT SMS gateway)
  AT_USERNAME            - Africa's Talking username
  SMS_MODE               - "modem" or "africas_talking" (default: modem)
  SERVER_LAT             - Farm latitude for weather (e.g. -6.3)
  SERVER_LON             - Farm longitude (e.g. 34.8)
  FARMER_PHONE           - Farmer's phone number to reply to
  GSM_PORT               - Serial port if SMS_MODE=modem (default /dev/ttyAMA0)
"""

import os
import json
import time
import logging
import requests
import serial
import anthropic
from flask import Flask, request, jsonify
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/soilsms_server.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("soilsms.server")

app = Flask(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
AT_API_KEY        = os.environ.get("AT_API_KEY", "")
AT_USERNAME       = os.environ.get("AT_USERNAME", "")
SMS_MODE          = os.environ.get("SMS_MODE", "modem")       # modem | africas_talking
FARM_LAT          = float(os.environ.get("SERVER_LAT", "-6.3"))
FARM_LON          = float(os.environ.get("SERVER_LON", "34.8"))
FARMER_PHONE      = os.environ.get("FARMER_PHONE", "+255YYYYYYYYY")
GSM_PORT          = os.environ.get("GSM_PORT", "/dev/ttyAMA0")

# ─── WEATHER ─────────────────────────────────────────────────────────────────

def get_weather_forecast(lat: float, lon: float) -> dict:
    """
    Fetch 7-day weather forecast from Open-Meteo (free, no API key).
    Returns a condensed summary suitable for agronomic analysis.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "et0_fao_evapotranspiration",
            "windspeed_10m_max",
        ],
        "forecast_days": 7,
        "timezone": "Africa/Dar_es_Salaam",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("daily", {})

        days = []
        for i in range(7):
            days.append({
                "date":       data["time"][i],
                "temp_max_c": data["temperature_2m_max"][i],
                "temp_min_c": data["temperature_2m_min"][i],
                "rain_mm":    data["precipitation_sum"][i],
                "et0_mm":     data["et0_fao_evapotranspiration"][i],
                "wind_kmh":   data["windspeed_10m_max"][i],
            })

        total_rain = sum(d["rain_mm"] for d in days)
        avg_temp   = sum((d["temp_max_c"] + d["temp_min_c"]) / 2 for d in days) / 7
        total_et0  = sum(d["et0_mm"] for d in days)

        return {
            "forecast_days": days,
            "summary": {
                "total_rain_mm_7d":    round(total_rain, 1),
                "avg_temp_c_7d":       round(avg_temp, 1),
                "total_et0_mm_7d":     round(total_et0, 1),
                "water_balance_mm_7d": round(total_rain - total_et0, 1),
            }
        }

    except Exception as e:
        log.error(f"Weather fetch failed: {e}")
        return {"error": str(e)}

# ─── AI ANALYSIS ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an agronomist assistant helping smallholder farmers in rural Tanzania.
You receive soil sensor data and weather forecast data, then produce a practical SMS-friendly report.

Output rules:
- Write in plain English only (no markdown, no bullet symbols, no emojis)
- Be concise — total output must fit in 3-4 SMS messages (max 600 characters total)
- Structure: STATUS | NUTRIENTS | ACTION | PLANT | TIMING
- Speak directly to the farmer ("Your soil...", "You should...")
- Prioritize the most critical actions first
- Consider local Tanzanian crops: maize, cassava, sorghum, beans, groundnuts, sunflower, rice, vegetables
- If data values are null/missing, note that sensor reading failed and advise re-check
- Always end with a short timing recommendation for planting or treatment

NPK interpretation reference (mg/kg):
  Nitrogen:    Low <100, Medium 100-200, High >200
  Phosphorus:  Low <25, Medium 25-50, High >50
  Potassium:   Low <100, Medium 100-200, High >200

pH interpretation:
  <5.5 = too acidic, 5.5-7.0 = good, 7.0-8.5 = alkaline, >8.5 = too alkaline

Moisture interpretation:
  <20% = very dry, 20-40% = dry, 40-70% = good, >70% = waterlogged"""

def analyze_with_claude(sensor_data: dict, weather: dict) -> str:
    """Send data to Claude for agronomic analysis."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = f"""SOIL SENSOR READING (node {sensor_data.get('node_id', 'unknown')}):
Moisture: {sensor_data.get('moisture_pct')}%
pH: {sensor_data.get('ph')}
Soil temperature: {sensor_data.get('soil_temp_c')} C
Air temperature: {sensor_data.get('air_temp_c')} C
Air humidity: {sensor_data.get('air_humid_pct')}%
Nitrogen: {sensor_data.get('nitrogen_mg_kg')} mg/kg
Phosphorus: {sensor_data.get('phosphorus_mg_kg')} mg/kg
Potassium: {sensor_data.get('potassium_mg_kg')} mg/kg

7-DAY WEATHER FORECAST SUMMARY:
Total expected rain: {weather.get('summary', {}).get('total_rain_mm_7d')} mm
Average temperature: {weather.get('summary', {}).get('avg_temp_c_7d')} C
Total evapotranspiration: {weather.get('summary', {}).get('total_et0_mm_7d')} mm
Water balance (rain minus evaporation): {weather.get('summary', {}).get('water_balance_mm_7d')} mm

Provide your agronomic assessment and recommendations."""

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return message.content[0].text
    except Exception as e:
        log.error(f"Claude API error: {e}")
        return f"Analysis failed: {e}. Raw data sent: pH={sensor_data.get('ph')}, moisture={sensor_data.get('moisture_pct')}%, N={sensor_data.get('nitrogen_mg_kg')} P={sensor_data.get('phosphorus_mg_kg')} K={sensor_data.get('potassium_mg_kg')}"

# ─── SMS SENDING ─────────────────────────────────────────────────────────────

class GSMModem:
    """Identical modem class to RPi node — reusable for server-side modem."""
    def __init__(self, port: str, baud: int = 9600):
        self.port = port
        self.baud = baud
        self.ser  = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=5)
            time.sleep(2)
            self.ser.write(b"AT\r\n"); time.sleep(1); self.ser.read_all()
            self.ser.write(b"AT+CMGF=1\r\n"); time.sleep(1); self.ser.read_all()
            log.info("Server GSM modem ready")
            return True
        except Exception as e:
            log.error(f"Server modem connect failed: {e}")
            return False

    def send_sms(self, number: str, message: str) -> bool:
        chunks = [message[i:i+155] for i in range(0, len(message), 155)]
        for chunk in chunks:
            try:
                self.ser.write(f'AT+CMGS="{number}"\r\n'.encode())
                time.sleep(0.5)
                self.ser.write((chunk + chr(26)).encode())
                time.sleep(3)
                resp = self.ser.read_all().decode(errors="replace")
                if "+CMGS:" not in resp:
                    log.error(f"SMS chunk failed: {resp!r}")
                    return False
            except Exception as e:
                log.error(f"send_sms error: {e}")
                return False
        return True

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

def send_via_africas_talking(to: str, message: str) -> bool:
    """Send SMS via Africa's Talking API (alternative to local modem)."""
    chunks = [message[i:i+155] for i in range(0, len(message), 155)]
    for chunk in chunks:
        try:
            resp = requests.post(
                "https://api.africastalking.com/version1/messaging",
                headers={
                    "apiKey": AT_API_KEY,
                    "Accept": "application/json",
                },
                data={
                    "username": AT_USERNAME,
                    "to":       to,
                    "message":  chunk,
                },
                timeout=10
            )
            data = resp.json()
            if data.get("SMSMessageData", {}).get("Recipients", [{}])[0].get("status") != "Success":
                log.error(f"AT SMS failed: {data}")
                return False
        except Exception as e:
            log.error(f"Africa's Talking error: {e}")
            return False
    return True

def send_reply_sms(to: str, message: str) -> bool:
    if SMS_MODE == "africas_talking":
        return send_via_africas_talking(to, message)
    else:
        modem = GSMModem(GSM_PORT)
        if modem.connect():
            result = modem.send_sms(to, message)
            modem.disconnect()
            return result
        return False

# ─── CORE PIPELINE ───────────────────────────────────────────────────────────

def process_sensor_sms(raw_message: str, sender_phone: str):
    """
    Full pipeline:
    1. Parse JSON from SMS
    2. Fetch weather
    3. Analyse with Claude
    4. Reply to farmer
    """
    log.info(f"Processing SMS from {sender_phone}: {raw_message[:80]}...")

    # 1. Parse sensor JSON
    try:
        sensor_data = json.loads(raw_message)
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in SMS: {e}")
        send_reply_sms(FARMER_PHONE, f"ERROR: Could not read sensor data. Please check node {sender_phone}.")
        return

    # 2. Fetch weather
    log.info("Fetching weather forecast...")
    weather = get_weather_forecast(FARM_LAT, FARM_LON)
    if "error" in weather:
        log.warning("Weather fetch failed, continuing without it")
        weather = {"summary": {}, "forecast_days": []}

    # 3. AI analysis
    log.info("Running Claude analysis...")
    analysis = analyze_with_claude(sensor_data, weather)

    # 4. Compose and send reply
    timestamp = datetime.utcnow().strftime("%d/%m %H:%M")
    full_reply = f"SoilSMS {timestamp} UTC\n{analysis}"

    log.info(f"Sending reply to {FARMER_PHONE} ({len(full_reply)} chars)")
    success = send_reply_sms(FARMER_PHONE, full_reply)

    if success:
        log.info("Reply sent successfully")
    else:
        log.error("Failed to send reply to farmer")

# ─── FLASK WEBHOOK (for Africa's Talking incoming SMS) ───────────────────────

@app.route("/sms/incoming", methods=["POST"])
def incoming_sms_webhook():
    """
    Africa's Talking incoming SMS webhook.
    POST fields: from, to, text, date, id, linkId
    """
    sender  = request.form.get("from", "")
    message = request.form.get("text", "")

    if not message:
        return jsonify({"status": "error", "detail": "empty message"}), 400

    process_sensor_sms(message, sender)
    return jsonify({"status": "ok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "mode": SMS_MODE}), 200

# ─── MODEM POLLING MODE (if no webhook available) ────────────────────────────

def poll_modem_for_sms(modem: GSMModem):
    """
    Poll GSM modem for incoming SMS messages.
    Used when SMS_MODE=modem and no webhook is available.
    """
    log.info("Polling modem for incoming SMS...")
    modem.ser.write(b'AT+CMGL="ALL"\r\n')
    time.sleep(2)
    resp = modem.ser.read_all().decode(errors="replace")

    if "+CMGL:" not in resp:
        return

    # Parse SMS entries: +CMGL: index,status,sender,...\r\ntext\r\n
    lines = resp.split("\r\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("+CMGL:"):
            parts = lines[i].split(",")
            sender = parts[2].strip().strip('"') if len(parts) > 2 else "unknown"
            text   = lines[i+1] if i+1 < len(lines) else ""
            if text.strip().startswith("{"):
                process_sensor_sms(text.strip(), sender)
            i += 2
        else:
            i += 1

    # Delete all read messages to free SIM storage
    modem.ser.write(b'AT+CMGD=1,4\r\n')
    time.sleep(1)
    modem.ser.read_all()

def run_modem_mode():
    """Run server in modem polling mode (no webhook)."""
    modem = GSMModem(GSM_PORT)
    if not modem.connect():
        log.critical("Cannot connect to server GSM modem. Halting.")
        return

    log.info("Server running in modem polling mode (checking every 60s)")
    while True:
        try:
            poll_modem_for_sms(modem)
        except Exception as e:
            log.error(f"Poll error: {e}", exc_info=True)
        time.sleep(60)

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if SMS_MODE == "africas_talking":
        log.info("Starting Flask webhook server on :5000 (Africa's Talking mode)")
        app.run(host="0.0.0.0", port=5000)
    else:
        log.info("Starting in modem polling mode")
        run_modem_mode()