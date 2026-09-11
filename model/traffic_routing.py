"""
traffic_routing.py
Congestion-aware Dijkstra + A* router for bengaluru_structured.net.xml.

Run from:
    AI Traffic Control\model> python traffic_routing.py

Optional:
    python traffic_routing.py --start J01 --pickup J23 --hospital J47
    python traffic_routing.py --network "path\to\bengaluru_structured.net.xml"
"""

from __future__ import annotations
import argparse
import heapq
import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CONGESTION_FACTOR = 2.0


@dataclass
class RoadEdge:
    edge_id: str
    from_node: str
    to_node: str
    length_m: float
    speed_mps: float
    lanes: int
    traffic_score: float = 0.0

    @property
    def base_time_s(self) -> float:
        return self.length_m / self.speed_mps

    @property
    def dynamic_time_s(self) -> float:
        score = max(0.0, min(100.0, self.traffic_score))
        return self.base_time_s * (1.0 + CONGESTION_FACTOR * score / 100.0)


class SumoRoadGraph:
    def __init__(self, net_file: Path):
        self.net_file = Path(net_file)
        self.edges: Dict[str, RoadEdge] = {}
        self.adj: Dict[str, List[RoadEdge]] = {}
        self.coords: Dict[str, Tuple[float, float]] = {}
        self.max_speed_mps = 1.0
        self._load()

    def _load(self) -> None:
        root = ET.parse(self.net_file).getroot()

        for j in root.findall("junction"):
            jid = j.get("id", "")
            if jid.startswith(":"):
                continue
            x, y = j.get("x"), j.get("y")
            if x is not None and y is not None:
                self.coords[jid] = (float(x), float(y))

        for e in root.findall("edge"):
            eid = e.get("id", "")
            if (
                eid.startswith(":")
                or e.get("function") == "internal"
                or e.get("from") is None
                or e.get("to") is None
            ):
                continue

            lanes = e.findall("lane")
            if not lanes:
                continue

            # For this network all lanes of a road share road length/speed.
            lane0 = lanes[0]
            edge = RoadEdge(
                edge_id=eid,
                from_node=e.get("from"),
                to_node=e.get("to"),
                length_m=float(lane0.get("length")),
                speed_mps=float(lane0.get("speed")),
                lanes=len(lanes),
            )
            self.edges[eid] = edge
            self.adj.setdefault(edge.from_node, []).append(edge)
            self.max_speed_mps = max(self.max_speed_mps, edge.speed_mps)

    def reset_traffic(self) -> None:
        for edge in self.edges.values():
            edge.traffic_score = 0.0

    def set_traffic_scores(self, scores: Dict[str, float]) -> List[str]:
        unknown = []
        for eid, score in scores.items():
            if eid not in self.edges:
                unknown.append(eid)
                continue
            self.edges[eid].traffic_score = max(0.0, min(100.0, float(score)))
        return unknown

    def heuristic_seconds(self, node: str, goal: str) -> float:
        """Admissible free-flow lower bound for A*."""
        if node not in self.coords or goal not in self.coords:
            return 0.0
        x1, y1 = self.coords[node]
        x2, y2 = self.coords[goal]
        return math.hypot(x2 - x1, y2 - y1) / self.max_speed_mps

    def _reconstruct(
        self, prev: Dict[str, Tuple[str, str]], start: str, goal: str
    ) -> Tuple[List[str], List[str]]:
        if start == goal:
            return [start], []
        if goal not in prev:
            raise ValueError(f"No route found from {start} to {goal}")

        nodes = [goal]
        edge_ids = []
        cur = goal
        while cur != start:
            pnode, eid = prev[cur]
            edge_ids.append(eid)
            nodes.append(pnode)
            cur = pnode
        nodes.reverse()
        edge_ids.reverse()
        return nodes, edge_ids

    def dijkstra(self, start: str, goal: str):
        pq = [(0.0, start)]
        dist = {start: 0.0}
        prev: Dict[str, Tuple[str, str]] = {}

        while pq:
            g, node = heapq.heappop(pq)
            if g > dist.get(node, float("inf")):
                continue
            if node == goal:
                break

            for edge in self.adj.get(node, []):
                ng = g + edge.dynamic_time_s
                if ng < dist.get(edge.to_node, float("inf")):
                    dist[edge.to_node] = ng
                    prev[edge.to_node] = (node, edge.edge_id)
                    heapq.heappush(pq, (ng, edge.to_node))

        nodes, edge_ids = self._reconstruct(prev, start, goal)
        return self.route_result("Dijkstra", nodes, edge_ids)

    def astar(self, start: str, goal: str):
        pq = [(self.heuristic_seconds(start, goal), 0.0, start)]
        gscore = {start: 0.0}
        prev: Dict[str, Tuple[str, str]] = {}

        while pq:
            _, g, node = heapq.heappop(pq)
            if g > gscore.get(node, float("inf")):
                continue
            if node == goal:
                break

            for edge in self.adj.get(node, []):
                ng = g + edge.dynamic_time_s
                if ng < gscore.get(edge.to_node, float("inf")):
                    gscore[edge.to_node] = ng
                    prev[edge.to_node] = (node, edge.edge_id)
                    f = ng + self.heuristic_seconds(edge.to_node, goal)
                    heapq.heappush(pq, (f, ng, edge.to_node))

        nodes, edge_ids = self._reconstruct(prev, start, goal)
        return self.route_result("A*", nodes, edge_ids)

    def route_result(self, algorithm: str, nodes: List[str], edge_ids: List[str]):
        details = []
        base = dynamic = distance = 0.0

        for eid in edge_ids:
            e = self.edges[eid]
            base += e.base_time_s
            dynamic += e.dynamic_time_s
            distance += e.length_m
            details.append({
                "edge_id": eid,
                "from": e.from_node,
                "to": e.to_node,
                "length_m": round(e.length_m, 2),
                "lanes": e.lanes,
                "speed_kmh": round(e.speed_mps * 3.6, 1),
                "traffic_score": round(e.traffic_score, 1),
                "base_time_s": round(e.base_time_s, 2),
                "dynamic_time_s": round(e.dynamic_time_s, 2),
            })

        return {
            "algorithm": algorithm,
            "junction_path": nodes,
            "edge_path": edge_ids,
            "distance_m": round(distance, 2),
            "base_travel_time_s": round(base, 2),
            "dynamic_cost_s": round(dynamic, 2),
            "details": details,
        }


def print_route(title: str, result: dict) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    print("Algorithm :", result["algorithm"])
    print("Junctions :", " -> ".join(result["junction_path"]))
    print("SUMO edges:", " -> ".join(result["edge_path"]))
    print(f"Distance  : {result['distance_m']:.2f} m")
    print(f"Free-flow : {result['base_travel_time_s']:.2f} s")
    print(f"AI cost   : {result['dynamic_cost_s']:.2f} s")

    print("\nEDGE DETAILS")
    for d in result["details"]:
        print(
            f"{d['edge_id']:12s} "
            f"{d['from']}->{d['to']}  "
            f"{d['length_m']:7.1f}m  "
            f"{d['speed_kmh']:5.1f}km/h  "
            f"lanes={d['lanes']}  "
            f"traffic={d['traffic_score']:5.1f}  "
            f"cost={d['dynamic_time_s']:6.2f}s"
        )


def load_scores(path: Optional[str]) -> Dict[str, float]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Supports either {"edge": score} or {"traffic_scores": {...}}
    if "traffic_scores" in data:
        data = data["traffic_scores"]
    return {str(k): float(v) for k, v in data.items()}


def demo_congestion(graph: SumoRoadGraph, freeflow_route: dict) -> Dict[str, float]:
    """
    Simulates a traffic incident by making the free-flow corridor congested.
    Later this dictionary will be replaced by traffic_density.py / TraCI data.
    """
    scores = {}
    for i, eid in enumerate(freeflow_route["edge_path"]):
        # Keep first/last approach moderate; congest the middle corridor strongly.
        if i == 0 or i == len(freeflow_route["edge_path"]) - 1:
            scores[eid] = 45.0
        else:
            scores[eid] = 92.0
    return scores


def main():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    default_net = (
        project_dir
        / "simulation"
        / "bengaluru_structured"
        / "bengaluru_structured.net.xml"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default=str(default_net))
    parser.add_argument("--start", default="J01")
    parser.add_argument("--pickup", default="J23")
    parser.add_argument("--hospital", default="J47")
    parser.add_argument("--traffic-json", default=None)
    args = parser.parse_args()

    graph = SumoRoadGraph(Path(args.network))

    print("\nBENGALURU AI AMBULANCE ROUTING")
    print("=" * 90)
    print("Network :", graph.net_file)
    print("Junctions:", len(graph.coords))
    print("Road edges:", len(graph.edges))
    print(f"Maximum road speed: {graph.max_speed_mps * 3.6:.1f} km/h")

    # LEG 1: ambulance station -> emergency pickup
    graph.reset_traffic()
    leg1_d = graph.dijkstra(args.start, args.pickup)
    leg1_a = graph.astar(args.start, args.pickup)
    print_route("LEG 1 FREE-FLOW: AMBULANCE STATION -> EMERGENCY PICKUP", leg1_a)

    if leg1_d["edge_path"] != leg1_a["edge_path"]:
        print("\nNOTE: Dijkstra and A* found equal/alternative optimal paths.")
    else:
        print("\nPASS: Dijkstra and A* agree on Leg 1.")

    # LEG 2 baseline: pickup -> hospital
    graph.reset_traffic()
    leg2_free_d = graph.dijkstra(args.pickup, args.hospital)
    leg2_free_a = graph.astar(args.pickup, args.hospital)
    print_route("LEG 2 FREE-FLOW: PICKUP -> MAIN HOSPITAL", leg2_free_a)

    # LEG 2 congested: external scores if supplied, otherwise demo incident
    graph.reset_traffic()
    external_scores = load_scores(args.traffic_json)
    if external_scores:
        scores = external_scores
        scenario_name = "LIVE/JSON CONGESTION"
    else:
        scores = demo_congestion(graph, leg2_free_a)
        scenario_name = "DEMO CONGESTION"

    unknown = graph.set_traffic_scores(scores)
    if unknown:
        print("\nWarning: unknown traffic edge IDs:", ", ".join(unknown))

    leg2_cong_d = graph.dijkstra(args.pickup, args.hospital)
    leg2_cong_a = graph.astar(args.pickup, args.hospital)
    print_route(f"LEG 2 {scenario_name}: PICKUP -> MAIN HOSPITAL", leg2_cong_a)

    if leg2_cong_d["edge_path"] == leg2_cong_a["edge_path"]:
        print("\nPASS: Dijkstra and A* agree on the congestion-aware route.")
    else:
        print("\nNOTE: Algorithms returned different equal/near-equal routes; inspect costs.")

    if leg2_free_a["edge_path"] != leg2_cong_a["edge_path"]:
        print("\nSUCCESS: Congestion changed the selected ambulance route.")
    else:
        print("\nINFO: Route did not change; increase/expand congestion scores for this scenario.")

    print("\nNEXT INTEGRATION:")
    print("traffic_density.py scores -> SUMO edge IDs -> this router -> TraCI ambulance route")


if __name__ == "__main__":
    main()
