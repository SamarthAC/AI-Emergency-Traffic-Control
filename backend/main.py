from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from event_bus import ConnectionManager, event_bus
from schemas import WSMessage


app = FastAPI(
    title="AI Smart Ambulance Backend",
    version="1.1.0",
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


@app.get("/")
async def root():
    return {
        "project": "AI Smart Ambulance",
        "backend": "FastAPI",
        "status": "running",
        "websocket": "/ws",
        "event_ingest": "/events",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "connected_clients": manager.connection_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/events")
async def ingest_event(message: WSMessage):
    """
    Receives events from the Python AI/SUMO process and places them onto
    the backend event bus. Connected React dashboards receive the same
    event through /ws.
    """
    payload = message.model_dump()
    await event_bus.put(payload)

    return {
        "accepted": True,
        "type": message.type,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

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
