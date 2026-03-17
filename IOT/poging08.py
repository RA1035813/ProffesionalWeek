#!/usr/bin/env python3

import smbus2
import time
import struct
import wiringpi
import requests
import logging
import datetime

# ---------------- CONFIGURATIE ----------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("SensorNode")

# VM IP over Tailscale
BASE_URL = "http://100.97.118.123:8000"
SERVER_URL = BASE_URL + "/readings/"
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
    """Zorgt dat de Boer en Node bestaan om Foreign Key errors te voorkomen."""
    log.info("Check/Create Farmer & Node op server...")
    
    # 1. Boer
    try:
        requests.post(BASE_URL + "/farmers/", json={
            "id": FARMER_ID,
            "phone_number": "+31699999999",
            "name": "OrangePi_User"
        }, timeout=5)
    except:
        pass

    # 2. Node
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

# ---------------- SENSOR READING ----------------

def init_bmp280():
    try:
        bus.write_byte_data(BMP280_ADDR, 0xF4, 0x27)
        time.sleep(0.2)
        calib['T1'] = bus.read_word_data(BMP280_ADDR, 0x88)
        calib['T2'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8A, 2)))[0]
        calib['T3'] = struct.unpack('<h', bytes(bus.read_i2c_block_data(BMP280_ADDR, 0x8C, 2)))[0]
    except Exception as e:
        log.error("BMP280 Init Fout: " + str(e))

def read_sensors():
    # Temperatuur
    try:
        data = bus.read_i2c_block_data(BMP280_ADDR, 0xFA, 3)
        raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        v1 = (((raw / 16384.0) - (calib['T1'] / 1024.0)) * calib['T2'])
        v2 = ((((raw / 131072.0) - (calib['T1'] / 8192.0)) ** 2) * calib['T3'])
        temp = (v1 + v2) / 5120.0
    except:
        temp = 0.0
    
    # Licht
    try:
        light_data = bus.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        lux = (light_data[0] << 8 | light_data[1]) / 1.2
    except:
        lux = 0.0
    
    # Vocht
    soil = "WET" if wiringpi.digitalRead(MOISTURE_PIN) == 0 else "DRY"
    
    return temp, lux, soil

# ---------------- HTTP DELIVERY ----------------

def send_data_http(temp, lux, soil):
    # Unieke ID op basis van milliseconden
    reading_id = int(time.time() * 1000)
    
    # Gebruik de tijd van de Orange Pi (zorg dat deze op 'date' klopt!)
    # We sturen een ISO string die de FastAPI/SQLAlchemy goed kan parsen
    now_iso = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    payload = {
        "id": reading_id,
        "node_id": NODE_ID,
        "timestamp": now_iso,
        "moisture_pct": 80.0 if soil == "WET" else 15.0,
        "ph": 6.5,
        "nitrogen_mg_kg": 0,
        "phosphorus_mg_kg": 0,
        "potassium_mg_kg": 0,
        "soil_temp_c": round(temp, 2),
        "air_temp_c": round(temp, 2),
        "air_humid_pct": 50.0
    }

    try:
        log.info("Verzenden ID {} met timestamp {}...".format(reading_id, now_iso))
        r = requests.post(SERVER_URL, json=payload, timeout=10)
        
        if r.status_code in [200, 201]:
            log.info("Succes! Data opgeslagen.")
            return True
        else:
            log.error("Server weigert data ({}): {}".format(r.status_code, r.text))
            return False
    except Exception as e:
        log.error("Netwerkfout: " + str(e))
        return False

# ---------------- MAIN ----------------

if __name__ == "__main__":
    try:
        init_bmp280()
        provision_database()
        log.info("Systeem actief. Start metingen om de 15 seconden...")
        
        while True:
            t, l, s = read_sensors()
            print("Meting: {:.1f}C, {:.0f} lux, Bodem: {}".format(t, l, s))
            
            send_data_http(t, l, s)
            
            # Wacht 15 seconden voor stabiliteit
            time.sleep(15)
            
    except KeyboardInterrupt:
        log.info("Gestopt.")
    finally:
        bus.close()
