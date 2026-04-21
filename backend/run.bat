@echo off
echo ==========================================
echo    KARMA AI - Reverse Scam Call Agent
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found! Copy .env.example and fill in your keys.
    pause
    exit /b 1
)

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting Karma AI server...
echo.
echo MODE OPTIONS in .env:
echo   MODE=web     - Browser voice call only (open http://localhost:5000)
echo   MODE=twilio  - Twilio phone call only (needs ngrok)
echo   MODE=both    - Both modes active
echo.
echo For WEB mode:  Just open http://localhost:5000 in your browser
echo For TWILIO:    Run 'ngrok http 5000' in another terminal
echo                Then run: python setup_twilio.py ^<ngrok-url^>
echo.
python app.py
