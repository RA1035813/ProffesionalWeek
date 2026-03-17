import serial
import time

class GSMModem:
    def __init__(self, port: str, baud: int = 9600):
        self.port = port
        self.baud = baud
        self.ser  = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=5)
            time.sleep(2)
            self.ser.write(b"AT\r\n") 
            time.sleep(1)
            self.ser.read_all()
            
            # Set SMS mode to text
            self.ser.write(b"AT+CMGF=1\r\n") 
            time.sleep(1)
            self.ser.read_all()
            print("GSM modem ready")
            return True
        except Exception as e:
            print(f"Modem connect failed: {e}")
            return False

    def send_sms(self, number: str, message: str) -> bool:
        chunks = [message[i:i+155] for i in range(0, len(message), 155)]
        for chunk in chunks:
            try:
                # Specify phone number
                self.ser.write(f'AT+CMGS="{number}"\r\n'.encode())
                time.sleep(0.5)
                # Send text chunk followed by CTRL+Z (chr(26))
                self.ser.write((chunk + chr(26)).encode())
                time.sleep(3)
                
                resp = self.ser.read_all().decode(errors="replace")
                if "+CMGS:" not in resp:
                    print(f"SMS chunk failed: {resp!r}")
                    return False
            except Exception as e:
                print(f"send_sms error: {e}")
                return False
        return True

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

# Example Usage:
# modem = GSMModem("/dev/ttyUSB0") # Update this port to match your VM's serial device
# if modem.connect():
#     modem.send_sms("+32493882886", "Hello from physical modem!")
#     modem.disconnect()
