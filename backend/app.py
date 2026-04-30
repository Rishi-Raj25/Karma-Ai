"""Karma AI - Reverse Scam Call Agent.

Twilio + Sarvam AI (STT/TTS) + OpenRouter GPT-4o (LLM).

Modes (configurable via MODE in .env):
  - "web"    : Browser-based voice call via WebSocket
  - "twilio" : Phone call via Twilio webhooks
  - "both"   : Both interfaces active simultaneously

Live Dashboard:
  - Socket.IO broadcasts to all connected dashboard clients
  - REST APIs for analytics and call archive
  - Frontend served from /dashboard/
"""

import base64
import io
import logging
import os
import uuid

from dotenv import load_dotenv

# Load .env BEFORE importing modules that read env vars at module level
load_dotenv()

from flask import Flask, Response, jsonify, render_template, request, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room

from conversation import ConversationManager, GREETING_TEXT
from database import (
    create_call, end_call as db_end_call, get_active_calls, get_call,
    get_call_history, get_call_intel, get_call_transcript, get_stats,
    get_total_calls, init_db, save_intel, save_message,
)
from intel_extractor import extract_intel
from llm_service import chat_completion
from sarvam_service import speech_to_text, text_to_speech

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "karma-ai-secret-key")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    max_http_buffer_size=10 * 1024 * 1024,  # 10 MB for audio blobs
    async_mode="threading",
)

MODE = os.getenv("MODE", "both").lower().strip()

conversation_mgr = ConversationManager()

# In-memory store for generated audio files (Twilio mode): audio_id -> wav bytes
audio_store: dict[str, bytes] = {}

# Mute state per call
mute_state: dict[str, bool] = {}

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# Flask will now serve templates from 'templates' and assets from 'static' automatically.

# Initialize database
init_db()

# Pre-cache greeting TTS audio at startup (saves ~1s on first call)
_cached_greeting_twilio: bytes | None = None  # 8kHz for phone
_cached_greeting_web: bytes | None = None     # 22050Hz for browser

def _precache_greetings():
    global _cached_greeting_twilio, _cached_greeting_web
    try:
        logger.info("Pre-caching greeting TTS audio...")
        _cached_greeting_twilio = text_to_speech(
            text=GREETING_TEXT, language_code="hi-IN", speaker="kavya", sample_rate="8000",
        )
        _cached_greeting_web = text_to_speech(
            text=GREETING_TEXT, language_code="hi-IN", speaker="kavya", sample_rate="22050",
        )
        logger.info("Greeting audio cached (twilio=%d bytes, web=%d bytes)",
                     len(_cached_greeting_twilio), len(_cached_greeting_web))
    except Exception as e:
        logger.warning("Failed to pre-cache greeting: %s (will generate on first call)", e)

_precache_greetings()


# ---------------------------------------------------------------------------
# Dashboard helpers — broadcast to all dashboard viewers
# ---------------------------------------------------------------------------
def broadcast_call_started(call_sid: str, caller: str = "Unknown"):
    """Notify dashboard that a new call started."""
    from datetime import datetime, timezone
    socketio.emit("call_started", {
        "call_sid": call_sid,
        "caller": caller,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, room="dashboard")


def broadcast_call_ended(call_sid: str, duration: int = 0):
    """Notify dashboard that a call ended."""
    socketio.emit("call_ended", {
        "call_sid": call_sid,
        "duration": duration,
    }, room="dashboard")


def broadcast_transcript(call_sid: str, speaker: str, text: str):
    """Send a transcript message to the dashboard."""
    socketio.emit("transcript_message", {
        "call_sid": call_sid,
        "speaker": speaker,  # "scammer" or "ai"
        "text": text,
    }, room="dashboard")


def broadcast_ai_status(status: str):
    """Update AI status on dashboard."""
    socketio.emit("ai_status", {"status": status}, room="dashboard")


def broadcast_intel(call_sid: str, intel_items: list[dict]):
    """Send extracted intel to dashboard."""
    if not intel_items:
        return

    update = {}
    for item in intel_items:
        field = item["field_name"]
        value = item["field_value"]
        if field == "scammer_name":
            update["scammer_name"] = value
        elif field == "scam_type":
            update["scam_type"] = value
        elif field == "organization_claimed":
            update["organization_claimed"] = value
        elif field in ("bank_mentioned",):
            update["organization_claimed"] = value
        elif field == "upi_id":
            update["upi_id"] = value
        elif field == "phone_number":
            update["phone_number"] = value

    if update:
        update["call_sid"] = call_sid
        socketio.emit("intel_update", update, room="dashboard")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def generate_and_store_audio(text: str, call_sid: str) -> str:
    """Generate TTS audio and store it, returning the audio URL (Twilio mode)."""
    logger.info("Generating TTS for call %s: %s", call_sid, text[:80])

    audio_bytes = text_to_speech(
        text=text,
        language_code="hi-IN",
        speaker="kavya",
        sample_rate="8000",
    )

    audio_id = f"{call_sid}_{uuid.uuid4().hex[:8]}"
    audio_store[audio_id] = audio_bytes

    return f"{BASE_URL}/audio/{audio_id}"


def process_scammer_speech(call_sid: str, speech_text: str) -> str | None:
    """Process scammer speech through LLM and intel extraction.

    Returns AI response text, or None if muted.
    """
    # Save scammer message to DB
    save_message(call_sid, "user", speech_text)

    # Broadcast to dashboard
    broadcast_ai_status("ANALYZING...")
    broadcast_transcript(call_sid, "scammer", speech_text)

    # Extract intel from scammer message
    intel_items = extract_intel(speech_text)
    for item in intel_items:
        save_intel(call_sid, item["field_name"], item["field_value"], item["confidence"])
    broadcast_intel(call_sid, intel_items)

    # Check if AI is muted for this call
    if mute_state.get(call_sid, False):
        broadcast_ai_status("MUTED")
        return None

    # Get AI response via OpenRouter GPT-4o
    messages = conversation_mgr.add_user_message(call_sid, speech_text)
    ai_response = chat_completion(messages, temperature=0.8)
    logger.info("AI response (CallSid: %s): %s", call_sid, ai_response)
    conversation_mgr.add_assistant_message(call_sid, ai_response)

    # Save AI message to DB
    save_message(call_sid, "assistant", ai_response)

    # Broadcast to dashboard
    broadcast_ai_status("DEFENDING")
    broadcast_transcript(call_sid, "ai", ai_response)

    return ai_response


# ===================================================================
#  SOCKET.IO — Connection handling (dashboard + web clients)
# ===================================================================

@socketio.on("connect")
def ws_connect():
    """Client connected — determine if dashboard or web client."""
    role = request.args.get("role", "")

    if role == "dashboard":
        join_room("dashboard")
        logger.info("Dashboard client connected: %s", request.sid)

        # Send currently active calls
        active = get_active_calls()
        for call in active:
            emit("call_started", {
                "call_sid": call["id"],
                "caller": call.get("caller_number", "Unknown"),
                "timestamp": call["start_time"],
            })
        return

    # Web mode client
    if MODE not in ("web", "both"):
        return

    session_id = request.sid
    logger.info("Web client connected: %s", session_id)
    conversation_mgr.get_or_create(session_id)

    # Register as active call in DB
    create_call(session_id, caller="web-client", mode="web")
    broadcast_call_started(session_id, "Web Client")

    try:
        # Use pre-cached web greeting or generate on the fly
        greeting_audio = _cached_greeting_web or text_to_speech(
            text=GREETING_TEXT,
            language_code="hi-IN",
            speaker="kavya",
            sample_rate="22050",
        )
        emit("audio_response", {
            "audio": base64.b64encode(greeting_audio).decode("utf-8"),
            "text": GREETING_TEXT,
            "type": "greeting",
        })

        # Save greeting to DB
        save_message(session_id, "assistant", GREETING_TEXT)
        broadcast_transcript(session_id, "ai", GREETING_TEXT)

    except Exception as e:
        logger.error("Error sending greeting: %s", e)
        emit("error", {"message": "Failed to generate greeting audio"})


@socketio.on("audio_data")
def ws_audio_data(data):
    """Process audio from browser microphone (web mode)."""
    if MODE not in ("web", "both"):
        return

    session_id = request.sid
    logger.info("Received audio from web client: %s", session_id)

    try:
        # Decode audio
        audio_b64 = data.get("audio", "")
        audio_bytes = base64.b64decode(audio_b64)
        audio_format = data.get("format", "wav")

        if audio_format == "webm":
            wav_bytes = _convert_webm_to_wav(audio_bytes)
        else:
            wav_bytes = audio_bytes

        # Step 1: Sarvam STT
        emit("processing", {"stage": "stt"})
        transcript = speech_to_text(wav_bytes, language_code="hi-IN")
        logger.info("STT result (session %s): %s", session_id, transcript)

        if not transcript.strip():
            emit("error", {"message": "Sunai nahi diya... please phir se bolo!"})
            return

        emit("transcript", {"text": transcript, "role": "user"})

        # Step 2: LLM + intel extraction
        emit("processing", {"stage": "thinking"})
        ai_response = process_scammer_speech(session_id, transcript)

        if ai_response is None:
            emit("error", {"message": "AI is muted"})
            return

        emit("transcript", {"text": ai_response, "role": "assistant"})

        # Step 3: Sarvam TTS
        emit("processing", {"stage": "tts"})
        response_audio = text_to_speech(
            text=ai_response,
            language_code="hi-IN",
            speaker="kavya",
            sample_rate="22050",
        )

        emit("audio_response", {
            "audio": base64.b64encode(response_audio).decode("utf-8"),
            "text": ai_response,
            "type": "response",
        })

    except Exception as e:
        logger.error("Error processing web audio (session %s): %s", session_id, e)
        emit("error", {"message": f"Error: {str(e)}"})


@socketio.on("end_call")
def ws_end_call():
    """Client ended the call."""
    session_id = request.sid
    logger.info("Web client ending call: %s", session_id)
    conversation_mgr.end_conversation(session_id)
    mute_state.pop(session_id, None)
    db_end_call(session_id, "completed")
    broadcast_call_ended(session_id)
    emit("call_ended", {"message": "Call ended. Phir milenge!"})


@socketio.on("disconnect")
def ws_disconnect():
    """Client disconnected."""
    session_id = request.sid
    role = request.args.get("role", "")

    if role == "dashboard":
        logger.info("Dashboard client disconnected: %s", session_id)
        return

    logger.info("Web client disconnected: %s", session_id)
    conversation_mgr.end_conversation(session_id)
    mute_state.pop(session_id, None)
    db_end_call(session_id, "completed")
    broadcast_call_ended(session_id)


# Dashboard control events
@socketio.on("mute_ai")
def ws_mute_ai(data):
    """Toggle AI mute for a call."""
    call_sid = data.get("call_sid")
    muted = data.get("muted", False)
    if call_sid:
        mute_state[call_sid] = muted
        logger.info("AI %s for call %s", "muted" if muted else "unmuted", call_sid)
        broadcast_ai_status("MUTED" if muted else "ACTIVE")


@socketio.on("drop_call")
def ws_drop_call(data):
    """Drop an active call from dashboard."""
    call_sid = data.get("call_sid")
    if not call_sid:
        return

    logger.info("Dashboard dropping call: %s", call_sid)

    # For Twilio calls, try to end the call via API
    if MODE in ("twilio", "both") and call_sid.startswith("CA"):
        try:
            from twilio.rest import Client
            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            )
            client.calls(call_sid).update(status="completed")
        except Exception as e:
            logger.error("Failed to drop Twilio call: %s", e)

    conversation_mgr.end_conversation(call_sid)
    mute_state.pop(call_sid, None)
    db_end_call(call_sid, "dropped")
    broadcast_call_ended(call_sid)


def _convert_webm_to_wav(webm_bytes: bytes) -> bytes:
    """Convert WebM/opus audio to WAV format."""
    from pydub import AudioSegment
    audio = AudioSegment.from_file(io.BytesIO(webm_bytes), format="webm")
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)
    return wav_buffer.read()


# ===================================================================
#  TWILIO MODE — Phone call via Twilio webhooks
# ===================================================================

if MODE in ("twilio", "both"):
    from twilio.twiml.voice_response import Gather, VoiceResponse


@app.route("/voice", methods=["POST"])
def voice():
    """Twilio webhook: called when someone calls the Twilio number."""
    if MODE not in ("twilio", "both"):
        return "Twilio mode not enabled", 404

    call_sid = request.form.get("CallSid", "unknown")
    caller = request.form.get("From", "unknown")
    logger.info("Incoming call from %s (CallSid: %s)", caller, call_sid)

    conversation_mgr.get_or_create(call_sid)

    # Register in DB and broadcast to dashboard
    create_call(call_sid, caller=caller, mode="twilio")
    broadcast_call_started(call_sid, caller)
    save_message(call_sid, "assistant", GREETING_TEXT)
    broadcast_transcript(call_sid, "ai", GREETING_TEXT)

    response = VoiceResponse()

    try:
        # Use pre-cached greeting audio (instant) or generate on the fly
        if _cached_greeting_twilio:
            audio_id = f"{call_sid}_{uuid.uuid4().hex[:8]}"
            audio_store[audio_id] = _cached_greeting_twilio
            greeting_url = f"{BASE_URL}/audio/{audio_id}"
        else:
            greeting_url = generate_and_store_audio(GREETING_TEXT, call_sid)

        gather = Gather(
            input="speech",
            action="/handle-speech",
            method="POST",
            timeout=3,
            speech_timeout=2,
            language="hi-IN",
        )
        gather.play(greeting_url)
        response.append(gather)
        response.redirect("/voice-prompt")

    except Exception as e:
        logger.error("Error in /voice: %s", e)
        response.say("Sorry, technical issue. Please call again.", voice="alice")

    return Response(str(response), mimetype="application/xml")


@app.route("/voice-prompt", methods=["POST"])
def voice_prompt():
    """Re-prompt the caller if no speech was detected."""
    if MODE not in ("twilio", "both"):
        return "Twilio mode not enabled", 404

    call_sid = request.form.get("CallSid", "unknown")
    response = VoiceResponse()

    prompt_text = "Hello? Beta? Koi hai? Arre bolo na kuch..."
    try:
        prompt_url = generate_and_store_audio(prompt_text, call_sid)

        gather = Gather(
            input="speech",
            action="/handle-speech",
            method="POST",
            timeout=6,
            speech_timeout=2,
            language="hi-IN",
        )
        gather.play(prompt_url)
        response.append(gather)

        goodbye_text = "Arre koi hai hi nahi... chalo phone rakhti hoon. Ram Ram!"
        goodbye_url = generate_and_store_audio(goodbye_text, call_sid)
        response.play(goodbye_url)
        response.hangup()

    except Exception as e:
        logger.error("Error in /voice-prompt: %s", e)
        response.hangup()

    return Response(str(response), mimetype="application/xml")


@app.route("/handle-speech", methods=["POST"])
def handle_speech():
    """Twilio webhook: processes caller's speech through pipeline."""
    if MODE not in ("twilio", "both"):
        return "Twilio mode not enabled", 404

    call_sid = request.form.get("CallSid", "unknown")
    speech_result = request.form.get("SpeechResult", "")

    logger.info("Speech from caller (CallSid: %s): %s", call_sid, speech_result)

    response = VoiceResponse()

    if not speech_result.strip():
        response.redirect("/voice-prompt")
        return Response(str(response), mimetype="application/xml")

    try:
        ai_response = process_scammer_speech(call_sid, speech_result)

        if ai_response is None:
            # AI is muted — just listen again
            gather = Gather(
                input="speech",
                action="/handle-speech",
                method="POST",
                timeout=5,
                speech_timeout=2,
                language="hi-IN",
            )
            response.append(gather)
            response.redirect("/voice-prompt")
            return Response(str(response), mimetype="application/xml")

        audio_url = generate_and_store_audio(ai_response, call_sid)

        gather = Gather(
            input="speech",
            action="/handle-speech",
            method="POST",
            timeout=5,
            speech_timeout=2,
            language="hi-IN",
        )
        gather.play(audio_url)
        response.append(gather)
        response.redirect("/voice-prompt")

    except Exception as e:
        logger.error("Error processing speech (CallSid: %s): %s", call_sid, e)
        try:
            error_url = generate_and_store_audio(
                "Arre beta, phone mein kuch gadbad ho gayi. Ruko thoda...", call_sid
            )
            response.play(error_url)
        except Exception:
            response.say("Sorry, there was an error.", voice="alice")
        response.redirect("/voice-prompt")

    return Response(str(response), mimetype="application/xml")


@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id: str):
    """Serve generated TTS audio to Twilio."""
    audio_bytes = audio_store.get(audio_id)
    if audio_bytes is None:
        return "Audio not found", 404

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/wav",
        download_name=f"{audio_id}.wav",
    )


@app.route("/call-status", methods=["POST"])
def call_status():
    """Twilio webhook: called when call status changes."""
    call_sid = request.form.get("CallSid", "unknown")
    status = request.form.get("CallStatus", "unknown")
    logger.info("Call status update (CallSid: %s): %s", call_sid, status)

    if status in ("completed", "failed", "busy", "no-answer", "canceled"):
        conversation_mgr.end_conversation(call_sid)
        mute_state.pop(call_sid, None)

        # Clean up stored audio
        keys_to_remove = [k for k in audio_store if k.startswith(call_sid)]
        for key in keys_to_remove:
            del audio_store[key]
        logger.info("Cleaned up %d audio files for call %s", len(keys_to_remove), call_sid)

        # Update DB and broadcast
        db_end_call(call_sid, status)
        broadcast_call_ended(call_sid)

    return "", 200


# ===================================================================
#  WEB MODE — Serve the browser voice-call UI
# ===================================================================

@app.route("/")
def index():
    """Serve the homepage."""
    return render_template("index.html")

@app.route("/live-calls.html")
@app.route("/dashboard/live-calls.html")
def live_calls():
    return render_template("live-calls.html")

@app.route("/analytics.html")
@app.route("/dashboard/analytics.html")
def analytics():
    return render_template("analytics.html")

@app.route("/archive.html")
@app.route("/dashboard/archive.html")
def archive():
    return render_template("archive.html")


# ===================================================================
#  REST API — Stats, calls, archive for frontend dashboards
# ===================================================================

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Aggregate stats for analytics dashboard."""
    stats = get_stats()
    return jsonify(stats)


@app.route("/api/calls", methods=["GET"])
def api_calls():
    """Paginated call history for archive."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    calls = get_call_history(limit, offset)
    total = get_total_calls()
    return jsonify({"calls": calls, "total": total, "limit": limit, "offset": offset})


@app.route("/api/calls/<call_id>/transcript", methods=["GET"])
def api_call_transcript(call_id: str):
    """Full transcript + intel for a specific call."""
    call = get_call(call_id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    messages = get_call_transcript(call_id)
    intel = get_call_intel(call_id)

    return jsonify({
        "call": call,
        "messages": messages,
        "intel": intel,
    })


@app.route("/api/calls/<call_id>/summary", methods=["GET"])
def api_call_summary(call_id: str):
    """AI-generated summary for a call."""
    messages = get_call_transcript(call_id)
    if not messages:
        return jsonify({"error": "No transcript found"}), 404

    intel = get_call_intel(call_id)

    # Build summary prompt
    transcript_text = "\n".join(
        f"{'Scammer' if m['role'] == 'user' else 'AI Dadi'}: {m['content']}"
        for m in messages
    )

    summary_messages = [
        {
            "role": "system",
            "content": (
                "You are a scam analyst. Summarize this scam call transcript. "
                "Include: scammer's tactics, information extracted, how AI wasted their time, "
                "and risk assessment. Keep it concise (3-5 bullet points). Respond in English."
            ),
        },
        {"role": "user", "content": f"Transcript:\n{transcript_text}"},
    ]

    try:
        summary = chat_completion(summary_messages, temperature=0.3)
        return jsonify({"summary": summary, "intel": intel})
    except Exception as e:
        logger.error("Error generating summary: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/active-calls", methods=["GET"])
def api_active_calls():
    """List currently active calls."""
    active = get_active_calls()
    return jsonify({"calls": active})


# ===================================================================
#  Serve frontend dashboard static files
# ===================================================================

# The /dashboard/ route is now handled by the template routes above.


# ===================================================================
#  Health check
# ===================================================================

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Karma AI",
        "mode": MODE,
        "active_conversations": len(conversation_mgr.conversations),
    })


# ===================================================================
#  Run
# ===================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("=" * 50)
    logger.info("  KARMA AI — Reverse Scam Call Agent")
    logger.info("  Mode: %s", MODE.upper())
    logger.info("  LLM: OpenRouter GPT-4o-mini")
    logger.info("  STT: Sarvam saaras:v3")
    logger.info("  TTS: Sarvam bulbul:v3")
    logger.info("=" * 50)

    if MODE in ("web", "both"):
        logger.info("Web interface: http://localhost:%d", port)
    if MODE in ("twilio", "both"):
        logger.info("Twilio webhook: %s/voice", BASE_URL)
    logger.info("Dashboard: http://localhost:%d/dashboard/live-calls.html", port)
    logger.info("Analytics: http://localhost:%d/dashboard/analytics.html", port)
    logger.info("Archive:   http://localhost:%d/dashboard/archive.html", port)

    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
