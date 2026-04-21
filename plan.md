# KARMA AI — Complete Integration Plan

## Current State Analysis

### What's Working
- **Sarvam STT** (saarika:v2.5) — Speech-to-text for Hindi/Hinglish ✅
- **Sarvam TTS** (bulbul:v3) — Text-to-speech with "shubh" voice ✅
- **Sarvam Chat** (sarvam-m) — LLM for conversation ⚠️ (replacing with OpenRouter GPT-4o)
- **Twilio Integration** — Incoming call handling, webhooks, TwiML responses ✅
- **Web Mode** — Browser-based voice call via Socket.IO ✅
- **Conversation Manager** — Per-call history with system prompt ✅
- **Frontend Landing Page** — Beautiful marketing page with animations ✅
- **Frontend Dashboard Pages** — live-calls.html, analytics.html, archive.html (HTML/CSS complete) ✅

### What's Missing / Broken
1. **LLM**: Using Sarvam-m → needs OpenRouter GPT-4o
2. **Dashboard Backend**: No events emitted to live dashboard (only per-call WebSocket events exist)
3. **Live Chat Preview**: Frontend expects `call_started`, `call_ended`, `transcript_message`, `ai_status`, `intel_update` events — none are emitted
4. **Analytics API**: `analytics.html` fetches `GET /api/stats` — endpoint doesn't exist
5. **Archive API**: `archive.html` needs endpoints to fetch historical call data — none exist
6. **Data Persistence**: Everything in-memory, lost on restart — no database
7. **Intelligence Extraction**: System prompt asks dadi to extract info, but no automated parsing
8. **Frontend-Backend URL**: Dashboard pages connect Socket.IO to `localhost` but backend serves on `/` only for web mode

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TWILIO CLOUD                             │
│  Scammer calls → Twilio Number → Webhook to Flask backend       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK BACKEND (app.py)                       │
│                                                                  │
│  ┌──────────┐   ┌──────────────┐   ┌────────────┐              │
│  │ Twilio   │──▶│ Conversation │──▶│ OpenRouter  │              │
│  │ Webhooks │   │   Manager    │   │ GPT-4o LLM │              │
│  └──────────┘   └──────────────┘   └────────────┘              │
│       │                │                  │                      │
│       │                ▼                  │                      │
│       │         ┌──────────────┐          │                      │
│       │         │   SQLite DB  │          │                      │
│       │         │ (calls, msgs,│          │                      │
│       │         │  intel, etc) │          │                      │
│       │         └──────────────┘          │                      │
│       │                │                  │                      │
│       ▼                ▼                  ▼                      │
│  ┌──────────┐   ┌──────────────┐   ┌────────────┐              │
│  │ Sarvam   │   │  Socket.IO   │   │ Sarvam TTS │              │
│  │   STT    │   │  (broadcast  │   │ (bulbul:v3)│              │
│  │(saarika) │   │  to dashboard│   │            │              │
│  └──────────┘   │  clients)    │   └────────────┘              │
│                  └──────────────┘                                │
│                        │                                         │
│          ┌─────────────┼──────────────┐                         │
│          ▼             ▼              ▼                          │
│    REST APIs      WebSocket      Static Files                   │
│   /api/stats    /transcript     /frontend/*                     │
│   /api/calls    /call_started                                   │
│   /api/archive  /intel_update                                   │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND DASHBOARD                           │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ live-calls   │ │  analytics   │ │   archive    │            │
│  │   .html      │ │    .html     │ │    .html     │            │
│  │              │ │              │ │              │            │
│  │ Socket.IO    │ │ REST API     │ │ REST API     │            │
│  │ real-time    │ │ /api/stats   │ │ /api/calls   │            │
│  │ transcript   │ │              │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan (Step by Step)

### Phase 1: OpenRouter GPT-4o Integration
**Files**: `backend/sarvam_service.py`, `backend/.env`

1. **Add OpenRouter API key to `.env`**
   ```
   OPENROUTER_API_KEY=<key>
   ```

2. **Create `backend/llm_service.py`** — OpenRouter GPT-4o chat completion
   - Endpoint: `https://openrouter.ai/api/v1/chat/completions`
   - Model: `openai/gpt-4o`
   - Headers: `Authorization: Bearer <key>`, `Content-Type: application/json`
   - Same function signature as current `chat_completion()`: takes messages list, returns string
   - Keep temperature=0.8, max_tokens=300
   - The system prompt is in Hinglish so GPT-4o handles it natively

3. **Update `backend/app.py`** — Import from `llm_service` instead of `sarvam_service.chat_completion`
   - Change: `from sarvam_service import speech_to_text, text_to_speech` (remove chat_completion)
   - Add: `from llm_service import chat_completion`
   - Everything else stays the same — STT and TTS still use Sarvam

4. **Remove `chat_completion` from `sarvam_service.py`** — Keep only STT and TTS functions

---

### Phase 2: SQLite Database for Persistence
**Files**: `backend/database.py` (new)

1. **Create `backend/database.py`** with SQLite schema:
   ```sql
   -- Calls table
   CREATE TABLE calls (
     id TEXT PRIMARY KEY,           -- CallSid or session ID
     caller_number TEXT,
     start_time DATETIME,
     end_time DATETIME,
     duration_seconds INTEGER,
     status TEXT,                    -- active, completed, failed
     mode TEXT,                      -- web, twilio
     threat_level TEXT DEFAULT 'HIGH'
   );

   -- Messages table
   CREATE TABLE messages (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     call_id TEXT REFERENCES calls(id),
     role TEXT,                      -- user/assistant
     content TEXT,
     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
   );

   -- Intel table (extracted scammer info)
   CREATE TABLE intel (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     call_id TEXT REFERENCES calls(id),
     field_name TEXT,               -- name, upi_id, bank_branch, address, phone, etc.
     field_value TEXT,
     confidence REAL DEFAULT 0.5,
     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Database helper functions**:
   - `init_db()` — Create tables if not exist
   - `create_call(call_id, caller, mode)` — Insert new call
   - `end_call(call_id)` — Set end_time, calculate duration
   - `save_message(call_id, role, content)` — Insert message
   - `save_intel(call_id, field, value)` — Insert intel data
   - `get_active_calls()` — Fetch calls with status='active'
   - `get_call_history(limit, offset)` — Paginated call history
   - `get_call_transcript(call_id)` — All messages for a call
   - `get_stats()` — Aggregate stats (total calls, avg duration, etc.)

---

### Phase 3: Intelligence Extraction
**Files**: `backend/intel_extractor.py` (new)

1. **Create `backend/intel_extractor.py`** — Lightweight regex + keyword extraction
   - Extract from scammer messages:
     - **UPI IDs**: regex `[a-zA-Z0-9.]+@[a-zA-Z]+` (e.g., `name@paytm`)
     - **Phone numbers**: regex for Indian phone numbers
     - **Names**: When scammer says "Main <name> bol raha hoon" or "I am <name>"
     - **Bank names**: Match against known bank keywords (SBI, HDFC, ICICI, etc.)
     - **Account numbers**: Long digit sequences (10+ digits)
     - **Scam type detection**: Keywords → categorize as KYC fraud, lottery, tech support, etc.
     - **Organization claimed**: "I am from <org>" patterns

2. **Run extraction after each scammer message** — Non-blocking, save to intel table
3. **Emit `intel_update` via Socket.IO** when new intel is found

---

### Phase 4: Connect Backend to Live Dashboard
**Files**: `backend/app.py`

This is the critical integration. The frontend `live-calls.html` expects these Socket.IO events:

#### Events the dashboard listens for:
| Event | Payload | When |
|-------|---------|------|
| `call_started` | `{call_sid, caller, timestamp}` | New call comes in |
| `call_ended` | `{call_sid, duration}` | Call terminates |
| `transcript_message` | `{speaker: 'scammer'\|'ai', text, call_sid}` | Each message |
| `ai_status` | `{status: 'ANALYZING...'\|'DEFENDING'\|'ACTIVE'}` | Processing stages |
| `intel_update` | `{scammer_name, location, scam_type, organization_claimed}` | Intel extracted |

#### Events the dashboard emits:
| Event | Payload | Purpose |
|-------|---------|---------|
| `mute_ai` | `{call_sid, muted}` | Mute AI responses |
| `drop_call` | `{call_sid}` | Terminate call |

#### Implementation:
1. **Use Socket.IO rooms** — Dashboard clients join a `dashboard` room
2. **On dashboard connect**: Join `dashboard` room, send list of active calls
3. **In Twilio `/voice` handler**: After creating conversation, broadcast `call_started` to dashboard room
4. **In `/handle-speech` handler**:
   - Broadcast `ai_status: ANALYZING...` → when scammer speech received
   - Broadcast `transcript_message` (speaker: scammer) → with scammer's text
   - Broadcast `ai_status: DEFENDING` → when AI responds
   - Broadcast `transcript_message` (speaker: ai) → with AI response
   - Run intel extraction → broadcast `intel_update` if found
5. **In `/call-status` handler**: Broadcast `call_ended` to dashboard room
6. **Handle `mute_ai`**: Store mute state per call, skip AI response when muted
7. **Handle `drop_call`**: Use Twilio API to end the call programmatically

#### Dashboard Socket.IO namespace:
- Use default namespace `/` but distinguish dashboard vs web-call clients
- Dashboard connects with query param: `io({ query: { role: 'dashboard' } })`
- On connect, check query param and join `dashboard` room
- Web mode clients don't need this since they connect for voice

---

### Phase 5: REST API Endpoints
**Files**: `backend/app.py`

1. **`GET /api/stats`** — For analytics.html
   ```json
   {
     "total_calls": 42,
     "avg_duration_seconds": 187,
     "total_time_wasted_seconds": 7854,
     "active_calls": 1,
     "intel_extracted": 23,
     "success_rate": 95.2,
     "calls_today": 5,
     "calls_this_week": [12, 18, 22, 30, 26, 42, 55]
   }
   ```

2. **`GET /api/calls`** — For archive.html
   ```json
   {
     "calls": [
       {
         "id": "CA_xxxx",
         "caller": "+91XXXXXXXXXX",
         "start_time": "2024-01-15T14:22:04",
         "duration": 245,
         "status": "completed",
         "threat_level": "HIGH",
         "intel_count": 3,
         "message_count": 12
       }
     ],
     "total": 42,
     "page": 1
   }
   ```

3. **`GET /api/calls/<call_id>/transcript`** — For archive detail view
   ```json
   {
     "call_id": "CA_xxxx",
     "messages": [
       {"role": "assistant", "content": "Haaaan?...", "timestamp": "..."},
       {"role": "user", "content": "Hello madam...", "timestamp": "..."}
     ],
     "intel": [
       {"field": "scam_type", "value": "KYC Fraud"},
       {"field": "organization_claimed", "value": "State Bank of India"}
     ]
   }
   ```

4. **`GET /api/calls/<call_id>/summary`** — AI-generated call summary
   - Use OpenRouter GPT-4o to summarize the conversation
   - Extract key scammer tactics, extracted info, duration analysis

---

### Phase 6: Serve Frontend from Flask
**Files**: `backend/app.py`

1. **Serve frontend static files** from Flask:
   ```python
   @app.route('/dashboard/')
   @app.route('/dashboard/<path:filename>')
   def serve_frontend(filename='index.html'):
       return send_from_directory('../frontend', filename)
   ```
   - `/dashboard/` → `frontend/index.html` (landing page)
   - `/dashboard/live-calls.html` → live dashboard
   - `/dashboard/analytics.html` → analytics
   - `/dashboard/archive.html` → archive

2. **Update frontend Socket.IO connection** in `live-calls.html`:
   - Connect to backend URL (same origin since served by Flask)
   - Add `query: { role: 'dashboard' }` to Socket.IO connection
   ```javascript
   const socket = io({
     transports: ['websocket', 'polling'],
     query: { role: 'dashboard' }
   });
   ```

3. **Update frontend API calls**:
   - `analytics.html` already fetches `/api/stats` — just needs the endpoint
   - `archive.html` needs JS to fetch `/api/calls` and render

---

### Phase 7: Archive Page Dynamic Loading
**Files**: `frontend/archive.html`

The archive page currently has hardcoded demo data. Add JS to:
1. On page load, fetch `GET /api/calls`
2. Render call cards dynamically
3. On click, fetch `/api/calls/<id>/transcript` and show in detail panel
4. Wire up "Generate Summary" button to `/api/calls/<id>/summary`

---

### Phase 8: Low Latency Optimizations

1. **Streaming LLM response**: Use OpenRouter streaming API to get tokens as they arrive
   - Start TTS generation as soon as first sentence is complete
   - Don't wait for full LLM response before generating speech

2. **Audio compression**: Reduce WAV payload sizes
   - Use 8000 Hz sample rate for Twilio (already done)
   - Consider mp3/opus for web mode instead of WAV

3. **Connection pooling**: Use `requests.Session()` for API calls
   - Reuse HTTP connections to Sarvam and OpenRouter
   - Reduces TCP handshake overhead

4. **Sentence-level TTS**: Split long AI responses into sentences
   - Generate TTS for first sentence immediately
   - Stream subsequent sentences as they're generated

5. **WebSocket transport priority**: Already using `['websocket', 'polling']`
   - WebSocket is faster than polling for real-time data

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/.env` | EDIT | Add `OPENROUTER_API_KEY` |
| `backend/llm_service.py` | NEW | OpenRouter GPT-4o chat completion |
| `backend/database.py` | NEW | SQLite DB schema + helper functions |
| `backend/intel_extractor.py` | NEW | Regex-based scammer intel extraction |
| `backend/sarvam_service.py` | EDIT | Remove `chat_completion` (keep STT + TTS only) |
| `backend/app.py` | EDIT | Major — add dashboard events, REST APIs, DB integration, serve frontend |
| `backend/requirements.txt` | EDIT | Add `openai` (for OpenRouter client) |
| `frontend/live-calls.html` | EDIT | Update Socket.IO connection with dashboard query param |
| `frontend/analytics.html` | EDIT | Minor — API URL already correct |
| `frontend/archive.html` | EDIT | Add dynamic data loading JS |

---

## Execution Order

1. ✅ Phase 1 — OpenRouter GPT-4o (replace LLM, keep STT/TTS)
2. ✅ Phase 2 — SQLite Database (persistence layer)
3. ✅ Phase 3 — Intel Extractor (auto-extract scammer info)
4. ✅ Phase 4 — Dashboard Socket.IO (real-time live chat preview)
5. ✅ Phase 5 — REST APIs (analytics + archive data)
6. ✅ Phase 6 — Serve Frontend (unified server)
7. ✅ Phase 7 — Archive Dynamic Loading
8. ✅ Phase 8 — Latency Optimizations

---

## Environment Variables Needed

```env
# Existing
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
SARVAM_API_KEY=...
PORT=5000
BASE_URL=https://xxxx.ngrok-free.app
MODE=both

# New
OPENROUTER_API_KEY=...   # Required — for GPT-4o LLM
```

---

## Testing Checklist

- [ ] OpenRouter GPT-4o responds in Hinglish with dadi personality
- [ ] Sarvam STT correctly transcribes Hindi speech
- [ ] Sarvam TTS generates natural Hindi speech
- [ ] Twilio call flow works end-to-end
- [ ] Dashboard shows real-time transcript during call
- [ ] Intel extraction picks up UPI IDs, names, bank info
- [ ] Analytics page loads real stats from `/api/stats`
- [ ] Archive page loads call history from `/api/calls`
- [ ] Call summary generation works via GPT-4o
- [ ] Timer, session ID, threat level update in real-time
- [ ] Mute AI and Drop Call buttons work from dashboard
- [ ] DB persists across server restarts
