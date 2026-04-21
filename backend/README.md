# Karma AI - Reverse Scam Call Agent

An AI-powered voice agent that plays a 70-year-old Indian grandmother (dadi) to waste scammers' time. She speaks in Hinglish (Hindi-English mix), pretends to be confused, gives wrong OTPs, tells long stories about her grandchildren, and keeps the scammer on the line as long as possible.

Built with **Python**, **Sarvam AI** (Indian language models), and **Twilio**.

---

## How It Works

Karma AI has two modes of operation — **Web Mode** (browser-based) and **Twilio Mode** (phone call-based). You can run either or both simultaneously.

### Web Mode (Browser Voice Call)

No phone number needed. You talk to the AI dadi directly from your browser using your microphone.

```
┌─────────────┐     WebSocket      ┌─────────────────┐
│   Browser    │ ◄──────────────── │   Flask Server   │
│              │                    │                  │
│  1. User     │  audio (base64)   │  4. Sarvam STT   │
│     speaks   │ ──────────────►   │     (saarika:v2.5)│
│     into mic │                    │                  │
│              │                    │  5. Sarvam Chat  │
│  8. Audio    │  audio (base64)   │     (sarvam-m)   │
│     plays    │ ◄──────────────── │                  │
│     back     │                    │  6. Sarvam TTS   │
│              │  transcript text   │     (bulbul:v3)  │
│  7. Chat     │ ◄──────────────── │                  │
│     shows up │                    │  7. Send audio + │
│              │                    │     text back    │
└─────────────┘                    └─────────────────┘
```

**Step-by-step flow:**

1. You open `http://localhost:5000` and click the green **Start Call** button
2. A WebSocket connection is established with the Flask server
3. The server generates a greeting audio using Sarvam TTS — dadi says *"Haaaan? Hello? Kaun bol raha hai?"*
4. The greeting audio (WAV) is sent back over WebSocket as base64 and plays in your browser
5. You hold the **mic button** (or press **Space bar**) and speak
6. When you release, the browser encodes your speech as a 16-bit PCM WAV file (done entirely in JavaScript, no server-side conversion needed)
7. The WAV audio is sent to the server via WebSocket as base64
8. Server sends it to **Sarvam STT** (`saarika:v2.5` model) to get a text transcript
9. The transcript is added to the conversation history and sent to **Sarvam Chat** (`sarvam-m` model) with the dadi system prompt
10. Sarvam Chat generates dadi's Hinglish response (1-3 short sentences)
11. The response text is sent to **Sarvam TTS** (`bulbul:v3` model, `shubh` speaker, 22050 Hz) to generate speech audio
12. The audio and text are sent back to the browser via WebSocket
13. Browser plays the audio and shows both sides in a chat transcript
14. Mic button re-enables — repeat from step 5

### Twilio Mode (Phone Call)

A real phone number that scammers can call. Requires a Twilio account and ngrok for webhook tunneling.

```
┌──────────┐   PSTN    ┌──────────┐  HTTP POST  ┌─────────────────┐
│  Scammer │ ────────► │  Twilio  │ ──────────► │  Flask Server   │
│  Phone   │           │  Cloud   │             │                  │
│          │           │          │  TwiML XML  │  /voice          │
│          │ ◄──────── │          │ ◄────────── │  /handle-speech  │
│          │   Audio   │          │             │  /voice-prompt   │
│          │           │          │  GET audio  │  /audio/<id>     │
│          │           │          │ ──────────► │  /call-status    │
└──────────┘           └──────────┘             └─────────────────┘
```

**Step-by-step flow:**

1. Scammer calls the Twilio phone number
2. Twilio sends a POST request to your server's `/voice` webhook
3. Server generates dadi's greeting via Sarvam TTS (8000 Hz for telephony) and stores the WAV audio in memory
4. Server returns TwiML XML with a `<Gather>` element that plays the greeting audio URL and listens for speech
5. Twilio plays the greeting to the caller and captures their speech using its own built-in speech recognition (set to `hi-IN` for Hindi)
6. When the caller stops speaking, Twilio sends the transcribed text to `/handle-speech`
7. Server sends the transcript to **Sarvam Chat** with dadi's system prompt
8. Sarvam Chat generates a response in Hinglish
9. Server converts the response to speech via **Sarvam TTS** (8000 Hz), stores the audio, and returns TwiML with the audio URL inside another `<Gather>` element
10. Twilio fetches the audio from `/audio/<id>`, plays it to the caller, and listens for the next speech
11. Loop continues until the caller hangs up
12. On hangup, Twilio hits `/call-status` and the server cleans up conversation history and stored audio

**Key difference:** In Twilio mode, Twilio handles speech recognition (STT). In Web mode, Sarvam's own STT model is used.

---

## Project Structure

```
karma-ai/
├── app.py                 # Main Flask server — routes, WebSocket handlers, mode toggle
├── sarvam_service.py      # Sarvam AI API wrapper (STT, Chat, TTS)
├── conversation.py        # Conversation manager + dadi system prompt
├── templates/
│   └── index.html         # Browser voice call UI (HTML/CSS/JS, single file)
├── setup_twilio.py        # Helper to configure Twilio webhooks via API
├── test_sarvam.py         # Quick test script for Sarvam API connectivity
├── requirements.txt       # Python dependencies
├── run.bat                # Windows one-click launcher
├── .env                   # API keys and configuration (not committed)
└── .gitignore
```

### File Details

#### `app.py` — Main Server

The central orchestrator. Initializes Flask + Flask-SocketIO and registers routes based on the `MODE` environment variable.

- **Web mode routes:** `GET /` serves the frontend. WebSocket events (`connect`, `audio_data`, `end_call`, `disconnect`) handle the browser voice call pipeline.
- **Twilio mode routes:** `POST /voice`, `/handle-speech`, `/voice-prompt`, `/call-status` handle Twilio webhooks. `GET /audio/<id>` serves generated audio files.
- **Shared:** `GET /health` returns server status including active conversation count and current mode.

Audio for Twilio is stored in an in-memory dict (`audio_store`) keyed by `{call_sid}_{uuid}` and cleaned up when the call ends. Web mode audio is sent directly over WebSocket (no storage needed).

#### `sarvam_service.py` — Sarvam AI API Wrapper

Three stateless functions that call the Sarvam AI REST API:

| Function | API Endpoint | Model | Purpose |
|----------|-------------|-------|---------|
| `speech_to_text(audio_bytes, language_code)` | `POST /speech-to-text` | `saarika:v2.5` | Converts WAV audio to text. Used in Web mode. |
| `chat_completion(messages, temperature)` | `POST /v1/chat/completions` | `sarvam-m` | Generates dadi's response given conversation history. OpenAI-compatible format. |
| `text_to_speech(text, language_code, speaker, sample_rate)` | `POST /text-to-speech` | `bulbul:v3` | Converts Hinglish text to speech. Returns base64-decoded WAV bytes. |

All functions authenticate using the `api-subscription-key` header with your `SARVAM_API_KEY`.

#### `conversation.py` — Conversation Manager

Manages per-session conversation history. The same class is used for both Web and Twilio modes — it's keyed by a string ID (WebSocket session ID or Twilio call SID).

**System Prompt:** The dadi personality is defined in a detailed Hinglish system prompt that instructs the AI to:
- Act as a 70-year-old grandmother who's hard of hearing
- Speak in natural Hindi-English mix (Hinglish)
- Use specific tactics: ask to repeat, give wrong OTPs, take chai breaks, tell stories about Sharma uncle
- Keep responses short (1-3 sentences, phone-style)
- Never give real personal information

**Memory management:** Conversations are trimmed to keep the system prompt + the last 20 messages, preventing token overflow in long calls.

#### `templates/index.html` — Browser Voice Call UI

A single-file frontend with embedded CSS and JavaScript. No build tools or npm needed.

**Audio capture:** Uses the Web Audio API (`AudioContext` + `ScriptProcessorNode`) to record raw PCM samples from the microphone, then encodes them into a 16-bit WAV file entirely in JavaScript. This avoids needing ffmpeg or any server-side audio conversion.

**Controls:**
- **Green button:** Start call (opens WebSocket, gets greeting)
- **Mic button:** Push-to-talk — hold to record, release to send. Also works with **Space bar**.
- **Red button:** End call
- Mic is disabled while dadi is speaking (prevents echo)
- Minimum recording length of 0.3 seconds to avoid accidental taps

**UI states:** Disconnected → Connected → Recording → Processing (Transcribing / Thinking / Generating voice) → Dadi Speaking → back to Connected

---

## Setup

### Prerequisites

- Python 3.10+
- A [Sarvam AI](https://dashboard.sarvam.ai) API key (required for all modes)
- A [Twilio](https://console.twilio.com) account (only needed for Twilio mode)
- [ngrok](https://ngrok.com) (only needed for Twilio mode)

### 1. Clone and Install

```bash
cd Z:\Code\granny

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure .env

Create a `.env` file in the project root:

```env
# Twilio Credentials (only needed if MODE=twilio or MODE=both)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Sarvam AI (required)
SARVAM_API_KEY=your_sarvam_api_key

# Server Config
PORT=5000
BASE_URL=https://your-ngrok-url.ngrok-free.app

# Mode: "web" (browser only), "twilio" (phone only), or "both"
MODE=web
```

| Variable | Required | Description |
|----------|----------|-------------|
| `SARVAM_API_KEY` | Always | Your Sarvam AI API key from the dashboard |
| `MODE` | Always | `web`, `twilio`, or `both` |
| `PORT` | Optional | Server port (default: 5000) |
| `BASE_URL` | Twilio only | Your public ngrok URL for Twilio to fetch audio |
| `TWILIO_ACCOUNT_SID` | Twilio only | From Twilio Console |
| `TWILIO_AUTH_TOKEN` | Twilio only | From Twilio Console |
| `TWILIO_PHONE_NUMBER` | Twilio only | Your Twilio phone number in +E.164 format |

### 3. Test API Connectivity (Optional)

```bash
python test_sarvam.py
```

This runs a quick test of all three Sarvam APIs (Chat → TTS → STT) and saves a test audio file.

---

## Running

### Web Mode (Recommended for India)

```bash
# Set MODE=web in .env, then:
python app.py
```

Open **http://localhost:5000** in your browser. Click the green button. Hold the mic button and speak. That's it.

**You need to run only one command: `python app.py`**

### Twilio Mode

Requires three terminals:

```bash
# Terminal 1: Start the server
python app.py

# Terminal 2: Start ngrok tunnel
ngrok http 5000

# Terminal 3: Configure Twilio (use the ngrok URL from Terminal 2)
python setup_twilio.py https://xxxx-xxxx.ngrok-free.app
```

Now scammers can call your Twilio number and talk to dadi.

**Note:** ngrok gives a new URL every restart (on the free plan), so you need to re-run `setup_twilio.py` each time. With a paid ngrok plan, you get a fixed domain.

### Both Modes

Set `MODE=both` in `.env`. Both the web interface at `http://localhost:5000` and the Twilio webhooks will be active.

---

## How the AI Dadi Personality Works

The dadi's behavior is controlled by the system prompt in `conversation.py`. Here's what she does:

### Personality Traits
- 70-year-old Indian grandmother, hard of hearing
- Speaks in natural Hinglish (Hindi + English mix)
- References grandchildren, pooja, household chores in every conversation
- Gets excited when the scammer offers something — *"Arre waah! Sach mein?!"*
- Goes off on tangential stories that are completely irrelevant

### Scam-Baiting Tactics
1. **Repeat requests:** *"Kya? Sunai nahi diya beta"* — makes them repeat everything
2. **Wrong details:** Deliberately gives wrong OTPs and made-up bank account numbers, slowly
3. **Chai breaks:** *"Ruko beta, chai rakh ke aati hoon"* — disappears to make tea
4. **Story time:** Launches into long stories about her son, daughter-in-law, or Sharma uncle
5. **Tech confusion:** *"Mera phone mein ye kaise karte hain?"* — pretends she doesn't know how phones work
6. **Guilt trips:** When the scammer gets frustrated — *"Beta gussa mat ho, BP badh jaayega"*
7. **Fake excitement:** *"Lottery?! 10 lakh?! Ruko main Sharma ji ko bhi batati hoon!"*

### Safety Rules
- Never gives any real personal information
- All bank details and OTPs are fake
- Responses are kept to 1-3 short sentences (natural phone conversation style)

---

## Sarvam AI Models Used

| Model | Version | Purpose | Details |
|-------|---------|---------|---------|
| **Saarika** | v2.5 | Speech-to-Text | Transcribes Hindi/Hinglish audio. Used in Web mode only. |
| **Sarvam-M** | — | Chat/LLM | Generates dadi's conversational responses. Supports Hinglish natively. |
| **Bulbul** | v3 | Text-to-Speech | Converts text to natural Hindi speech. Speaker: `shubh`. Supports code-mixed Hindi-English. |

**Sample rates:**
- Web mode: 22050 Hz (higher quality for browser playback)
- Twilio mode: 8000 Hz (telephony standard)

---

## API Endpoints

### Web Mode (WebSocket Events)

| Direction | Event | Payload | Description |
|-----------|-------|---------|-------------|
| Client → Server | `connect` | — | Opens connection, triggers greeting |
| Client → Server | `audio_data` | `{audio: "<base64>", format: "wav"}` | User's recorded speech |
| Client → Server | `end_call` | — | End the conversation |
| Server → Client | `audio_response` | `{audio: "<base64>", text: "...", type: "greeting"\|"response"}` | AI-generated audio to play |
| Server → Client | `transcript` | `{text: "...", role: "user"\|"assistant"}` | Text for chat display |
| Server → Client | `processing` | `{stage: "stt"\|"thinking"\|"tts"}` | Pipeline progress indicator |
| Server → Client | `error` | `{message: "..."}` | Error notification |
| Server → Client | `call_ended` | `{message: "..."}` | Confirmation of call end |

### Twilio Mode (HTTP Endpoints)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/voice` | POST | Incoming call webhook — plays greeting, starts listening |
| `/handle-speech` | POST | Receives transcribed speech, returns AI response audio |
| `/voice-prompt` | POST | Re-prompts caller if no speech detected |
| `/call-status` | POST | Call status changes — triggers cleanup on hangup |
| `/audio/<audio_id>` | GET | Serves generated TTS audio files to Twilio |

### Shared

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check — returns status, mode, active conversation count |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | Flask + Flask-SocketIO | Lightweight, handles both HTTP (Twilio) and WebSocket (browser) |
| AI - STT | Sarvam AI (Saarika v2.5) | Best-in-class Hindi/Hinglish speech recognition |
| AI - Chat | Sarvam AI (Sarvam-M) | Native Hinglish understanding, fast responses |
| AI - TTS | Sarvam AI (Bulbul v3) | Natural Hindi speech with code-mixing support |
| Telephony | Twilio | Phone number + call handling (optional) |
| Frontend | Vanilla HTML/CSS/JS | Zero build tools, single-file, works everywhere |
| Audio | Web Audio API | Browser-side WAV encoding, no ffmpeg needed |
| Real-time | Socket.IO | Bidirectional audio/text streaming |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mic not working in browser | Make sure you're on `localhost` or HTTPS. Check browser mic permissions. |
| "Sunai nahi diya" error | Your recording was too quiet or too short. Hold the mic button longer and speak louder. |
| Sarvam API errors | Run `python test_sarvam.py` to verify your API key works. Check your Sarvam dashboard for quota. |
| Twilio not receiving calls | Verify ngrok is running and the URL in `BASE_URL` matches. Re-run `setup_twilio.py`. |
| Audio not playing in browser | Check browser console for errors. Some browsers block autoplay — click the page first. |
| High latency | The full pipeline (STT + Chat + TTS) takes 3-8 seconds. This is normal for three sequential API calls. |
| WebSocket disconnects | Check your network. The server logs show connection/disconnection events for debugging. |

---

## License

This project is for educational and entertainment purposes. Use responsibly.
