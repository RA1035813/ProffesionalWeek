import requests

def send_via_africas_talking(to: str, message: str) -> bool:
    AT_API_KEY = "your_api_key_here"
    AT_USERNAME = "your_username_here"
    
    # Chunk the message if it exceeds standard SMS length
    chunks = [message[i:i+155] for i in range(0, len(message), 155)]
    
    for chunk in chunks:
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
                    "message": chunk,
                },
                timeout=10
            )
            data = resp.json()
            if data.get("SMSMessageData", {}).get("Recipients", [{}])[0].get("status") != "Success":
                print(f"AT SMS failed: {data}")
                return False
        except Exception as e:
            print(f"Africa's Talking error: {e}")
            return False
    return True

# Example Usage:
# send_via_africas_talking("+32493882886", "Hello from Ubuntu VM!")
