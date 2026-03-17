# 🌾 Project Status: SoilSMS - Groep 20 'The Big Dogs'

Dit document bevat de actuele status van het software-prototype en de roadmap voor de fysieke implementatie.

## ✅ Wat is er nu AF (Done)

### 1. 📍 Farm Node (Edge Logic)
- **`sensor_node.py`**: Een Python script dat sensordata (Moisture, pH, NPK, Temp) verzamelt.
- **Simulatie Mode**: Kan draaien zonder hardware (genereert realistische testdata).
- **HTTP Transport**: Verstuurt data via HTTP POST naar de server voor lokaal testen.
- **GSM Drivers**: Bevat de logica voor de SIM800L module (AT-commando's) voor de echte 2G-omgeving.

### 2. ☁️ Cloud & Analysis (Backend)
- **`analysis_server.py`**: Flask-gebaseerde server die de data ontvangt.
- **Weather Integration**: Haalt automatisch 7-daagse weersvoorspellingen op via de **Open-Meteo API**.
- **AI Dual-Core Strategy**:
    - **Cloud**: Integratie met **Google Gemini API**.
    - **Lokaal**: Integratie met **Ollama (Mistral)** voor offline gebruik.
- **SMS Constraints**: Geforceerde output van maximaal 160 tekens in Swahili/Engels.

### 3. 🧠 Local AI & RAG (In de map `localAI/`)
- **`knowledge_base.txt`**: Een lokale dataset met agronomische regels specifiek voor Tanzania.
- **`rag_engine.py`**: Een 'Retrieval-Augmented Generation' systeem dat relevante kennis uit de database koppelt aan de sensordata.
- **`local_inference.py`**: Handelt de communicatie met de lokale Mistral-modellen af.

### 4. 🛠️ Automatisering & DevOps
- **`setup.sh`**: Een cross-platform (Linux/WSL/macOS) script dat dependencies installeert, Ollama configureert en het hele systeem met één klik opstart.
- **`.env`**: Configuratiebeheer voor API keys.
- **`requirements.txt`**: Alle benodigde Python libraries.

---

## 🛠️ Wat moet er nog GEDAAN worden (To-Do)

### 1. Hardware Assemblage (Fysiek)
- **Bedrading**: De sensoren (ADS1115, DHT22, DS18B20, NPK, GSM) fysiek aansluiten op de Raspberry Pi volgens het `README.md` schema.
- **Stroomvoorziening**: De 12V Solar setup en de 5V step-down converter testen onder belasting.

### 2. Kalibratie (Kritiek voor data-integriteit)
- **Vochtsensor**: Wet/Dry kalibratie uitvoeren en de waarden `MOISTURE_VOLT_WET` en `MOISTURE_VOLT_DRY` updaten in de code.
- **pH-Sonde**: Buffer-kalibratie (pH 4, 7, 10) uitvoeren om nauwkeurige zuurgraadmetingen te garanderen.

### 3. SMS Gateway Configuratie
- **Twilio of Africa's Talking**: Een account aanmaken en de API keys toevoegen aan `.env` om de gesimuleerde SMS-logs te vervangen door échte SMS-berichten naar de boer.
- **GSM Polling**: Op de server de `poll_modem_for_sms` functie activeren als er een fysieke GSM-dongle aan de server wordt gehangen.

### 4. Deployment
- **Systemd Services**: De `.service` bestanden (`soilsms-node.service` en `soilsms-server.service`) activeren op de RPi en de Linux server zodat ze automatisch starten bij een reboot.
- **Field Test**: Het systeem in een testomgeving (bijv. een moestuin) plaatsen en controleren of de data-loop (Node -> SMS -> Server -> AI -> SMS -> Farmer) stabiel blijft gedurende 24 uur.

---

**Status Rapport gegenereerd op:** 16 maart 2026
**Eigenaar:** Lead IoT & Backend Developer (Groep 20)
