"""Karma AI — One-click startup script.

Automatically:
  1. Starts ngrok tunnel on port 5000
  2. Updates BASE_URL in .env with the new ngrok URL
  3. Configures Twilio webhooks to point to the ngrok URL
  4. Launches the Flask server

Usage:
  python start.py

Requirements:
  pip install pyngrok
  (or install ngrok CLI and set authtoken)
"""

import os
import re
import subprocess
import sys
import time

from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 5000))
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")


def check_ngrok_installed():
    """Check if pyngrok is available, install if not."""
    try:
        from pyngrok import ngrok  # noqa: F401
        return True
    except ImportError:
        print("[!] pyngrok not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
        return True


def start_ngrok(port: int) -> str:
    """Start ngrok tunnel and return the public HTTPS URL."""
    from pyngrok import ngrok, conf

    # Check if NGROK_AUTHTOKEN is set
    authtoken = os.getenv("NGROK_AUTHTOKEN", "")
    if authtoken:
        conf.get_default().auth_token = authtoken

    print(f"[*] Starting ngrok tunnel on port {port}...")
    tunnel = ngrok.connect(port, "http")
    public_url = tunnel.public_url

    # Ensure HTTPS
    if public_url.startswith("http://"):
        public_url = public_url.replace("http://", "https://")

    print(f"[+] Ngrok tunnel: {public_url}")
    return public_url


def update_env_base_url(ngrok_url: str):
    """Update BASE_URL in .env file."""
    with open(ENV_FILE, "r") as f:
        content = f.read()

    # Replace existing BASE_URL
    if "BASE_URL=" in content:
        content = re.sub(r"BASE_URL=.*", f"BASE_URL={ngrok_url}", content)
    else:
        content += f"\nBASE_URL={ngrok_url}\n"

    with open(ENV_FILE, "w") as f:
        f.write(content)

    # Also update the current environment
    os.environ["BASE_URL"] = ngrok_url
    print(f"[+] Updated .env BASE_URL = {ngrok_url}")


def setup_twilio_webhooks(ngrok_url: str):
    """Configure Twilio phone number webhooks."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, phone_number]):
        print("[!] Twilio credentials not set in .env — skipping webhook setup")
        print("    Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
        return

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        if not numbers:
            print(f"[!] Phone number {phone_number} not found in Twilio account")
            return

        numbers[0].update(
            voice_url=f"{ngrok_url}/voice",
            voice_method="POST",
            status_callback=f"{ngrok_url}/call-status",
            status_callback_method="POST",
        )

        print(f"[+] Twilio webhooks configured:")
        print(f"    Voice URL:       {ngrok_url}/voice")
        print(f"    Status Callback: {ngrok_url}/call-status")
        print(f"    Phone Number:    {phone_number}")
    except Exception as e:
        print(f"[!] Failed to configure Twilio: {e}")


def main():
    print("=" * 55)
    print("  KARMA AI — Automatic Startup")
    print("=" * 55)
    print()

    # Step 1: Start ngrok
    check_ngrok_installed()
    ngrok_url = start_ngrok(PORT)
    print()

    # Step 2: Update .env
    update_env_base_url(ngrok_url)
    print()

    # Step 3: Configure Twilio
    setup_twilio_webhooks(ngrok_url)
    print()

    # Step 4: Print URLs
    print("=" * 55)
    print("  KARMA AI is starting...")
    print("=" * 55)
    print(f"  Web Voice Call:  http://localhost:{PORT}/")
    print(f"  Live Dashboard:  http://localhost:{PORT}/dashboard/live-calls.html")
    print(f"  Analytics:       http://localhost:{PORT}/dashboard/analytics.html")
    print(f"  Archive:         http://localhost:{PORT}/dashboard/archive.html")
    print(f"  Twilio Webhook:  {ngrok_url}/voice")
    print(f"  Health Check:    http://localhost:{PORT}/health")
    print("=" * 55)
    print()

    # Step 5: Launch Flask server
    # Use subprocess so ngrok stays alive
    subprocess.run([
        sys.executable, "app.py"
    ], cwd=os.path.dirname(__file__))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Karma AI...")
        try:
            from pyngrok import ngrok
            ngrok.kill()
        except Exception:
            pass
