#!/usr/bin/env python3

import smbus2
import time
import struct
import wiringpi
import requests
import logging
import datetime

# ---------------- CONFIGURATIE ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("SensorNode")

BASE_URL = "http://100.97.118.123:8000"
NODE_ID = "OPi_Node_01"
FARMER_ID = 1

# I2C setup
bus = smbus2.SMBus(0)
BH1750_ADDR = 0x23
BMP280_ADDR = 0x77

# Vochtsensor setup
MOISTURE_PIN = 3
wiringpi.wiringPiSetup()
wiringpi.pinMode(MOISTURE_PIN, 0)

calib = {}

# ---------------- DATABASE PREPARATION ----------------
def provision_database():
    """Zorgt dat Boer en Node bestaan om 500 errors (Foreign Key) te voorkomen."""
    log.info("Database controleren/voorbeiden...")
    
    # 1. Maak boer aan
    try:
        requests.post(f"{BASE_URL}/farmers/", json={
            "id": FARMER_ID,
            "phone_number": "+31600000000",
            "name": "OrangePi User"
        }, timeout=5)
    except:
        pass

    # 2. Maak node aan
    try:
        requests.post(f"{BASE_URL}/nodes/", json={
            "node_id": NODE_ID,
            "farmer_id": FARMER_ID,
            "latitude": 51.0,
            "longitude": 3.0,
            "crop_type": "OrangePi_Garden"
        }, timeout=5)
    except:
        pass

# ---------------- SENSOR READING ----------------
def init_bmp280():
    bus.write_byte_data(BMP280_ADDR, 0xF4, 0x27)
    time.sleep(0.2)
    calib['T1'] = bus.read_word_data(BMP280_ADDR, 0x88)
    calib['T2'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8A, 2)))[0]
    calib['T3'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8C, 2)))[0]

def read_sensors():
    # Temp
    try:
        data = bus.read_i2c_block_data(BMP280_ADDR, 0xFA, 3)
        raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        v1 = (((raw / 16384.0) - (calib['T1'] / 1024.0)) * calib['T2'])
        v2 = ((((raw / 131072.0) - (calib['T1'] / 8192.0)) ** 2) * calib['T3'])
        temp = (v1 + v2) / 5120.0
    except:
        temp = 0.0
    
    # Lux
    try:
        light_data = bus.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        lux = (light_data[0] << 8 | light_data[1]) / 1.2
    except:
        lux = 0.0
    
    # Soil
    soil = "WET" if wiringpi.digitalRead(MOISTURE_PIN) == 0 else "DRY"
    
    return temp, lux, soil

# ---------------- API SENDING ----------------
def send_to_api(temp, lux, soil):
    # Matcht exact met SensorReadingCreate schema
    payload = {
        "id": int(time.time()), 
        "node_id": NODE_ID,
        "timestamp": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "moisture_pct": 80.0 if soil == "WET" else 20.0,
        "ph": 6.5,
        "nitrogen_mg_kg": 0,
        "phosphorus_mg_kg": 0,
        "potassium_mg_kg": 0,
        "soil_temp_c": round(temp, 2),
        "air_temp_c": round(temp, 2),
        "air_humid_pct": 50.0
    }

    try:
        r = requests.post(f"{BASE_URL}/readings/", json=payload, timeout=10)
        if r.status_code in [200, 201]:
            log.info(f"Succes! Data verzonden voor {NODE_ID}")
        else:
            log.error(f"Server Fout {r.status_code}: {r.text}")
    except Exception as e:
        log.error(f"Verbindingsfout: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    try:
        init_bmp280()
        provision_database()
        log.info("Systeem gestart. Start metingen...")
        while True:
            t, l, s = read_sensors()
            print("Meting: {:.1f}C, {:.0f} lux, Bodem: {}".format(t, l, s))
            send_to_api(t, l, s)
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Gestopt door gebruiker.")
    finally:
        bus.close()
