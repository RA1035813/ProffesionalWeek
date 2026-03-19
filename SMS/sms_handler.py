import os
import time
import logging
import requests
import json
import serial
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("soilsms.sms_handler")

def send_sms(to: str, message: str) -> bool:
    """Unified SMS sender supporting Modem, Africa's Talking, and httpSMS."""
    SMS_MODE = os.getenv("SMS_MODE", "httpsms") # Default to httpsms as it's common
    
    if SMS_MODE == "modem":
        return _send_via_modem(to, message)
    elif SMS_MODE == "africas_talking":
        return _send_via_africas_talking(to, message)
    elif SMS_MODE == "httpsms":
        return _send_via_httpsms(to, message)
    else:
        log.error(f"Unknown SMS_MODE: {SMS_MODE}")
        return False

def _send_via_modem(to: str, message: str) -> bool:
    GSM_PORT = os.getenv("GSM_PORT", "/dev/ttyAMA0")
    try:
        # Simple serial logic for GSM modem
        ser = serial.Serial(GSM_PORT, 9600, timeout=5)
        ser.write(b"AT+CMGF=1\r\n")
        time.sleep(1)
        ser.write(f'AT+CMGS="{to}"\r\n'.encode())
        time.sleep(0.5)
        ser.write((message + chr(26)).encode())
        time.sleep(3)
        ser.close()
        log.info(f"SMS Sent via Modem to {to}")
        return True
    except Exception as e:
        log.error(f"Modem SMS failed: {e}")
        return False

def _send_via_africas_talking(to: str, message: str) -> bool:
    AT_API_KEY = os.getenv("AT_API_KEY", "")
    AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
    
    # Chunk the message if it exceeds standard SMS length (AT often handles this, but being safe)
    try:
        resp = requests.post(
            "https://api.africastalking.com/version1/messaging",
            headers={
                "apiKey": AT_API_KEY,
                "Accept": "application/json",
            },
            data={
                "username": AT_USERNAME,
                "to": to,
                "message": message,
            },
            timeout=15
        )
        data = resp.json()
        status = data.get("SMSMessageData", {}).get("Recipients", [{}])[0].get("status")
        if status == "Success":
            log.info(f"SMS Sent via Africa's Talking to {to}")
            return True
        else:
            log.error(f"Africa's Talking failed: {data}")
            return False
    except Exception as e:
        log.error(f"Africa's Talking error: {e}")
        return False

def _send_via_httpsms(to: str, message: str) -> bool:
    API_KEY = os.getenv("httpsms_api_key", "").strip()
    FROM_NUMBER = os.getenv("Ward_phone")
    
    if not API_KEY or not FROM_NUMBER:
        log.error("httpSMS credentials missing (httpsms_api_key or Ward_phone)")
        return False

    try:
        resp = requests.post(
            "https://api.httpsms.com/v1/messages/send",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
            json={
                "content": message, 
                "from": FROM_NUMBER, 
                "to": to, 
                "skip_rcs": True
            },
            timeout=15
        )
        resp.raise_for_status()
        log.info(f"SMS Sent via httpSMS to {to}")
        return True
    except Exception as e:
        log.error(f"httpSMS failed: {e}")
        return False
