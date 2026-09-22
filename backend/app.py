import os
import re
import json
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.agent.core import StackyAgent
from backend.tools.os_control import get_system_diagnostics
from backend.voice.tts import synthesize_speech
from backend.comms.hub import CommunicationsHub

from backend.config import STACKY_MASTER_KEY

logger = logging.getLogger("StackyApp")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Stacky-OS // Autonomous Sovereign Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes accessible without Master Key (webhooks & health probes)
PUBLIC_ROUTES = {
    "/",
    "/api/health",
    "/api/auth/verify",
    "/api/telegram/webhook",
    "/api/twilio/voice",
    "/api/twilio/gather",
    "/docs",
    "/openapi.json"
}

@app.middleware("http")
async def sovereign_auth_gate(request: Request, call_next):
    """Enforces Sovereign Master Key authentication for all remote cloud requests."""
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Always permit local loopback requests, public webhooks, and static files
    if (
        client_ip in ["127.0.0.1", "localhost", "::1"]
        or path in PUBLIC_ROUTES
        or path.startswith("/static")
        or request.method == "OPTIONS"
        or not STACKY_MASTER_KEY
    ):
        return await call_next(request)

    # Remote cloud access requires Master Key validation
    auth_header = request.headers.get("X-Stacky-Key") or request.headers.get("Authorization", "")
    token = request.query_params.get("key") or request.query_params.get("token")

    if (
        auth_header == STACKY_MASTER_KEY 
        or f"Bearer {STACKY_MASTER_KEY}" in auth_header 
        or token == STACKY_MASTER_KEY
    ):
        return await call_next(request)

    return Response(
        content=json.dumps({"detail": "Access Denied: Sovereign Master Authorization Key required to command Stacky."}),
        status_code=401,
        media_type="application/json"
    )

agent = StackyAgent()
comms_hub = CommunicationsHub()

# ==========================================================
# WEBSOCKET CONNECTION MANAGER FOR PRESENCE & REALTIME SYNC
# ==========================================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.current_task: str = "listening"
        self.current_status: str = "Listening..."

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Immediately sync current presence state
        await websocket.send_json({
            "type": "presence_state",
            "task": self.current_task,
            "status_text": self.current_status
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def set_presence(self, task: str, status_text: Optional[str] = None):
        """Broadcast state update: 'listening' | 'working' | 'searching' | 'explaining'."""
        self.current_task = task
        if status_text:
            self.current_status = status_text
        elif task == "listening":
            self.current_status = "Listening..."
        elif task == "working":
            self.current_status = "Working..."
        elif task == "searching":
            self.current_status = "Searching..."
        elif task == "explaining":
            self.current_status = "Explaining..."

        await self.broadcast({
            "type": "presence_state",
            "task": self.current_task,
            "status_text": self.current_status
        })

manager = ConnectionManager()

# ==========================================================
# REQUEST SCHEMAS
# ==========================================================
class ChatRequest(BaseModel):
    message: str

class CallRequest(BaseModel):
    phone_number: Optional[str] = None

class PresenceStateRequest(BaseModel):
    task: str
    status_text: Optional[str] = None

class AuthVerifyRequest(BaseModel):
    key: str

# ==========================================================
# API ENDPOINTS
# ==========================================================
@app.post("/api/auth/verify")
async def verify_master_key(req: AuthVerifyRequest):
    """Verify Master Key for web dashboard login."""
    if req.key == STACKY_MASTER_KEY:
        return {"status": "authorized", "message": "Master Key verified, Sir."}
    return Response(
        content=json.dumps({"detail": "Invalid Master Key."}),
        status_code=401,
        media_type="application/json"
    )
@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "name": "Stacky",
        "presence_task": manager.current_task,
        "diagnostics": get_system_diagnostics()
    }

@app.post("/api/presence/state")
async def update_presence_state(req: PresenceStateRequest):
    """Programmatically trigger notch bar state."""
    await manager.set_presence(req.task, req.status_text)
    return {"status": "ok", "task": req.task, "status_text": manager.current_status}

def make_spoken_summary(full_text: str, query: str) -> str:
    """Condenses long explanations into 1-2 punchy spoken sentences for Mac voice output."""
    text = re.sub(r'```[\s\S]*?```', '', full_text)
    lines = [line.strip() for line in text.split('\n')]
    valid_sentences = []
    for line in lines:
        if not line or line.startswith(('#', '-', '*', '>', '|')):
            continue
        clean_line = re.sub(r'\*\*|\*|`|\[.*?\]\(.*?\)', '', line)
        for s in re.split(r'(?<=[.!?])\s+', clean_line):
            s = s.strip()
            if len(s) > 15:
                valid_sentences.append(s)

    summary = ""
    for s in valid_sentences:
        if len(summary) + len(s) < 220:
            summary = (summary + " " + s).strip()
        else:
            break
    if not summary:
        summary = "Here is the briefing you requested, Sir."
    return summary

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.lower()
    
    # Intelligently determine if searching or working
    if any(k in user_msg for k in ["search", "scan", "inbox", "email", "whatsapp", "memory", "recall", "research", "find"]):
        await manager.set_presence("searching", "Searching inboxes & archives...")
    else:
        await manager.set_presence("working", "Processing & computing...")

    result = await agent.chat(req.message)
    full_reply = result["reply"]

    # Automatic Split Mode: Quick answers spoken on Mac; Long/Research answers summarized on Mac + full notes to Telegram
    word_count = len(full_reply.split())
    is_long_answer = word_count > 45 or "\n\n" in full_reply or "```" in full_reply or any(k in user_msg for k in ["telegram", "notes", "briefing", "detail"])

    spoken_summary = full_reply
    telegram_dispatched = False

    if is_long_answer:
        core_summary = make_spoken_summary(full_reply, req.message)
        spoken_summary = f"{core_summary} I have sent the full detailed briefing to your Telegram."

        # Automatically dispatch full detailed research note to Telegram
        tg_text = f"📋 *Stacky Intelligence Briefing*\n*Query:* {req.message}\n\n{full_reply}"
        try:
            from backend.comms.telegram_bridge import telegram_bridge
            tg_res = telegram_bridge.send_text_message(tg_text)
            telegram_dispatched = tg_res.get("status") in ["SUCCESS", "SIMULATED_SUCCESS"]
        except Exception as e:
            logger.warning(f"Auto-dispatch to Telegram failed: {e}")

    # Deliver response in explaining mode
    await manager.set_presence("explaining", "Explaining solution...")
    
    res_data = {
        "reply": full_reply,
        "spoken_summary": spoken_summary,
        "is_split_mode": is_long_answer,
        "telegram_dispatched": telegram_dispatched,
        "tools_used": result.get("tools_used", []),
        "diagnostics": get_system_diagnostics()
    }
    return res_data

@app.post("/api/comms/scan")
async def scan_inboxes():
    """Trigger inbox perception and scan all channels."""
    await manager.set_presence("searching", "Scanning incoming inboxes...")
    res = await comms_hub.scan_and_process_all_inboxes()
    await manager.set_presence("listening", "Listening...")
    return res

@app.post("/api/comms/call")
async def trigger_briefing_call(req: Optional[CallRequest] = None):
    """Trigger voice phone call briefing."""
    await manager.set_presence("explaining", "Initiating voice briefing call...")
    phone = req.phone_number if req else None
    res = await comms_hub.execute_phone_briefing(phone)
    await manager.set_presence("listening", "Listening...")
    return res

@app.get("/api/tts")
async def tts_endpoint(text: str):
    """Synthesize speech on demand."""
    try:
        audio_bytes = await synthesize_speech(text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        return Response(content=f"TTS error: {str(e)}", status_code=500)

# ==========================================================
# STEP 5: TWILIO INTERACTIVE TWO-WAY VOICE WEBHOOKS
# ==========================================================
@app.post("/api/twilio/voice")
async def twilio_voice_webhook():
    """Initial TwiML greeting when user answers Stacky's phone call."""
    await manager.set_presence("explaining", "On Voice Call with User...")
    briefing = comms_hub.caller.generate_briefing_speech(
        auto_replied=comms_hub.auto_replied_history[-3:],
        held_for_review=comms_hub.held_for_review
    )
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Brian" language="en-GB">{briefing}</Say>
    <Gather input="speech" action="/api/twilio/gather" timeout="6" speechTimeout="auto">
        <Say voice="Polly.Brian" language="en-GB">What instructions do you have for me, Sir?</Say>
    </Gather>
    <Say voice="Polly.Brian" language="en-GB">I did not catch that, Sir. Standing by. Have a productive evening.</Say>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/twilio/gather")
async def twilio_gather_webhook(request: Request):
    """Two-way interactive speech processing during the phone call."""
    form_data = await request.form()
    user_speech = form_data.get("SpeechResult", "").strip()
    logger.info(f"[Twilio Voice User Spoke]: '{user_speech}'")

    if not user_speech:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Brian" language="en-GB">I didn't detect any instructions, Sir. Closing connection.</Say>
</Response>
"""
        await manager.set_presence("listening", "Listening...")
        return Response(content=twiml, media_type="application/xml")

    # Pass voice command to Stacky Brain
    await manager.set_presence("working", f"Executing phone command: {user_speech[:30]}...")
    agent_res = await agent.chat(user_speech)
    reply_text = agent_res.get("reply", "Understood, Sir. Action complete.")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Brian" language="en-GB">{reply_text}</Say>
    <Gather input="speech" action="/api/twilio/gather" timeout="5" speechTimeout="auto">
        <Say voice="Polly.Brian" language="en-GB">Anything else, Sir?</Say>
    </Gather>
    <Say voice="Polly.Brian" language="en-GB">All systems secured, Sir. Goodbye.</Say>
</Response>
"""
# ==========================================================
# TELEGRAM CLOUD WEBHOOK (FOR 24/7 RENDER CLOUD HOSTING)
# ==========================================================
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive live messages from Telegram via cloud webhook with zero polling."""
    from backend.comms.telegram_bridge import telegram_bridge
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return {"ok": True}

    sender = message.get("from", {})
    sender_id = str(sender.get("id", ""))
    text = message.get("text", "").strip()

    # Security Gate: only the authorized user ID is permitted
    allowed_id = str(telegram_bridge.allowed_user_id) if telegram_bridge.allowed_user_id else None
    if allowed_id and sender_id != allowed_id:
        logger.warning(f"[Unauthorized Telegram access attempt]: Sender {sender_id}")
        return {"ok": True}

    if not text:
        return {"ok": True}

    if text == "/start":
        greeting = (
            "⚡ *STACKY AI // CLOUD READY*\n"
            "Welcome, Sir. Stacky is running 24/7 in the cloud powered by Groq ultra-fast LPU inference.\n"
            "Awaiting your instruction."
        )
        telegram_bridge.send_text_message(greeting)
        return {"ok": True}

    # Pass command directly to Stacky Brain (powered by Groq)
    agent_res = await agent.chat(text)
    reply = agent_res.get("reply", "Task completed, Sir.")
    telegram_bridge.send_text_message(reply)

    return {"ok": True}

# ==========================================================
# MASTER REALTIME WEBSOCKET
# ==========================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "message": "Connected to Stacky AI Realtime Kernel.",
            "diagnostics": get_system_diagnostics()
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                user_msg = data.get("message", "")
                
                if any(k in user_msg.lower() for k in ["search", "scan", "inbox", "email", "whatsapp", "memory", "recall", "research"]):
                    await manager.set_presence("searching", "Searching...")
                else:
                    await manager.set_presence("working", "Reasoning...")

                result = await agent.chat(user_msg)

                await manager.set_presence("explaining", "Delivering response...")

                audio_b64 = None
                try:
                    audio_data = await synthesize_speech(result["reply"])
                    audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                except Exception:
                    pass

                await websocket.send_json({
                    "type": "response",
                    "reply": result["reply"],
                    "tools_used": result.get("tools_used", []),
                    "audio": audio_b64,
                    "diagnostics": get_system_diagnostics()
                })
                
                await manager.set_presence("listening", "Listening...")

            elif msg_type == "set_presence":
                task = data.get("task", "listening")
                status_text = data.get("status_text")
                await manager.set_presence(task, status_text)

            elif msg_type == "interrupt":
                logger.info("[Voice Barge-in Triggered]: Interrupting audio playback.")
                await manager.set_presence("listening", "Listening (Interrupted)...")

            elif msg_type == "telemetry":
                await websocket.send_json({
                    "type": "telemetry",
                    "diagnostics": get_system_diagnostics()
                })

            elif msg_type == "scan_inbox":
                await manager.set_presence("searching", "Scanning inboxes...")
                scan_res = await comms_hub.scan_and_process_all_inboxes()
                await websocket.send_json({
                    "type": "comms_update",
                    "data": scan_res
                })
                await manager.set_presence("listening", "Listening...")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        logger.warning(f"WebSocket session terminated: {e}")

# Mount static frontend assets
static_path = Path(__file__).resolve().parent.parent / "frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
