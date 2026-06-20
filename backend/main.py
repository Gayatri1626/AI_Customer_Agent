"""
ShopEase AI Customer Support — FastAPI backend.

Endpoints:
  POST /api/chat          — send a message, get streaming agent response
  WS   /ws/logs/{session} — real-time agent reasoning log stream
  POST /api/voice/session — create an OpenAI Realtime API session token
  GET  /api/customers     — list all CRM customers (admin)
  GET  /api/customers/{id}— get single customer (admin)
  GET  /api/refund-policy — return the policy document
"""
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel

# Load .env from the same directory as this file, regardless of cwd
_HERE = Path(__file__).parent
load_dotenv(dotenv_path=_HERE / ".env")

from agent.graph import get_graph
from data.crm_database import list_all_customers, get_customer_by_id
from data.refund_policy import get_policy_text

# Fail at startup if the API key is missing — avoids cryptic mid-request errors
if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(
        "\n\nOPENAI_API_KEY not found.\n"
        f"Create a .env file in {_HERE} with:\n"
        "  OPENAI_API_KEY=sk-...\n"
        "Or copy .env.example → .env and fill in your key.\n"
    )

app = FastAPI(title="ShopEase AI Customer Support", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID", "Content-Type"],
)

# ── In-memory session store ──────────────────────────────────────────────────
# Maps session_id -> list of log entries for admin dashboard
SESSION_LOGS: dict[str, list[dict]] = {}
# Active WebSocket connections: session_id -> [WebSocket]
WS_CONNECTIONS: dict[str, list[WebSocket]] = {}
# Conversation histories: session_id -> list of LangChain messages
CONVERSATIONS: dict[str, list] = {}


# ── WebSocket log broadcaster ────────────────────────────────────────────────
import time as _time

async def broadcast_log(session_id: str, entry: dict):
    """Append to session log and push to all relevant WebSocket listeners,
    including any admin dashboard connections registered under __admin__."""
    entry.setdefault("session_id", session_id)
    entry.setdefault("timestamp", _time.time())

    # Ensure the entry is JSON-serializable before storing or sending.
    # Any non-serializable values (e.g. LangChain objects) are converted to strings.
    try:
        safe_entry = json.loads(json.dumps(entry, default=str))
    except Exception:
        safe_entry = {"type": entry.get("type", "unknown"), "content": str(entry), "session_id": session_id}

    SESSION_LOGS.setdefault(session_id, []).append(safe_entry)

    # Broadcast to session-specific listeners AND the admin wildcard channel
    targets = list(WS_CONNECTIONS.get(session_id, [])) + list(WS_CONNECTIONS.get("__admin__", []))
    for ws in targets:
        try:
            await ws.send_json(safe_entry)
        except Exception:
            pass


# ── Chat endpoint ────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def run_agent_stream(
    user_message: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    graph = get_graph()
    history = CONVERSATIONS.setdefault(session_id, [])
    history.append(HumanMessage(content=user_message))

    await broadcast_log(session_id, {
        "type": "user_message",
        "content": user_message,
        "session_id": session_id,
    })

    state = {
        "messages": history,
        "customer": None,
        "order": None,
        "decision": None,
        "decision_reason": None,
        "session_id": session_id,
    }

    final_text = ""

    async for event in graph.astream_events(state, version="v2"):
        kind = event["event"]
        name = event.get("name", "")
        data = event.get("data", {})

        # ── Tool call start ──
        if kind == "on_tool_start":
            tool_name = name
            tool_input = data.get("input", {})
            log_entry = {
                "type": "tool_call",
                "tool": tool_name,
                "input": tool_input,
                "session_id": session_id,
            }
            await broadcast_log(session_id, log_entry)
            yield f"data: {json.dumps({'type': 'reasoning', 'content': f'🔧 Calling tool: {tool_name}...'})}\n\n"

        # ── Tool call end ──
        elif kind == "on_tool_end":
            tool_name = name
            raw = data.get("output", "")
            # LangGraph v2: output is a ToolMessage object, not a plain string
            if hasattr(raw, "content"):
                output_str = raw.content  # extract string content from ToolMessage
            elif isinstance(raw, str):
                output_str = raw
            else:
                output_str = str(raw)
            # Try to parse as JSON for pretty display; fall back to raw string
            try:
                parsed_output: dict | str = json.loads(output_str)
            except Exception:
                parsed_output = output_str
            log_entry = {
                "type": "tool_result",
                "tool": tool_name,
                "output": parsed_output,
                "session_id": session_id,
            }
            await broadcast_log(session_id, log_entry)
            yield f"data: {json.dumps({'type': 'reasoning', 'content': f'✅ {tool_name} returned result'})}\n\n"

        # ── LLM streaming tokens ──
        elif kind == "on_chat_model_stream":
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                token = chunk.content
                final_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # ── LLM thinking (tool call decision) ──
        elif kind == "on_chat_model_end":
            output = data.get("output")
            if output and hasattr(output, "tool_calls") and output.tool_calls:
                for tc in output.tool_calls:
                    await broadcast_log(session_id, {
                        "type": "agent_thinking",
                        "content": f"Agent decided to call: {tc['name']}",
                        "session_id": session_id,
                    })

    # Store assistant reply in history
    if final_text:
        history.append(AIMessage(content=final_text))
        await broadcast_log(session_id, {
            "type": "assistant_message",
            "content": final_text,
            "session_id": session_id,
        })

    yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"


@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    return StreamingResponse(
        run_agent_stream(request.message, session_id),
        media_type="text/event-stream",
        headers={
            "X-Session-ID": session_id,
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",   # disables nginx/proxy buffering
            "Connection": "keep-alive",
        },
    )


# ── WebSocket proxy → OpenAI Realtime API ────────────────────────────────────
VOICE_SYSTEM_PROMPT = (
    "You are a professional AI customer support agent for ShopEase, an e-commerce platform. "
    "Help customers with refund requests. Be empathetic, concise, and clear. "
    "When a customer tells you their issue, ask for their order ID if not provided. "
    "Explain the policy and outcome clearly. Keep responses brief for voice — 2-3 sentences max."
)

REALTIME_MODELS = [
    "gpt-4o-realtime-preview",
    "gpt-4o-mini-realtime-preview",
    "gpt-4o-realtime-preview-2024-12-17",
    "gpt-4o-realtime-preview-2024-10-01",
]


@app.websocket("/ws/voice")
async def voice_proxy(websocket: WebSocket):
    """
    Proxies browser ↔ OpenAI Realtime API over WebSocket.
    The browser sends/receives raw Realtime API JSON events.
    Audio format: PCM16, 24kHz, mono (base64-encoded).
    """
    import websockets as ws_lib

    await websocket.accept()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        await websocket.close(code=1011, reason="OPENAI_API_KEY not configured")
        return

    oai_ws = None
    connected_model = None

    # Try each model until one connects
    for model in REALTIME_MODELS:
        try:
            oai_ws = await ws_lib.connect(
                f"wss://api.openai.com/v1/realtime?model={model}",
                additional_headers={
                    "Authorization": f"Bearer {api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
                open_timeout=10,
            )
            connected_model = model
            break
        except Exception as e:
            print(f"[voice] Model {model} failed: {e}")
            continue

    if oai_ws is None:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": {
                "message": (
                    "Could not connect to OpenAI Realtime API. "
                    "Ensure your API key has Realtime API access (tier 2+)."
                )
            }
        }))
        await websocket.close(code=1011)
        return

    print(f"[voice] Connected to OpenAI Realtime using model: {connected_model}")

    # Send initial session configuration
    await oai_ws.send(json.dumps({
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": VOICE_SYSTEM_PROMPT,
            "voice": "alloy",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {"model": "whisper-1"},
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 600,
            },
        },
    }))

    # Notify browser that proxy is ready
    await websocket.send_text(json.dumps({
        "type": "proxy.ready",
        "model": connected_model,
    }))

    async def browser_to_oai():
        """Forward browser → OpenAI."""
        try:
            async for msg in websocket.iter_text():
                if oai_ws.open:
                    await oai_ws.send(msg)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[voice] browser→oai error: {e}")

    async def oai_to_browser():
        """Forward OpenAI → browser."""
        try:
            async for msg in oai_ws:
                text = msg if isinstance(msg, str) else msg.decode()
                await websocket.send_text(text)
        except Exception as e:
            print(f"[voice] oai→browser error: {e}")

    try:
        await asyncio.gather(browser_to_oai(), oai_to_browser())
    finally:
        if oai_ws and oai_ws.open:
            await oai_ws.close()


# ── WebSocket for admin reasoning logs ──────────────────────────────────────
@app.websocket("/ws/logs/{session_id}")
async def websocket_logs(websocket: WebSocket, session_id: str):
    await websocket.accept()
    WS_CONNECTIONS.setdefault(session_id, []).append(websocket)
    # Send existing logs immediately
    for entry in SESSION_LOGS.get(session_id, []):
        await websocket.send_json(entry)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        WS_CONNECTIONS[session_id].remove(websocket)


@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """Admin WebSocket — receives logs from ALL sessions."""
    await websocket.accept()
    WS_CONNECTIONS.setdefault("__admin__", []).append(websocket)
    try:
        # Send recent history from all sessions
        all_logs = []
        for session_id, logs in SESSION_LOGS.items():
            if session_id == "__admin__":
                continue  # WS_CONNECTIONS key, not a real session
            all_logs.extend(logs)
        # Use 0 as default so float comparison never fails
        all_logs.sort(key=lambda x: x.get("timestamp", 0))
        for entry in all_logs[-200:]:
            try:
                await websocket.send_json(entry)
            except Exception:
                return  # client gone during initial dump
        # Keep-alive ping loop — catch everything so exceptions don't kill the socket
        while True:
            await asyncio.sleep(15)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break  # connection closed, exit cleanly
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[admin ws] error: {e}")
    finally:
        lst = WS_CONNECTIONS.get("__admin__", [])
        if websocket in lst:
            lst.remove(websocket)


# ── Voice: OpenAI Realtime API session ──────────────────────────────────────
@app.post("/api/voice/session")
async def create_voice_session():
    """Creates an ephemeral token for the OpenAI Realtime API (WebRTC).
    Requires an API key with access to gpt-4o-realtime-preview.
    Returns 503 with a clear message if the model is unavailable.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # Try the latest Realtime model; fall back to the dated version if needed
    for model in ["gpt-4o-realtime-preview", "gpt-4o-realtime-preview-2024-12-17"]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "voice": "alloy",
                    "instructions": (
                        "You are a professional AI customer support agent for ShopEase. "
                        "Help customers with refund requests. Be empathetic and clear. "
                        "When a customer describes their issue, acknowledge their concern, "
                        "ask for their order ID if not provided, and explain what you're checking."
                    ),
                    "turn_detection": {"type": "server_vad"},
                },
            )
            if response.status_code == 200:
                return response.json()
            # If 404 or 400, try next model; if auth error, fail immediately
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI auth error: {response.text}",
                )

    # Both models failed — voice not available on this API key tier
    raise HTTPException(
        status_code=503,
        detail=(
            "Voice unavailable: the OpenAI Realtime API requires a paid API key "
            "with gpt-4o-realtime-preview access. Chat mode works without it."
        ),
    )


# ── TTS: OpenAI text-to-speech (works on any paid API key) ──────────────────
class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"  # alloy | echo | fable | onyx | nova | shimmer


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using OpenAI TTS (tts-1 model).
    Returns an audio/mpeg stream the browser can play directly.
    Works with any standard OpenAI API key — no Realtime API tier needed.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # Truncate very long responses to keep latency reasonable
    text = request.text.strip()[:4000]
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    async def audio_stream():
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": request.voice,
                    "response_format": "mp3",
                },
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"OpenAI TTS error: {body.decode()}",
                    )
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )



# ── Admin: Customer list ──────────────────────────────────────────────────────
@app.get("/api/customers")
async def get_customers():
    customers = list_all_customers()
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "email": c["email"],
            "tier": c["tier"],
            "member_since": c["member_since"],
            "orders": c["orders"],
        }
        for c in customers
    ]


@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: str):
    customer = get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/api/refund-policy")
async def refund_policy():
    return {"policy": get_policy_text()}


@app.get("/api/sessions")
async def get_sessions():
    """List all chat sessions with log counts (admin)."""
    return [
        {"session_id": sid, "log_count": len(logs)}
        for sid, logs in SESSION_LOGS.items()
        if sid != "__admin__"
    ]


@app.get("/api/sessions/{session_id}/logs")
async def get_session_logs(session_id: str):
    return SESSION_LOGS.get(session_id, [])


@app.get("/health")
async def health():
    return {"status": "ok"}
