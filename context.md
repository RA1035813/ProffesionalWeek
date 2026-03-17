# Project Context: SoilSMS

[Terug/Back](README)
## Overview
SoilSMS is an SMS-based soil monitoring and crop advisory system designed for rural Tanzania. It uses Raspberry Pi nodes to collect soil data and a central server to analyze it using Claude AI and Open-Meteo weather data, sending advice back to farmers via 2G SMS.
![schema](schemaProffesionalWeek.drawio.png)
## Current Project Status: **Architecture & Code Ready**

### What has been done:
1.  **Codebase Reorganization**: The repository has been cleaned up and follows the target structure.
    - `sensor_node.py`: Core logic for RPi sensor data collection and SMS transmission.
    - `analysis_server.py`: Flask-based server for processing incoming data, fetching weather, and generating AI advice.
2.  **Deployment Configuration**:
    - `.env.example`: Created a template for all required API keys and environment variables.
    - `soilsms-node.service`: Systemd service file for the RPi node.
    - `soilsms-server.service`: Systemd service file for the analysis server.
3.  **Documentation**:
    - `README.md`: Consolidated all hardware, wiring, calibration, and setup instructions into a single source of truth.

### What remains to be done:
1.  **Hardware Assembly**: Physical wiring of the sensors (ADS1115, DHT22, DS18B20, NPK, GSM) to the Raspberry Pi according to the wiring diagrams in the `README.md`.
2.  **Calibration (Critical)**:
    - Perform wet/dry calibration for the capacitive moisture sensors.
    - Perform pH buffer calibration (pH 4, 7, 10) for the pH probes.
    - Update the constants at the top of `sensor_node.py` with these values.
3.  **Environment Setup**:
    - Create a `.env` file from `.env.example` on the server.
    - Obtain an **Anthropic API Key** for Claude analysis.
    - (Optional) Set up an **Africa's Talking** account for more reliable SMS gateway usage.
4.  **Hardware Testing**:
    - Verify RS485 communication with the NPK sensor (check polarity).
    - Ensure the SIM800L/SIM7600 has adequate power (independent 4.2V supply).
5.  **Deployment**:
    - Install Python dependencies on both the RPi and the Server.
    - Enable and start the systemd services.
    - Test the full loop: Node -> SMS -> Server -> Claude -> Weather -> SMS -> Farmer.

## Technical Notes for AI/Human Colleagues:
- **Serial Port Conflict**: On the RPi, ensure the serial console is disabled in `raspi-config` so the GSM and NPK modules can use the UART pins.
- **SMS Constraints**: The `GSMModem` class handles message chunking (155 chars) to prevent delivery failures on rural 2G networks.
- **Weather API**: Open-Meteo is used because it requires no API key, making the system easier to deploy in low-resource settings.
