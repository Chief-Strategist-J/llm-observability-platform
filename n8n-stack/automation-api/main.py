import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(message)s")
logger = logging.getLogger("automation")

N8N_BASE = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_WEBHOOK_PATH = os.getenv("N8N_WEBHOOK_PATH", "/webhook/automation")


def log_event(event: str, **kwargs):
    payload = {"ts": datetime.now(timezone.utc).isoformat(), "event": event}
    if kwargs:
        for k, v in kwargs.items():
            try:
                json.dumps(v)
                payload[k] = v
            except Exception:
                payload[k] = str(v)
    logger.info(json.dumps(payload))


app = FastAPI(title="automation-api", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LinkedInGenIn(BaseModel):
    topic: str
    style: str
    word_limit: int

class LinkedInGenOut(BaseModel):
    request_id: str
    generated_at: str
    topic: str
    linkedin_post: str

class TwitterGenIn(BaseModel):
    topic: str
    count: int
    max_chars: int
    style: str

class TwitterGenOut(BaseModel):
    request_id: str
    generated_at: str
    topic: str
    tweets: List[str]
    count: int


@app.post("/ai/linkedin", response_model=LinkedInGenOut)
def ai_linkedin(payload: LinkedInGenIn, request: Request):
    req_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    log_event("ai_linkedin.start", req_id=req_id, client=str(request.client), body=payload.dict())
    linkedin_post = f"Demo LinkedIn post about {payload.topic} in {payload.style} style with limit {payload.word_limit}"
    out = {
        "request_id": req_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": payload.topic,
        "linkedin_post": linkedin_post,
    }
    dt_ms = int((time.perf_counter() - t0) * 1000)
    log_event("ai_linkedin.success", req_id=req_id, duration_ms=dt_ms, response_size=len(json.dumps(out)))
    return out

@app.post("/ai/twitter", response_model=TwitterGenOut)
def ai_twitter(payload: TwitterGenIn, request: Request):
    req_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    log_event("ai_twitter.start", req_id=req_id, client=str(request.client), body=payload.dict())
    tweets = []
    for i in range(payload.count):
        t = f"Demo tweet {i+1} about {payload.topic} ({payload.style})"
        if len(t) > payload.max_chars:
            t = t[: payload.max_chars]
        tweets.append(t)
    out = {
        "request_id": req_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": payload.topic,
        "tweets": tweets,
        "count": len(tweets),
    }
    dt_ms = int((time.perf_counter() - t0) * 1000)
    log_event("ai_twitter.success", req_id=req_id, duration_ms=dt_ms, tweets=len(tweets))
    return out


@app.get("/health")
async def health():
    log_event("health.check")
    return {"ok": True}

@app.post("/trigger")
async def trigger(payload: dict):
    t0 = time.perf_counter()
    req_id = str(uuid.uuid4())
    url = f"{N8N_BASE}{N8N_WEBHOOK_PATH}"
    log_event("trigger.start", req_id=req_id, url=url, payload=payload)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json=payload)
        dt_ms = int((time.perf_counter() - t0) * 1000)
        log_event("trigger.done", req_id=req_id, status=r.status_code, duration_ms=dt_ms, body_len=len(r.text))
        return {"status": r.status_code, "body": r.text}
    except Exception as e:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        log_event("trigger.error", req_id=req_id, duration_ms=dt_ms, error=str(e))
        return {"status": 500, "error": str(e)}

@app.post("/webhook/events")
async def webhook(payload: dict):
    t0 = time.perf_counter()
    req_id = str(uuid.uuid4())
    url = f"{N8N_BASE}{N8N_WEBHOOK_PATH}"
    log_event("webhook.start", req_id=req_id, url=url, payload=payload)
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(url, json=payload)
        dt_ms = int((time.perf_counter() - t0) * 1000)
        log_event("webhook.forwarded", req_id=req_id, duration_ms=dt_ms)
        return {"received": True}
    except Exception as e:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        log_event("webhook.error", req_id=req_id, duration_ms=dt_ms, error=str(e))
        return {"received": False, "error": str(e)}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())
    log_event("ws.accept", session_id=session_id)
    try:
        while True:
            data = await ws.receive_text()
            log_event("ws.recv", session_id=session_id, bytes=len(data.encode("utf-8")))
            try:
                async with httpx.AsyncClient(timeout=5) as c:
                    await c.post(f"{N8N_BASE}{N8N_WEBHOOK_PATH}", json={"ws": data})
                log_event("ws.forwarded", session_id=session_id)
            except Exception as e:
                log_event("ws.forward.error", session_id=session_id, error=str(e))
            await ws.send_text(data)
            log_event("ws.sent", session_id=session_id, echo_bytes=len(data.encode("utf-8")))
    except Exception as e:
        log_event("ws.closed", session_id=session_id, error=str(e))
        await ws.close()
