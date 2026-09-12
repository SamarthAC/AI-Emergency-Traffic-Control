from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class DashboardStateStore:
    """
    In-memory latest-state store for the prototype dashboard.

    The AI/SUMO process remains the source of truth. This class only keeps
    the most recent values so REST clients and newly connected WebSocket
    clients can immediately reconstruct the dashboard.
    """

    MAX_LOGS = 200

    def __init__(self):
        self.reset()

    def reset(self):
        self.ambulance: dict[str, Any] = {}
        self.route: dict[str, Any] = {}
        self.traffic: dict[str, dict[str, Any]] = {}
        self.signals: dict[str, dict[str, Any]] = {}
        self.junction_cameras: dict[str, dict[str, Any]] = {}
        self.vehicles: dict[str, dict[str, Any]] = {}
        self.logs: list[dict[str, Any]] = []
        self.last_event_type: str | None = None
        self.updated_at: str | None = None

    def apply(self, message: dict[str, Any]):
        event_type = message.get("type")
        data = deepcopy(message.get("data") or {})

        self.last_event_type = event_type
        self.updated_at = datetime.now(timezone.utc).isoformat()

        if event_type == "AMBULANCE_STATUS":
            self.ambulance.update(data)

        elif event_type == "AI_ROUTE":
            self.route = data

        elif event_type == "TRAFFIC_OVERVIEW":
            camera_id = data.get("camera_id")
            edge_ids = data.get("edge_ids") or []

            if camera_id:
                key = str(camera_id)
            elif edge_ids:
                key = ",".join(map(str, edge_ids))
            else:
                key = f"traffic_{len(self.traffic) + 1}"

            self.traffic[key] = data

        elif event_type == "SIGNAL_UPDATE":
            junction_id = data.get("junction_id")
            if junction_id:
                self.signals[str(junction_id)] = data

        elif event_type == "JUNCTION_CAMERA_DETECTION":
            junction_id = data.get("junction_id")
            camera_id = data.get("camera_id")

            if junction_id:
                self.junction_cameras[str(junction_id)] = data
            elif camera_id:
                self.junction_cameras[str(camera_id)] = data

        elif event_type == "VEHICLE_UPDATE":
            vehicle_id = data.get("vehicle_id")
            if vehicle_id:
                self.vehicles[str(vehicle_id)] = data

            # Keep the ambulance state useful even between explicit
            # AMBULANCE_STATUS events.
            if vehicle_id == "AI_AMB_001":
                self.ambulance.update(
                    {
                        "id": vehicle_id,
                        "edge_id": data.get("edge_id"),
                        "lane_id": data.get("lane_id"),
                        "route_index": data.get("route_index"),
                        "route_length": data.get("route_length"),
                        "speed_kmh": data.get("speed_kmh"),
                        "x": data.get("x"),
                        "y": data.get("y"),
                        "simulation_time": data.get("simulation_time"),
                    }
                )

        elif event_type == "LOG":
            self.logs.append(data)
            self.logs = self.logs[-self.MAX_LOGS:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "ambulance": deepcopy(self.ambulance),
            "route": deepcopy(self.route),
            "traffic": deepcopy(self.traffic),
            "signals": deepcopy(self.signals),
            "junction_cameras": deepcopy(self.junction_cameras),
            "vehicles": deepcopy(self.vehicles),
            "logs": deepcopy(self.logs),
            "meta": {
                "last_event_type": self.last_event_type,
                "updated_at": self.updated_at,
            },
        }
