# SoilSMS

SMS-based soil monitoring and crop advisory system for rural Tanzania.  
No internet required on the farm. Works on **2G GSM**.

---

# System Overview

## Two-Component System

### sensor_node.py (runs on RPi)

Reads **5 sensor types** via:

- I2C  
- 1-Wire  
- UART Modbus  
- GPIO  

Then:

1. Serializes readings into **compact JSON**
2. Sends data as an **SMS using AT commands**
3. Loops every hour

---

### analysis_server.py (runs on any Linux server)

1. Receives SMS
2. Parses JSON data
3. Fetches **7-day weather forecast** from **Open-Meteo** (no API key required)
4. Sends both datasets to **Claude** with a Tanzania-specific agronomy prompt
5. Converts the result into **plain readable advice**
6. Sends SMS reply back to the farmer

Supports two modes:

- **Local GSM modem** (polling mode)
- **Africa’s Talking API** (webhook mode)

---

# Architecture
[Farm / RPi Node] [Server]
Sensors → sensor_node.py analysis_server.py
└─ Reads soil data ├─ Parses SMS JSON
└─ JSON via SMS ─────────► ├─ Fetches weather
(Open-Meteo) ├─ Analyses with Claude
└─ Replies to farmer
  [Farmer's Phone]
  Receives plain-text crop advisory

---

# Sensors Covered

- **Capacitive soil moisture** (via ADS1115 ADC)
- **Analog pH sensor** (same ADC)
- **DHT22** — air temperature + humidity
- **DS18B20** — soil temperature (1-Wire)
- **NPK sensor** — Nitrogen, Phosphorus, Potassium (RS485 Modbus RTU)

---

# Example SMS Output

The SMS sent to the farmer contains:
→ Nutrient diagnosis
→ What to do
→ What crop to plant
→ When to plant

Total size: **~550 characters across 3–4 messages**.

---

# Key Rural-Friendly Design Decisions

- **2G SMS only** → no internet required at the farm
- **Compact JSON messages (~120 chars per reading)**
- Optional **Africa’s Talking SMS gateway** for reliability
- **Systemd services** so everything auto-starts
- **Calibration values clearly marked** at the top of the node script

---

# Hardware (RPi Node)

| Component | Model | Purpose |
|-----------|-------|--------|
| Microcontroller | Raspberry Pi Zero 2W | Main controller |
| Moisture sensor | Capacitive (3.3V) | Soil moisture % |
| ADC | ADS1115 (I2C) | Reads moisture + pH analog |
| pH sensor | Analog pH probe + module | Soil pH |
| Air temp/humidity | DHT22 | Air conditions |

---

# Data Flow
Sensors
↓
Raspberry Pi Node
↓
SMS (JSON)
↓
Analysis Server
↓
Weather + AI Analysis
↓
SMS Crop Advisory
↓
Farmer

---

# Deployment

The repository includes:

- Wiring tables
- Sensor calibration steps
- Troubleshooting
- Deployment commands
