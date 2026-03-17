#!/usr/bin/env python3

import smbus2
import time
import struct
import wiringpi
import requests

# ---------------- SETUP ----------------

BH1750_ADDR = 0x23
BMP280_ADDR = 0x77

bus = smbus2.SMBus(0)

# Moisture sensor (Pin 8 = WiringPi pin 3)
MOISTURE_PIN = 3

wiringpi.wiringPiSetup()
wiringpi.pinMode(MOISTURE_PIN, 0)  # INPUT

# ThingSpeak API Key
API_KEY = "FGHVUA86ARQKJIKG"

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

    if value == 0:
        return "WET"
    else:
        return "DRY"

# ---------------- THINGSPEAK ----------------

def send_to_thingspeak(temp, lux, soil):
    url = "https://api.thingspeak.com/update"

    # Convert soil to numeric value
    soil_value = 1 if soil == "WET" else 0

    payload = {
        "api_key": API_KEY,
        "field1": temp,
        "field2": lux,
        "field3": soil_value
    }

    try:
        response = requests.post(url, data=payload)
        print("ThingSpeak response:", response.text)
    except Exception as e:
        print("Error sending to ThingSpeak:", e)

# ---------------- MAIN ----------------

try:
    print("Initializing sensors...")
    init_bmp280()
    print("System ready!\n")

    while True:
        temp = read_temperature()
        lux = read_light()
        soil = read_moisture()

        print("------ SENSOR DATA ------")

        if temp is not None:
            print("Temperature: {:.2f} C".format(temp))
        else:
            print("Temp: ERROR")

        if lux is not None:
            print("Light: {:.2f} lx".format(lux))
        else:
            print("Light: ERROR")

        print("Soil:", soil)

        # SEND TO THINGSPEAK
        if temp is not None and lux is not None:
            send_to_thingspeak(temp, lux, soil)

        print("-------------------------\n")

        # IMPORTANT: ThingSpeak limit (>=15 sec)
        time.sleep(20)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    bus.close()
    print("Closed. Bye!")