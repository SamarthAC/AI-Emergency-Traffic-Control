from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HospitalCandidate:
    hospital_id: str
    name: str
    junction_id: str
    beds_available: int
    doctors_available: int
    emergency_enabled: bool = True


class HospitalSelector:
    def __init__(self, hospitals: list[HospitalCandidate]):
        self.hospitals = hospitals

    @classmethod
    def from_json(cls, json_path: str | Path) -> "HospitalSelector":
        raw = json.loads(Path(json_path).read_text(encoding="utf-8"))
        hospitals = [
            HospitalCandidate(
                hospital_id=item["hospital_id"],
                name=item["name"],
                junction_id=item["junction_id"],
                beds_available=int(item.get("beds_available", 0)),
                doctors_available=int(item.get("doctors_available", 0)),
                emergency_enabled=bool(item.get("emergency_enabled", True)),
            )
            for item in raw["hospitals"]
        ]
        return cls(hospitals)

    def evaluate(self, graph, pickup_junction: str) -> list[dict[str, Any]]:
        results = []

        for hospital in self.hospitals:
            reasons = []

            if not hospital.emergency_enabled:
                reasons.append("Emergency service unavailable")
            if hospital.beds_available <= 0:
                reasons.append("No beds available")
            if hospital.doctors_available <= 0:
                reasons.append("No doctor available")

            eligible = not reasons
            route = None

            if eligible:
                route = graph.astar(pickup_junction, hospital.junction_id)
                if not route:
                    eligible = False
                    reasons.append("No reachable route")

            results.append({
                "hospital_id": hospital.hospital_id,
                "name": hospital.name,
                "junction_id": hospital.junction_id,
                "beds_available": hospital.beds_available,
                "doctors_available": hospital.doctors_available,
                "emergency_enabled": hospital.emergency_enabled,
                "eligible": eligible,
                "reasons": reasons,
                "route": route,
                "dynamic_cost_s": float(route["dynamic_cost_s"]) if route else None,
                "distance_m": float(route["distance_m"]) if route else None,
            })

        return results

    def select(self, graph, pickup_junction: str) -> dict[str, Any]:
        candidates = self.evaluate(graph, pickup_junction)
        eligible = [c for c in candidates if c["eligible"]]

        if not eligible:
            raise RuntimeError("No eligible hospital is currently available.")

        selected = min(
            eligible,
            key=lambda c: (
                c["dynamic_cost_s"],
                -c["beds_available"],
                -c["doctors_available"],
            ),
        )

        return {
            "selected_hospital": selected,
            "candidates": candidates,
            "selection_reason": (
                f"{selected['name']} selected because it is medically eligible "
                f"and has the lowest traffic-aware route cost "
                f"({selected['dynamic_cost_s']:.2f} s) among eligible hospitals."
            ),
        }
