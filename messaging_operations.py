from twilio.rest import Client
import json

credfile = open("creds.json")
creds = json.load(credfile)

class TwilioOperations:
    def __init__(self):
        self.twilio_account_sid = creds['sid']
        self.twilio_auth_token = creds['token']
        self.twilio_phone_number = creds['number']
        
    def send_message(self, body, receiver):
        client = Client(self.twilio_account_sid, self.twilio_auth_token)
        message = client.messages.create(
            to='whatsapp:' + receiver, 
            from_='whatsapp:' + self.twilio_phone_number,
            body=body
        )
        print("Message SID:", message.sid)