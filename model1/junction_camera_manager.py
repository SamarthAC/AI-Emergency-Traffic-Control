from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class JunctionDetection:
    camera_id: str
    junction_id: str
    detected: bool
    confidence: float
    simulation_time: float
    metadata: dict[str, Any]


class JunctionCameraManager:
    """
    Stores ambulance-detection evidence produced by virtual junction cameras.

    Important:
    - This class does NOT fake CNN detections.
    - A real detector (or a test harness) must call report_detection(...).
    - Green Corridor can then call authorize_preemption(...) before changing a TLS.
    """

    def __init__(
        self,
        config_path: str | Path,
        publisher=None,
        detection_ttl_s: float = 8.0,
    ):
        self.config_path = Path(config_path)
        self.publisher = publisher
        self.detection_ttl_s = max(0.1, float(detection_ttl_s))

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Junction-camera config not found:\n{self.config_path}"
            )

        data = json.loads(self.config_path.read_text(encoding="utf-8"))

        self.policy = data.get("trigger_policy", {})
        self.minimum_confidence = float(
            self.policy.get("minimum_confidence", 0.70)
        )
        self.required_detection = bool(
            self.policy.get("required_detection", True)
        )
        self.require_traci_confirmation = bool(
            self.policy.get("traci_confirmation", True)
        )
        self.preempt_only_if_on_route = bool(
            self.policy.get("preempt_only_if_junction_on_active_route", True)
        )

        cameras = data.get("junction_cameras", [])
        if not isinstance(cameras, list) or not cameras:
            raise ValueError(
                "junction_camera_config.json contains no junction_cameras."
            )

        self.camera_by_id: dict[str, dict[str, Any]] = {}
        self.camera_by_junction: dict[str, dict[str, Any]] = {}

        for camera in cameras:
            camera_id = str(camera.get("camera_id", "")).strip()
            junction_id = str(camera.get("junction_id", "")).strip()

            if not camera_id or not junction_id:
                raise ValueError(
                    "Each junction camera requires camera_id and junction_id."
                )

            if camera_id in self.camera_by_id:
                raise ValueError(f"Duplicate camera_id: {camera_id}")

            if junction_id in self.camera_by_junction:
                raise ValueError(
                    f"More than one camera configured for junction {junction_id}. "
                    "This manager currently expects one logical camera per junction."
                )

            self.camera_by_id[camera_id] = camera
            self.camera_by_junction[junction_id] = camera

        self.latest_detection_by_junction: dict[str, JunctionDetection] = {}

    @property
    def camera_count(self) -> int:
        return len(self.camera_by_id)

    def has_camera(self, junction_id: str) -> bool:
        return junction_id in self.camera_by_junction

    def get_camera_for_junction(self, junction_id: str) -> dict[str, Any] | None:
        return self.camera_by_junction.get(junction_id)

    def report_detection(
        self,
        camera_id: str,
        detected: bool,
        confidence: float,
        simulation_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> JunctionDetection:
        """
        Register the latest CNN result for one junction camera.

        Example:
            manager.report_detection(
                camera_id="JCAM_J10",
                detected=True,
                confidence=0.91,
                simulation_time=123.0,
                metadata={"image": "frame_001.jpg"},
            )
        """
        if camera_id not in self.camera_by_id:
            raise KeyError(f"Unknown junction camera: {camera_id}")

        camera = self.camera_by_id[camera_id]
        junction_id = str(camera["junction_id"])

        result = JunctionDetection(
            camera_id=camera_id,
            junction_id=junction_id,
            detected=bool(detected),
            confidence=max(0.0, min(1.0, float(confidence))),
            simulation_time=float(simulation_time),
            metadata=dict(metadata or {}),
        )

        self.latest_detection_by_junction[junction_id] = result

        if self.publisher is not None:
            self.publisher.publish(
                "JUNCTION_CAMERA_DETECTION",
                {
                    "camera_id": camera_id,
                    "junction_id": junction_id,
                    "ambulance_detected": result.detected,
                    "confidence": round(result.confidence, 4),
                    "minimum_confidence": self.minimum_confidence,
                    "simulation_time": result.simulation_time,
                    "metadata": result.metadata,
                },
            )

        return result

    def get_latest_detection(
        self,
        junction_id: str,
    ) -> JunctionDetection | None:
        return self.latest_detection_by_junction.get(junction_id)

    def authorize_preemption(
        self,
        junction_id: str,
        simulation_time: float,
    ) -> tuple[bool, str, JunctionDetection | None]:
        """
        Decide whether camera evidence currently authorizes signal preemption.

        TraCI route/position confirmation remains the responsibility of the
        GreenCorridorController. This method evaluates only camera evidence.
        """
        camera = self.camera_by_junction.get(junction_id)
        if camera is None:
            return False, "NO_CAMERA_CONFIGURED", None

        if not self.required_detection:
            return True, "CAMERA_DETECTION_NOT_REQUIRED", None

        detection = self.latest_detection_by_junction.get(junction_id)
        if detection is None:
            return False, "NO_DETECTION_RECEIVED", None

        age = float(simulation_time) - detection.simulation_time
        if age < 0:
            age = 0.0

        if age > self.detection_ttl_s:
            return False, f"DETECTION_STALE_{age:.1f}s", detection

        if not detection.detected:
            return False, "AMBULANCE_NOT_DETECTED", detection

        if detection.confidence < self.minimum_confidence:
            return (
                False,
                f"CONFIDENCE_TOO_LOW_{detection.confidence:.2f}",
                detection,
            )

        return True, "CAMERA_CONFIRMED", detection

    def describe(self) -> None:
        print("\nJUNCTION CAMERA MANAGER")
        print("-" * 72)
        print(f"Configured cameras      : {self.camera_count}")
        print(f"Minimum confidence      : {self.minimum_confidence:.2f}")
        print(f"Detection TTL           : {self.detection_ttl_s:.1f} s")
        print(f"Detection required      : {self.required_detection}")
        print(f"TraCI confirmation      : {self.require_traci_confirmation}")
        print(f"Route confirmation      : {self.preempt_only_if_on_route}")
        print("-" * 72)

        for junction_id in sorted(self.camera_by_junction):
            camera = self.camera_by_junction[junction_id]
            print(f"{camera['camera_id']:14s} -> {junction_id}")
