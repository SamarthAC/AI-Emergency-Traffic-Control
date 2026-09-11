from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from event_bus import ConnectionManager, event_bus
from schemas import WSMessage
from state_store import DashboardStateStore


app = FastAPI(
    title="AI Smart Ambulance Backend",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
state_store = DashboardStateStore()


@app.get("/")
async def root():
    return {
        "project": "AI Smart Ambulance",
        "backend": "FastAPI",
        "status": "running",
        "websocket": "/ws",
        "event_ingest": "/events",
        "state": "/api/state",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "connected_clients": manager.connection_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/state")
async def get_state():
    return state_store.snapshot()


@app.get("/api/ambulance")
async def get_ambulance():
    return state_store.ambulance


@app.get("/api/route")
async def get_route():
    return state_store.route


@app.get("/api/traffic")
async def get_traffic():
    return state_store.traffic


@app.get("/api/signals")
async def get_signals():
    return state_store.signals


@app.get("/api/logs")
async def get_logs():
    return state_store.logs


@app.post("/api/reset")
async def reset_state():
    state_store.reset()
    return {"reset": True}


@app.post("/events")
async def ingest_event(message: WSMessage):
    payload = message.model_dump()

    # Update REST-readable dashboard state immediately.
    state_store.apply(payload)

    # Then broadcast the exact same event to WebSocket clients.
    await event_bus.put(payload)

    return {
        "accepted": True,
        "type": message.type,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # A newly connected dashboard immediately receives the current state,
    # so it does not need to wait for the next simulation event.
    await manager.send_personal(
        websocket,
        {
            "type": "STATE_SNAPSHOT",
            "data": state_store.snapshot(),
        },
    )

    await manager.send_personal(
        websocket,
        WSMessage(
            type="LOG",
            data={
                "level": "INFO",
                "message": "Dashboard connected to AI ambulance backend.",
            },
        ).model_dump(),
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_worker():
    while True:
        message = await event_bus.get()
        await manager.broadcast(message)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_worker())
