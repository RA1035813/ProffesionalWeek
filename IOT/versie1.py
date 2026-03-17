#!/usr/bin/env python3
 
import smbus2
import time
import struct
import wiringpi
import requests
import logging
import datetime
import json

# ---------------- SETUP ----------------
 
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("SensorNode")

BH1750_ADDR = 0x23
BMP280_ADDR = 0x77
 
# API CONFIG
SERVER_URL = "http://100.97.118.123:8000/readings/"
NODE_ID = "OPi_Node_01" # Make sure this exists in the 'farm_nodes' table

bus = smbus2.SMBus(0)
 
# Moisture sensor (Pin 8 = WiringPi pin 3)
MOISTURE_PIN = 3
 
wiringpi.wiringPiSetup()
wiringpi.pinMode(MOISTURE_PIN, 0)  # INPUT
 
calib = {}
 
# ---------------- BH1750 ----------------
 
def read_light():
    try:
        data = bus.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        return (data[0] << 8 | data[1]) / 1.2
    except:
        return None
 
# ---------------- BMP280 ----------------
 
def init_bmp280():
    bus.write_byte_data(BMP280_ADDR, 0xF4, 0x27)
    time.sleep(0.2)
    read_calibration()
 
def read_calibration():
    calib['T1'] = bus.read_word_data(BMP280_ADDR, 0x88)
    calib['T2'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8A, 2)))[0]
    calib['T3'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8C, 2)))[0]
 
def read_temperature():
    try:
        data = bus.read_i2c_block_data(BMP280_ADDR, 0xFA, 3)
        raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
 
        var1 = (((raw / 16384.0) - (calib['T1'] / 1024.0)) * calib['T2'])
        var2 = ((((raw / 131072.0) - (calib['T1'] / 8192.0)) ** 2) * calib['T3'])
 
        return (var1 + var2) / 5120.0
    except:
        return None
 
# ---------------- MOISTURE ----------------
 
def read_moisture():
    value = wiringpi.digitalRead(MOISTURE_PIN)
 
    # Adjust if reversed
    if value == 0:
        return "WET"
    else:
        return "DRY"
 
# ---------------- HTTP DELIVERY ----------------

def send_data_http(temp, lux, soil):
    """
    Sends sensor data to the FastAPI server over Tailscale.
    Includes error handling for network/VPN interruptions.
    """
    # Map raw sensor values to the FastAPI Schema (SensorReadingCreate)
    # Note: Using placeholders for NPK and pH as they aren't measured by current hardware
    payload = {
        "id": int(time.time()), # Schema requires an explicit ID
        "node_id": NODE_ID,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "moisture_pct": 80.0 if soil == "WET" else 15.0,
        "ph": 6.5,
        "nitrogen_mg_kg": 0,
        "phosphorus_mg_kg": 0,
        "potassium_mg_kg": 0,
        "soil_temp_c": round(temp, 2) if temp else 0.0,
        "air_temp_c": round(temp, 2) if temp else 0.0,
        "air_humid_pct": 50.0 # Placeholder
    }

    try:
        log.info(f"Attempting to send data to {SERVER_URL}...")
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        
        # Raise an exception for 4xx/5xx responses
        response.raise_for_status()
        
        log.info(f"Successfully sent data! Server responded with status {response.status_code}")
        return True

    except requests.exceptions.ConnectionError:
        log.error("Network Error: Could not connect to the server. Is Tailscale connected?")
    except requests.exceptions.Timeout:
        log.error("Network Error: Connection timed out.")
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP Error: Server returned an error: {e}")
    except Exception as e:
        log.error(f"Unexpected Error: {e}")
    
    return False

# ---------------- MAIN ----------------
 
try:
    log.info("Initializing sensors...")
    init_bmp280()
    log.info("System ready!\n")
 
    while True:
        temp = read_temperature()
        lux = read_light()
        soil = read_moisture()
 
        print("------ SENSOR DATA ------")
        print("Temperature: {:.2f} C".format(temp) if temp else "Temp: ERROR")
        print("Light: {:.2f} lx".format(lux) if lux else "Light: ERROR")
        print("Soil:", soil)
        print("-------------------------\n")

        # Send data via HTTP
        send_data_http(temp, lux, soil)
 
        # Wait for next cycle
        time.sleep(10) # Increased interval slightly for network stability
 
except KeyboardInterrupt:
    log.info("Stopping...")
 
finally:
    bus.close()
    log.info("Closed. Bye!")
