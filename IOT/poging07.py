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
BASE_URL = "http://100.97.118.123:8000"
SERVER_URL = BASE_URL + "/readings/"
NODE_ID = "OPi_Node_01"
FARMER_ID = 1

bus = smbus2.SMBus(0)

# Moisture sensor (Pin 8 = WiringPi pin 3)
MOISTURE_PIN = 3
wiringpi.wiringPiSetup()
wiringpi.pinMode(MOISTURE_PIN, 0)  # INPUT

calib = {}

# ---------------- DATABASE PREPARATION ----------------

def provision_database():
    """Zorgt dat Boer en Node bestaan om Foreign Key errors op de server te voorkomen."""
    log.info("Database controleren op VM...")
    
    # 1. Maak boer aan
    try:
        requests.post(BASE_URL + "/farmers/", json={
            "id": FARMER_ID,
            "phone_number": "+32493882886",
            "name": "OrangePi User"
        }, timeout=5)
    except:
        pass

    # 2. Maak node aan
    try:
        requests.post(BASE_URL + "/nodes/", json={
            "node_id": NODE_ID,
            "farmer_id": FARMER_ID,
            "latitude": 51.0,
            "longitude": 3.0,
            "crop_type": "OrangePi_Garden"
        }, timeout=5)
    except:
        pass

# ---------------- BH1750 (Licht) ----------------

def read_light():
    try:
        data = bus.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        return (data[0] << 8 | data[1]) / 1.2
    except Exception as e:
        log.error("Fout bij lezen BH1750: " + str(e))
        return None

# ---------------- BMP280 (Temperatuur) ----------------

def init_bmp280():
    try:
        bus.write_byte_data(BMP280_ADDR, 0xF4, 0x27)
        time.sleep(0.2)
        read_calibration()
    except Exception as e:
        log.error("Fout bij init BMP280: " + str(e))

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
    except Exception as e:
        log.error("Fout bij lezen BMP280: " + str(e))
        return None

# ---------------- MOISTURE (Bodem) ----------------

def read_moisture():
    value = wiringpi.digitalRead(MOISTURE_PIN)
    if value == 0:
        return "WET"
    else:
        return "DRY"

# ---------------- HTTP DELIVERY ----------------

def send_data_http(temp, lux, soil):
    """Verstuurt data naar FastAPI met correcte schema-mapping."""
    payload = {
        "node_id": NODE_ID,
        "timestamp": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "moisture_pct": 80.0 if soil == "WET" else 15.0,
        "ph": 6.5,
        "nitrogen_mg_kg": 0,
        "phosphorus_mg_kg": 0,
        "potassium_mg_kg": 0,
        "soil_temp_c": round(temp, 2) if temp else 0.0,
        "air_temp_c": round(temp, 2) if temp else 0.0,
        "air_humid_pct": 50.0
    }

    try:
        log.info("Verzenden naar " + SERVER_URL + "...")
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            log.info("Succes! Status: " + str(response.status_code))
            return True
        else:
            log.error("Server Fout " + str(response.status_code) + ": " + response.text)
            return False

    except Exception as e:
        log.error("Netwerkfout: " + str(e))
        return False

# ---------------- MAIN ----------------

if __name__ == "__main__":
    try:
        log.info("Systeem start op...")
        init_bmp280()
        provision_database()
        log.info("System ready!\n")

        while True:
            temp = read_temperature()
            lux = read_light()
            soil = read_moisture()

            print("------ SENSOR DATA ------")
            print("Temperature: {:.2f} C".format(temp) if temp else "Temp: ERROR")
            print("Light: {:.2f} lx".format(lux) if lux else "Light: ERROR")
            print("Soil: " + soil)
            print("-------------------------\n")

            # Verstuur naar API
            send_data_http(temp, lux, soil)

            # Wacht 10 seconden voor de volgende cyclus
            time.sleep(10)

    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        bus.close()
        log.info("Closed. Bye!")
