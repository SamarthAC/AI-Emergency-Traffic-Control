r"""
Bridge between AI traffic-density results and SUMO routing edge costs.

Important behavior:
- Observed camera roads use the latest AI traffic score.
- Unobserved SUMO roads receive a conservative LOW-traffic baseline instead
  of being treated as perfectly free roads.
- This prevents A* from preferring an unmonitored road simply because its
  traffic score was never measured.

Place in:
    AI Traffic Control\model\edge_traffic_manager.py
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

try:
    from traffic_density import calculate_traffic_density
except ImportError as exc:
    raise RuntimeError(
        "Could not import traffic_density.py. Keep this file inside the model folder."
    ) from exc

try:
    from traffic_routing import SumoRoadGraph
except ImportError as exc:
    raise RuntimeError(
        "Could not import traffic_routing.py. Keep this file inside the model folder."
    ) from exc


# A low but non-zero prior for roads without a camera observation.
# Unknown road != empty road.
DEFAULT_UNOBSERVED_SCORE = 25.0


CAMERA_EDGE_MAP = {
    "CAM_STATION_APPROACH": (
        "J01_J10",
        "J10_J01",
    ),

    "CAM_CBD_WEST": (
        "J10_J11",
        "J11_J10",
        "J11_J12",
        "J12_J11",
    ),

    "CAM_CBD_EAST": (
        "J12_J13",
        "J13_J12",
        "J13_J14",
        "J14_J13",
    ),

    "CAM_PICKUP_CORRIDOR": (
        "J14_J23",
        "J23_J14",
    ),

    "CAM_HOSPITAL_DIRECT_1": (
        "J23_J31",
        "J31_J23",
    ),

    "CAM_HOSPITAL_DIRECT_2": (
        "J31_J39",
        "J39_J31",
    ),

    "CAM_HOSPITAL_DIRECT_3": (
        "J39_J47",
        "J47_J39",
    ),

    "CAM_ORR_NORTH": (
        "J23_J24",
        "J24_J23",
        "J24_J32",
        "J32_J24",
    ),

    "CAM_ORR_SOUTH": (
        "J32_J40",
        "J40_J32",
        "J40_J48",
        "J48_J40",
        "J48_J47",
        "J47_J48",
    ),
}


class EdgeTrafficManager:
    def __init__(
        self,
        camera_edge_map: Optional[Dict[str, Iterable[str]]] = None,
        default_unobserved_score: float = DEFAULT_UNOBSERVED_SCORE,
    ):
        self.camera_edge_map = {
            camera_id: tuple(edges)
            for camera_id, edges in (
                camera_edge_map or CAMERA_EDGE_MAP
            ).items()
        }

        self.default_unobserved_score = self._clamp_score(
            default_unobserved_score
        )

        # Explicit AI-observed scores only.
        self.edge_scores: Dict[str, float] = {}

        # Latest per-camera density results.
        self.camera_results: Dict[str, dict] = {}

        # Full resolved road state after apply_to_graph():
        # every SUMO edge gets either an AI score or baseline score.
        self.resolved_edge_scores: Dict[str, float] = {}

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(0.0, min(float(score), 100.0))

    def get_camera_edges(self, camera_id: str) -> Tuple[str, ...]:
        if camera_id not in self.camera_edge_map:
            raise KeyError(
                f"Unknown camera_id '{camera_id}'. "
                f"Known cameras: {sorted(self.camera_edge_map.keys())}"
            )

        return self.camera_edge_map[camera_id]

    def get_known_camera_ids(self):
        return sorted(self.camera_edge_map.keys())

    def update_from_density_result(
        self,
        camera_id: str,
        density_result: dict,
    ) -> dict:
        edges = self.get_camera_edges(camera_id)

        if "traffic_score" not in density_result:
            raise KeyError(
                "density_result does not contain 'traffic_score'."
            )

        traffic_score = self._clamp_score(
            density_result["traffic_score"]
        )

        normalized_result = deepcopy(density_result)
        normalized_result["traffic_score"] = round(traffic_score, 2)
        normalized_result["camera_id"] = camera_id
        normalized_result["mapped_edges"] = list(edges)

        self.camera_results[camera_id] = normalized_result

        for edge_id in edges:
            self.edge_scores[edge_id] = traffic_score

        return normalized_result

    def update_from_inference(
        self,
        camera_id: str,
        inference_result: dict,
        roi=None,
    ) -> dict:
        if roi is None:
            density_result = calculate_traffic_density(inference_result)
        else:
            density_result = calculate_traffic_density(
                inference_result,
                roi=roi,
            )

        return self.update_from_density_result(
            camera_id,
            density_result,
        )

    def set_camera_score(
        self,
        camera_id: str,
        score: float,
        traffic_level: Optional[str] = None,
    ) -> dict:
        score = self._clamp_score(score)

        if traffic_level is None:
            if score < 48.0:
                traffic_level = "LOW"
            elif score < 90.0:
                traffic_level = "MEDIUM"
            else:
                traffic_level = "HIGH"

        density_result = {
            "traffic_score": round(score, 2),
            "traffic_level": traffic_level,
            "source": "manual_test",
        }

        return self.update_from_density_result(
            camera_id,
            density_result,
        )

    def get_edge_score(self, edge_id: str) -> float:
        return self.edge_scores.get(
            edge_id,
            self.default_unobserved_score,
        )

    def get_observed_edge_scores(self) -> Dict[str, float]:
        return {
            edge_id: round(score, 2)
            for edge_id, score in sorted(self.edge_scores.items())
        }

    def get_all_edge_scores(self) -> Dict[str, float]:
        """
        Return the latest full resolved graph state if apply_to_graph()
        has already been called. Otherwise return only observed edge scores.
        """
        source = (
            self.resolved_edge_scores
            if self.resolved_edge_scores
            else self.edge_scores
        )

        return {
            edge_id: round(score, 2)
            for edge_id, score in sorted(source.items())
        }

    def clear(self):
        self.edge_scores.clear()
        self.camera_results.clear()
        self.resolved_edge_scores.clear()

    def build_resolved_scores(
        self,
        graph: SumoRoadGraph,
    ) -> Dict[str, float]:
        """
        Give every road in the SUMO graph a score.

        Observed road:
            actual AI score

        Unobserved road:
            DEFAULT_UNOBSERVED_SCORE baseline
        """
        scores = {
            edge_id: self.default_unobserved_score
            for edge_id in graph.edges.keys()
        }

        for edge_id, score in self.edge_scores.items():
            if edge_id in graph.edges:
                scores[edge_id] = self._clamp_score(score)

        return scores

    def apply_to_graph(self, graph: SumoRoadGraph):
        if not hasattr(graph, "set_traffic_scores"):
            raise AttributeError(
                "SumoRoadGraph has no set_traffic_scores(...) method."
            )

        # Critical: first resolve EVERY edge, not only camera-observed edges.
        self.resolved_edge_scores = self.build_resolved_scores(graph)

        unknown = graph.set_traffic_scores(
            self.resolved_edge_scores
        )

        if unknown:
            print(
                "Warning: traffic scores referenced unknown SUMO edges:",
                ", ".join(unknown),
            )

    def to_routing_json(self) -> dict:
        return {
            "traffic_scores": self.get_all_edge_scores(),
            "metadata": {
                "default_unobserved_score": self.default_unobserved_score,
                "observed_edge_count": len(self.edge_scores),
                "resolved_edge_count": len(self.resolved_edge_scores),
            },
        }

    def save_routing_json(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                self.to_routing_json(),
                file,
                indent=4,
            )

        return path

    def print_status(self):
        print("\n" + "=" * 92)
        print("AI EDGE TRAFFIC MANAGER")
        print("=" * 92)
        print(
            f"Unobserved-road baseline: "
            f"{self.default_unobserved_score:.2f}"
        )

        if not self.camera_results:
            print("No camera traffic results available yet.")
            print("=" * 92)
            return

        for camera_id in self.get_known_camera_ids():
            result = self.camera_results.get(camera_id)
            if not result:
                continue

            score = result.get("traffic_score", 0.0)
            level = result.get("traffic_level", "UNKNOWN")
            edges = result.get("mapped_edges", [])

            print(
                f"{camera_id:24s} "
                f"score={score:6.2f} "
                f"level={level:6s} "
                f"edges={', '.join(edges)}"
            )

        print(
            f"Observed edges: {len(self.edge_scores)} | "
            f"Resolved SUMO edges: {len(self.resolved_edge_scores)}"
        )
        print("=" * 92)


if __name__ == "__main__":
    print(
        "edge_traffic_manager.py is an integration module.\n"
        "Run edge_traffic_manager.py's earlier test script or "
        "ai_dynamic_routing_demo.py for a full routing test."
    )
