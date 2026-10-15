from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from event_bus import ConnectionManager, event_bus
from schemas import WSMessage
from state_store import DashboardStateStore


app = FastAPI(
    title="AI Smart Ambulance Backend",
    version="1.3.0",
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

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
MODEL_DIR = PROJECT_DIR / "model"
LIVE_TRAFFIC_IMAGE_DIR = MODEL_DIR / "live_inputs"
JUNCTION_CAMERA_IMAGE_DIR = MODEL_DIR / "ambulance demo images"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
LIVE_TRAFFIC_CAMERA_IDS = {
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
}


def _image_response(path: Path) -> FileResponse:
    """Return an image without browser caching stale overwritten camera frames."""
    return FileResponse(
        path,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def _resolve_live_traffic_frame(camera_id: str) -> Path:
    if camera_id not in LIVE_TRAFFIC_CAMERA_IDS:
        raise HTTPException(status_code=404, detail="Unknown traffic camera")

    matches = [
        LIVE_TRAFFIC_IMAGE_DIR / f"{camera_id}{suffix}"
        for suffix in IMAGE_SUFFIXES
        if (LIVE_TRAFFIC_IMAGE_DIR / f"{camera_id}{suffix}").exists()
    ]

    if not matches:
        raise HTTPException(status_code=404, detail="Traffic camera image unavailable")

    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail="Multiple image files exist for this traffic camera",
        )

    return matches[0]


def _resolve_junction_frame(image_name: str) -> Path:
    # Prevent path traversal; junction events contain a simple validated basename.
    safe_name = Path(image_name).name
    if safe_name != image_name:
        raise HTTPException(status_code=400, detail="Invalid image name")

    path = JUNCTION_CAMERA_IMAGE_DIR / safe_name
    if not path.exists() or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise HTTPException(status_code=404, detail="Junction camera image unavailable")

    return path


@app.get("/")
async def root():
    return {
        "project": "AI Smart Ambulance",
        "backend": "FastAPI",
        "status": "running",
        "websocket": "/ws",
        "event_ingest": "/events",
        "state": "/api/state",
        "image_manifest": "/api/images/manifest",
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


@app.get("/api/junction-cameras")
async def get_junction_cameras():
    return state_store.junction_cameras


@app.get("/api/hospital")
async def get_hospital():
    return state_store.hospital


@app.get("/api/corridor")
async def get_corridor():
    return state_store.corridor


@app.get("/api/metrics")
async def get_metrics():
    return state_store.metrics


@app.get("/api/images/traffic/{camera_id}")
async def get_live_traffic_image(camera_id: str):
    """
    Serve the current watched frame for one logical traffic camera.

    The filename remains stable while its bytes are overwritten during a live
    demo, so responses explicitly disable caching. The dashboard should still
    append ?v=<image_version> from TRAFFIC_OVERVIEW for an unambiguous refresh.
    """
    return _image_response(_resolve_live_traffic_frame(camera_id))


@app.get("/api/images/junction/{image_name}")
async def get_junction_camera_image(image_name: str):
    """Serve a validated prerecorded ambulance-detection frame by basename."""
    return _image_response(_resolve_junction_frame(image_name))


@app.get("/api/images/manifest")
async def get_image_manifest():
    traffic = {}
    for camera_id in sorted(LIVE_TRAFFIC_CAMERA_IDS):
        try:
            path = _resolve_live_traffic_frame(camera_id)
            traffic[camera_id] = {
                "available": True,
                "filename": path.name,
                "url": f"/api/images/traffic/{camera_id}",
                "modified_ns": path.stat().st_mtime_ns,
            }
        except HTTPException:
            traffic[camera_id] = {
                "available": False,
                "filename": None,
                "url": f"/api/images/traffic/{camera_id}",
                "modified_ns": None,
            }

    junction_images = []
    if JUNCTION_CAMERA_IMAGE_DIR.exists():
        for path in sorted(JUNCTION_CAMERA_IMAGE_DIR.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                junction_images.append(
                    {
                        "filename": path.name,
                        "url": f"/api/images/junction/{path.name}",
                    }
                )

    return {
        "traffic": traffic,
        "junction": junction_images,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
