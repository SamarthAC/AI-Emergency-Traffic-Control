from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class DashboardStateStore:
    """
    Latest-state store for the Smart Ambulance dashboard.

    ai_emergency_demo.py / SUMO remains the source of truth.
    This store keeps the latest state for REST clients and for
    dashboards that connect after the simulation has already started.
    """

    MAX_LOGS = 200

    def __init__(self):
        self.reset()

    def reset(self):
        self.ambulance: dict[str, Any] = {}
        self.route: dict[str, Any] = {}

        # New dashboard state
        self.hospital: dict[str, Any] = {}
        self.corridor: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}

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

        # -------------------------------------------------------------
        # Ambulance
        # -------------------------------------------------------------
        if event_type == "AMBULANCE_STATUS":
            self.ambulance.update(data)

            # Keep route lifecycle metadata synchronized with the
            # authoritative ambulance status.
            if "pickup_reached" in data:
                self.route["pickup_reached"] = bool(data["pickup_reached"])

                if data["pickup_reached"]:
                    self.route["route_stage"] = "POST_PICKUP"

            status = str(data.get("status", "")).upper()

            if status == "ARRIVED":
                self.route["pickup_reached"] = True
                self.route["route_stage"] = "ARRIVED"

        # -------------------------------------------------------------
        # AI route / reroutes
        # -------------------------------------------------------------
        elif event_type == "AI_ROUTE":
            self.route = data

        # -------------------------------------------------------------
        # Selected hospital
        # -------------------------------------------------------------
        elif event_type == "HOSPITAL_SELECTION":
            self.hospital = data

        # -------------------------------------------------------------
        # Traffic CNN results
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # Traffic signals
        # -------------------------------------------------------------
        elif event_type == "SIGNAL_UPDATE":
            junction_id = data.get("junction_id")

            if junction_id:
                self.signals[str(junction_id)] = data

        # -------------------------------------------------------------
        # Green Corridor
        # -------------------------------------------------------------
        elif event_type == "GREEN_CORRIDOR_STATUS":
            self.corridor.update(data)

        # -------------------------------------------------------------
        # Junction-camera ambulance detection
        # -------------------------------------------------------------
        elif event_type == "JUNCTION_CAMERA_DETECTION":
            junction_id = data.get("junction_id")
            camera_id = data.get("camera_id")

            if junction_id:
                self.junction_cameras[str(junction_id)] = data
            elif camera_id:
                self.junction_cameras[str(camera_id)] = data

        # -------------------------------------------------------------
        # Vehicle positions
        # -------------------------------------------------------------
        elif event_type == "VEHICLE_UPDATE":
            vehicle_id = data.get("vehicle_id")

            if vehicle_id:
                self.vehicles[str(vehicle_id)] = data

            # Keep ambulance state continuously updated.
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

        # -------------------------------------------------------------
        # Final emergency response metrics
        # -------------------------------------------------------------
        elif event_type == "EMERGENCY_METRICS":
            self.metrics = data

        # -------------------------------------------------------------
        # Logs
        # -------------------------------------------------------------
        elif event_type == "LOG":
            self.logs.append(data)
            self.logs = self.logs[-self.MAX_LOGS:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "ambulance": deepcopy(self.ambulance),
            "route": deepcopy(self.route),
            "hospital": deepcopy(self.hospital),
            "traffic": deepcopy(self.traffic),
            "signals": deepcopy(self.signals),
            "corridor": deepcopy(self.corridor),
            "junction_cameras": deepcopy(self.junction_cameras),
            "vehicles": deepcopy(self.vehicles),
            "metrics": deepcopy(self.metrics),
            "logs": deepcopy(self.logs),
            "meta": {
                "last_event_type": self.last_event_type,
                "updated_at": self.updated_at,
            },
        }