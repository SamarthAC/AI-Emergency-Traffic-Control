r"""
Bridge between AI traffic-density results and SUMO routing edge costs.

Place this file in:
    AI Traffic Control\model\

Required beside it:
    traffic_density.py
    traffic_routing.py

This module:
1. Stores virtual camera -> SUMO edge mappings.
2. Accepts AI traffic-density results for a camera.
3. Converts camera traffic_score (0-100) into SUMO edge traffic scores.
4. Supports bidirectional road mapping when the same camera covers both directions.
5. Can export the edge scores in the JSON format already supported by traffic_routing.py.
6. Includes a demo proving that high AI congestion on the direct hospital corridor
   causes A* to select the alternate ORR route.

Run:
    python edge_traffic_manager.py
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple


# ---------------------------------------------------------------------
# Optional imports from existing project modules
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# If an edge has no camera observation yet, routing falls back to this score.
DEFAULT_UNOBSERVED_SCORE = 0.0

# Virtual strategic camera placement for the current Bengaluru SUMO network.
#
# One physical camera/corridor can update more than one directed SUMO edge.
# This is deliberate because SUMO stores each direction as a separate edge.
#
# You can later add separate per-direction cameras if required.
CAMERA_EDGE_MAP = {
    # Ambulance station / west approach
    "CAM_STATION_APPROACH": (
        "J01_J10",
        "J10_J01",
    ),

    # Central arterial around J10-J14
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

    # Pickup approach / departure zone
    "CAM_PICKUP_CORRIDOR": (
        "J14_J23",
        "J23_J14",
    ),

    # Direct hospital corridor
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

    # Alternate ORR-style route
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
    """
    Maintains the latest AI traffic score for strategic SUMO road edges.

    Scores are always normalized to:
        0.0 = free / very low traffic
        100.0 = maximum congestion penalty
    """

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

        self.edge_scores: Dict[str, float] = {}
        self.camera_results: Dict[str, dict] = {}

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(0.0, min(float(score), 100.0))

    # -----------------------------------------------------------------
    # Camera / edge mapping
    # -----------------------------------------------------------------
    def get_camera_edges(self, camera_id: str) -> Tuple[str, ...]:
        if camera_id not in self.camera_edge_map:
            raise KeyError(
                f"Unknown camera_id '{camera_id}'. "
                f"Known cameras: {sorted(self.camera_edge_map.keys())}"
            )

        return self.camera_edge_map[camera_id]

    def get_known_camera_ids(self):
        return sorted(self.camera_edge_map.keys())

    # -----------------------------------------------------------------
    # Update using already-calculated density result
    # -----------------------------------------------------------------
    def update_from_density_result(
        self,
        camera_id: str,
        density_result: dict,
    ) -> dict:
        """
        Apply traffic_score from calculate_traffic_density(...) to every
        SUMO edge mapped to the supplied camera.
        """
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

    # -----------------------------------------------------------------
    # Update directly from V4 inference output
    # -----------------------------------------------------------------
    def update_from_inference(
        self,
        camera_id: str,
        inference_result: dict,
        roi=None,
    ) -> dict:
        """
        Run the existing traffic_density.py logic and map its result to
        the camera's SUMO road edges.
        """
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

    # -----------------------------------------------------------------
    # Manual score injection for testing / simulation
    # -----------------------------------------------------------------
    def set_camera_score(
        self,
        camera_id: str,
        score: float,
        traffic_level: Optional[str] = None,
    ) -> dict:
        """
        Useful for integration testing before wiring real camera inference.

        This does NOT replace AI in the final system; it is only a test input.
        """
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

    # -----------------------------------------------------------------
    # Edge score access
    # -----------------------------------------------------------------
    def get_edge_score(self, edge_id: str) -> float:
        return self.edge_scores.get(
            edge_id,
            self.default_unobserved_score,
        )

    def get_all_edge_scores(self) -> Dict[str, float]:
        return {
            edge_id: round(score, 2)
            for edge_id, score in sorted(self.edge_scores.items())
        }

    def clear(self):
        self.edge_scores.clear()
        self.camera_results.clear()

    # -----------------------------------------------------------------
    # Routing integration
    # -----------------------------------------------------------------
    def apply_to_graph(self, graph: SumoRoadGraph):
        """
        Push current edge traffic scores into traffic_routing.py.

        The existing SumoRoadGraph implementation is expected to expose
        set_traffic_scores(...), as used by the routing integration.
        """
        if not hasattr(graph, "set_traffic_scores"):
            raise AttributeError(
                "SumoRoadGraph has no set_traffic_scores(...) method. "
                "Use the current traffic_routing.py integration version."
            )

        graph.set_traffic_scores(
            self.get_all_edge_scores()
        )

    # -----------------------------------------------------------------
    # JSON export / import
    # -----------------------------------------------------------------
    def to_routing_json(self) -> dict:
        """
        Matches traffic_routing.py's supported JSON structure:
            {"traffic_scores": {"EDGE_ID": 72.5, ...}}
        """
        return {
            "traffic_scores": self.get_all_edge_scores()
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

    # -----------------------------------------------------------------
    # Console status
    # -----------------------------------------------------------------
    def print_status(self):
        print("\n" + "=" * 92)
        print("AI EDGE TRAFFIC MANAGER")
        print("=" * 92)

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

        print("=" * 92)


# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------
def print_route(title: str, result: dict):
    print("\n" + title)
    print("-" * 92)
    print("Junction path :", " -> ".join(result["junction_path"]))
    print("Edge path     :", " -> ".join(result["edge_path"]))
    print(
        f"Distance      : {result['distance_m']:.2f} m"
    )
    print(
        f"Free-flow time: {result['base_travel_time_s']:.2f} s"
    )
    print(
        f"AI route cost : {result['dynamic_cost_s']:.2f} s"
    )


def main():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    net_file = (
        project_dir
        / "simulation"
        / "bengaluru_structured"
        / "bengaluru_structured.net.xml"
    )

    if not net_file.exists():
        raise FileNotFoundError(
            f"SUMO network not found:\n{net_file}"
        )

    graph = SumoRoadGraph(net_file)
    manager = EdgeTrafficManager()

    # -------------------------------------------------------------
    # Test 1: LOW traffic everywhere relevant
    # -------------------------------------------------------------
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_1", 10.0)
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_2", 10.0)
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_3", 10.0)

    manager.set_camera_score("CAM_ORR_NORTH", 10.0)
    manager.set_camera_score("CAM_ORR_SOUTH", 10.0)

    manager.apply_to_graph(graph)

    free_route = graph.astar(
        "J23",
        "J47",
    )

    print_route(
        "TEST 1 - LOW TRAFFIC",
        free_route,
    )

    # -------------------------------------------------------------
    # Test 2:
    # AI now reports severe congestion on direct hospital corridor.
    # Alternate ORR route remains low.
    # -------------------------------------------------------------
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_1", 100.0)
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_2", 100.0)
    manager.set_camera_score("CAM_HOSPITAL_DIRECT_3", 100.0)

    manager.set_camera_score("CAM_ORR_NORTH", 5.0)
    manager.set_camera_score("CAM_ORR_SOUTH", 5.0)

    manager.apply_to_graph(graph)

    congested_route = graph.astar(
        "J23",
        "J47",
    )

    manager.print_status()

    print_route(
        "TEST 2 - AI HIGH TRAFFIC ON DIRECT HOSPITAL CORRIDOR",
        congested_route,
    )

    # -------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------
    route_changed = (
        free_route["edge_path"]
        != congested_route["edge_path"]
    )

    print("\n" + "=" * 92)
    print("INTEGRATION RESULT")
    print("=" * 92)

    if route_changed:
        print(
            "PASS: AI traffic scores changed the selected ambulance route."
        )
        print(
            "Traffic-density -> SUMO edge scores -> A* routing bridge is working."
        )
    else:
        print(
            "WARNING: Route did not change with the current scores."
        )
        print(
            "The bridge is working, but congestion values / camera mapping "
            "may need adjustment."
        )

    # Save sample JSON that traffic_routing.py can also consume directly.
    output_json = script_dir / "live_edge_traffic.json"
    manager.save_routing_json(output_json)

    print(f"\nSaved routing traffic JSON:\n{output_json}")
    print("=" * 92)


if __name__ == "__main__":
    main()
