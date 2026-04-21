"""Helper script to configure Twilio phone number webhooks.

Run this after starting ngrok to automatically configure your
Twilio phone number to point to your ngrok URL.
"""

import os
import sys

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def setup_twilio_webhooks(ngrok_url: str):
    """Configure Twilio phone number to use our webhooks."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, phone_number]):
        print("ERROR: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env")
        sys.exit(1)

    client = Client(account_sid, auth_token)

    # Find the phone number SID
    numbers = client.incoming_phone_numbers.list(phone_number=phone_number)

    if not numbers:
        print(f"ERROR: Phone number {phone_number} not found in your Twilio account")
        sys.exit(1)

    number = numbers[0]

    # Update webhooks
    number.update(
        voice_url=f"{ngrok_url}/voice",
        voice_method="POST",
        status_callback=f"{ngrok_url}/call-status",
        status_callback_method="POST",
    )

    print(f"Twilio webhooks configured:")
    print(f"  Voice URL:      {ngrok_url}/voice")
    print(f"  Status Callback: {ngrok_url}/call-status")
    print(f"  Phone Number:    {phone_number}")
    print(f"\nKarma AI is ready! Scammers can now call {phone_number}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_twilio.py <ngrok_url>")
        print("Example: python setup_twilio.py https://abc123.ngrok-free.app")
        sys.exit(1)

    setup_twilio_webhooks(sys.argv[1].rstrip("/"))
