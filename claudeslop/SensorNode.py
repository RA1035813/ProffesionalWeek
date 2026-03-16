#!/usr/bin/env python3
"""
SoilSMS - Raspberry Pi Sensor Node
Reads soil sensors and sends data to server via SMS (AT commands over serial).

Hardware wiring:
  - Capacitive soil moisture sensor  → ADC (ADS1115) channel 0
  - DHT22 (air temp + humidity)      → GPIO 4
  - DS18B20 (soil temperature)       → GPIO 17 (1-Wire)
  - pH sensor (analog)               → ADC channel 1
  - NPK sensor (Modbus RTU UART)     → UART0 /dev/ttyS0
  - SIM800L / SIM7600 GSM module     → UART1 /dev/ttyAMA0

Install dependencies:
  pip install adafruit-circuitpython-ads1x15 adafruit-circuitpython-dht
  pip install w1thermsensor pyserial minimalmodbus
"""

import time
import json
import serial
import logging
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from w1thermsensor import W1ThermSensor
import minimalmodbus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/soilsms.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("soilsms.node")

# ─── CONFIG ──────────────────────────────────────────────────────────────────

SERVER_PHONE   = "+255XXXXXXXXX"   # Tanzania server SIM number
FARMER_PHONE   = "+255YYYYYYYYY"   # Farmer's phone (for direct fallback)
NODE_ID        = "FARM001"         # Unique ID for this sensor node
GSM_PORT       = "/dev/ttyAMA0"
NPK_PORT       = "/dev/ttyS0"
READ_INTERVAL  = 3600              # Seconds between readings (1 hour default)
GSM_BAUD       = 9600
NPK_BAUD       = 9600

# ADC voltage calibration for moisture (adjust per sensor)
MOISTURE_VOLT_WET  = 1.2   # Voltage when fully wet
MOISTURE_VOLT_DRY  = 2.8   # Voltage when fully dry

# pH calibration (adjust per sensor + calibration solution)
PH_VOLT_PH4    = 3.00
PH_VOLT_PH7    = 2.50
PH_VOLT_PH10   = 2.00

# ─── GSM / SMS ───────────────────────────────────────────────────────────────

class GSMModem:
    def __init__(self, port: str, baud: int = 9600):
        self.port = port
        self.baud = baud
        self.ser  = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=5)
            time.sleep(2)
            if self._at("AT") and self._at("AT+CMGF=1"):  # SMS text mode
                log.info("GSM modem ready")
                return True
        except serial.SerialException as e:
            log.error(f"GSM connect failed: {e}")
        return False

    def _at(self, cmd: str, wait: float = 1.5) -> str:
        """Send AT command, return response string."""
        self.ser.write((cmd + "\r\n").encode())
        time.sleep(wait)
        resp = self.ser.read_all().decode(errors="replace").strip()
        log.debug(f"AT>{cmd} => {resp!r}")
        return resp

    def send_sms(self, number: str, message: str) -> bool:
        """Send SMS. Message should be <160 chars for single SMS."""
        try:
            # Chunk if needed (rural GSM often drops long concat SMS)
            chunks = [message[i:i+155] for i in range(0, len(message), 155)]
            for i, chunk in enumerate(chunks):
                self.ser.write(f'AT+CMGS="{number}"\r\n'.encode())
                time.sleep(0.5)
                self.ser.write((chunk + chr(26)).encode())  # Ctrl+Z to send
                time.sleep(3)
                resp = self.ser.read_all().decode(errors="replace")
                if "+CMGS:" not in resp:
                    log.error(f"SMS chunk {i+1} failed: {resp!r}")
                    return False
                time.sleep(1)
            log.info(f"SMS sent to {number} ({len(chunks)} part(s))")
            return True
        except Exception as e:
            log.error(f"send_sms error: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

# ─── SENSORS ─────────────────────────────────────────────────────────────────

def read_moisture_and_ph() -> dict:
    """Read ADS1115 ADC for capacitive moisture and pH sensors."""
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)

    moisture_chan = AnalogIn(ads, ADS.P0)
    ph_chan       = AnalogIn(ads, ADS.P1)

    m_volt = moisture_chan.voltage
    p_volt = ph_chan.voltage

    # Map moisture voltage to 0-100%
    moisture_pct = max(0, min(100,
        (MOISTURE_VOLT_DRY - m_volt) / (MOISTURE_VOLT_DRY - MOISTURE_VOLT_WET) * 100
    ))

    # Linear interpolation for pH (4-10 range via two calibration points)
    if p_volt >= PH_VOLT_PH4:
        ph = 4.0
    elif p_volt <= PH_VOLT_PH10:
        ph = 10.0
    else:
        ph = 4.0 + (PH_VOLT_PH4 - p_volt) / (PH_VOLT_PH4 - PH_VOLT_PH10) * 6.0

    return {
        "moisture_pct": round(moisture_pct, 1),
        "ph": round(ph, 2),
    }

def read_air_temp_humidity() -> dict:
    """Read DHT22 for air temperature and humidity."""
    dht = adafruit_dht.DHT22(board.D4)
    for attempt in range(3):
        try:
            return {
                "air_temp_c":  dht.temperature,
                "air_humid_pct": dht.humidity,
            }
        except RuntimeError as e:
            log.warning(f"DHT22 read attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return {"air_temp_c": None, "air_humid_pct": None}

def read_soil_temp() -> dict:
    """Read DS18B20 1-Wire soil temperature probe."""
    try:
        sensor = W1ThermSensor()
        return {"soil_temp_c": round(sensor.get_temperature(), 2)}
    except Exception as e:
        log.warning(f"DS18B20 read failed: {e}")
        return {"soil_temp_c": None}

def read_npk() -> dict:
    """
    Read NPK sensor via Modbus RTU.
    Typical RS485 NPK sensors (e.g. JXBS-3001-NPK) use:
      Register 0x0000 = Nitrogen  (mg/kg)
      Register 0x0001 = Phosphorus (mg/kg)
      Register 0x0002 = Potassium  (mg/kg)
    """
    try:
        inst = minimalmodbus.Instrument(NPK_PORT, slaveaddress=1)
        inst.serial.baudrate = NPK_BAUD
        inst.serial.timeout  = 1
        inst.mode = minimalmodbus.MODE_RTU

        nitrogen    = inst.read_register(0x0000, functioncode=3)
        phosphorus  = inst.read_register(0x0001, functioncode=3)
        potassium   = inst.read_register(0x0002, functioncode=3)

        return {
            "nitrogen_mg_kg":   nitrogen,
            "phosphorus_mg_kg": phosphorus,
            "potassium_mg_kg":  potassium,
        }
    except Exception as e:
        log.error(f"NPK read failed: {e}")
        return {
            "nitrogen_mg_kg":   None,
            "phosphorus_mg_kg": None,
            "potassium_mg_kg":  None,
        }

def collect_all_readings() -> dict:
    """Aggregate all sensor readings into one payload."""
    log.info("Collecting sensor readings...")
    data = {
        "node_id":   NODE_ID,
        "timestamp": int(time.time()),
    }
    data.update(read_moisture_and_ph())
    data.update(read_air_temp_humidity())
    data.update(read_soil_temp())
    data.update(read_npk())
    log.info(f"Readings: {data}")
    return data

# ─── MAIN LOOP ───────────────────────────────────────────────────────────────

def main():
    log.info(f"SoilSMS node {NODE_ID} starting")
    modem = GSMModem(GSM_PORT, GSM_BAUD)

    if not modem.connect():
        log.critical("Cannot connect to GSM modem. Halting.")
        return

    while True:
        try:
            readings = collect_all_readings()
            payload  = json.dumps(readings, separators=(',', ':'))  # Compact JSON

            log.info(f"Sending payload ({len(payload)} chars) to server")
            success = modem.send_sms(SERVER_PHONE, payload)

            if not success:
                log.error("Failed to send SMS to server, will retry next cycle")

        except Exception as e:
            log.error(f"Main loop error: {e}", exc_info=True)

        log.info(f"Sleeping {READ_INTERVAL}s until next reading")
        time.sleep(READ_INTERVAL)


if __name__ == "__main__":
    main()