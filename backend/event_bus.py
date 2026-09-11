from __future__ import annotations
import asyncio
from typing import Any
from fastapi import WebSocket

event_bus: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    @property
    def connection_count(self):
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        dead = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)

async def publish(message_type: str, data: dict[str, Any]):
    await event_bus.put({"type": message_type, "data": data})
