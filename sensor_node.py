import time
import json
import random
import requests
import logging

# --- CONFIGURATION ---
SIMULATE = True          # Set to False when running on actual RPi
USE_HTTP = True          # Use HTTP POST for local testing instead of SMS
SERVER_URL = "http://127.0.0.1:5000/api/data"
FARMER_PHONE = "+255712345678"
NODE_ID = "DEMO_NODE_001"
READ_INTERVAL = 60       # Seconds between readings for prototype

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("soilsms.node")

def read_sensors():
    """Simulates reading from NPK, pH, Moisture, and Temp sensors."""
    if SIMULATE:
        log.info("Simulating sensor readings...")
        return {
            "moisture_pct": round(random.uniform(15, 65), 1),
            "ph": round(random.uniform(5.0, 8.5), 2),
            "nitrogen_mg_kg": random.randint(50, 250),
            "phosphorus_mg_kg": random.randint(10, 60),
            "potassium_mg_kg": random.randint(50, 250),
            "soil_temp_c": round(random.uniform(22, 32), 1),
            "air_temp_c": round(random.uniform(25, 38), 1),
            "air_humid_pct": round(random.uniform(30, 80), 1)
        }
    else:
        # In actual production, this would call the I2C/UART libraries
        return {
            "moisture_pct": 0, "ph": 7.0, "nitrogen_mg_kg": 0,
            "phosphorus_mg_kg": 0, "potassium_mg_kg": 0,
            "soil_temp_c": 0, "air_temp_c": 0, "air_humid_pct": 0
        }

def send_data_http(data):
    """Sends data via HTTP POST for local prototype testing."""
    payload = {
        "node_id": NODE_ID,
        "farmer_id": FARMER_PHONE,
        "location": {"lat": -6.7924, "lon": 39.2083},
        "sensors": data
    }
    try:
        log.info(f"Sending HTTP POST to {SERVER_URL}...")
        resp = requests.post(SERVER_URL, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log.error(f"HTTP Delivery failed: {e}")
        return False

def main():
    log.info(f"SoilSMS Node {NODE_ID} Started (Simulate={SIMULATE})")
    while True:
        data = read_sensors()
        log.info(f"New Data: {data}")
        
        if USE_HTTP:
            success = send_data_http(data)
        else:
            log.info("GSM Mode: SMS sending skipped in local simulation.")
            success = True
        
        if success:
            log.info("Transmission complete.")
        
        log.info(f"Sleeping for {READ_INTERVAL}s...")
        time.sleep(READ_INTERVAL)

if __name__ == "__main__":
    main()
