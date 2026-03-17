import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load env
load_dotenv(load_dotenv())

# Variables
account_sid = os.getenv("twilio_account_sid")
auth_token = os.getenv("twilio_auth_token")
phone_number = os.getenv("twilio_phone_number")
client_number=  os.getenv("client_phone_number")
client = Client(account_sid, auth_token)

#Test message
message = client.messages.create(
    #The body should contain the data that the server returns.
    body="", 
    from_=phone_number,
    to=client_number
)
print(auth_token)

print(message.body)


