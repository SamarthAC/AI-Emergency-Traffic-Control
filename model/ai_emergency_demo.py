r"""
AI Smart Ambulance - backend-connected end-to-end demo.

Runtime chain:
Real road images
-> V4 CNN
-> traffic density
-> SUMO edge scores
-> congestion-aware A*
-> TraCI ambulance
-> adaptive Green Corridor
-> FastAPI /events
-> WebSocket dashboard

Place in:
    AI Traffic Control\model\ai_emergency_demo.py

Required beside it:
    inference_v4.py
    traffic_density.py
    edge_traffic_manager.py
    traffic_routing.py
    green_corridor_demo.py
    backend_bridge.py

FastAPI must be running on http://127.0.0.1:8000 unless another
--backend-url is supplied.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

from inference_v4 import TrafficInferenceV4
from edge_traffic_manager import EdgeTrafficManager
from traffic_routing import SumoRoadGraph
from backend_bridge import BackendEventPublisher
from hospital_selector import HospitalSelector
from junction_camera_manager import JunctionCameraManager

import green_corridor_demo as gc


AMBULANCE_ID = "AI_AMB_001"
ROUTE_ID = "AI_DYNAMIC_EMERGENCY_ROUTE"

# Send live vehicle state every N simulation seconds.
VEHICLE_PUBLISH_INTERVAL_S = 2.0

# Re-analyse simulated live CCTV traffic every N SUMO seconds.
REALTIME_TRAFFIC_UPDATE_INTERVAL_S = 30.0

# Dynamic rerouting policy.
MIN_REROUTE_IMPROVEMENT = 0.10
REROUTE_COOLDOWN_S = 30.0

# Emergency-vehicle driving policy.
# We keep SUMO collision/safety checks enabled, but make the ambulance more
# assertive and equip it with SUMO's native blue-light rescue-lane behavior.
AMBULANCE_SPEED_FACTOR = 1.15
AMBULANCE_BLUE_LIGHT_REACTION_DISTANCE_M = 75.0
AMBULANCE_LC_STRATEGIC = 5.0
AMBULANCE_LC_SPEED_GAIN = 2.0
AMBULANCE_LC_ASSERTIVE = 2.0

# Stopless-corridor traffic clearing. Nearby leaders are encouraged to move
# aside using SUMO's native blue-light device first; if a leader remains
# immediately in front of the ambulance, we temporarily request a safe
# adjacent-lane change for that leader.
BLOCKER_CLEAR_DISTANCE_M = 35.0
BLOCKER_FORCE_GAP_M = 12.0
BLOCKER_LANE_CHANGE_DURATION_S = 8.0
BLOCKER_ACTION_COOLDOWN_S = 4.0

REALTIME_PHASE_FALLBACKS = {
    "phase_1": {
        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",
        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",
        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",
        "CAM_ORR_NORTH": "high3.jpg",
        "CAM_ORR_SOUTH": "high4.jpg",
    },
    "phase_2": {
        "CAM_HOSPITAL_DIRECT_1": "high2.jpg",
        "CAM_HOSPITAL_DIRECT_2": "high3.jpg",
        "CAM_HOSPITAL_DIRECT_3": "high4.jpg",
        "CAM_ORR_NORTH": "low1.jpeg",
        "CAM_ORR_SOUTH": "low2.jpg",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit_log(publisher, message: str, level: str = "INFO", **extra):
    if publisher is None:
        return

    data = {
        "level": level,
        "message": message,
        "timestamp": utc_now(),
    }
    data.update(extra)
    publisher.publish("LOG", data)


def resolve_image_path(raw_path: str, model_dir: Path) -> Path:
    image = Path(raw_path)

    if image.is_absolute():
        return image

    cwd_candidate = Path.cwd() / image
    model_candidate = model_dir / image

    if cwd_candidate.exists():
        return cwd_candidate

    if model_candidate.exists():
        return model_candidate

    return image


def print_route(title: str, result: dict):
    print("\n" + "=" * 96)
    print(title)
    print("=" * 96)
    print("Junction path :", " -> ".join(result["junction_path"]))
    print("Edge path     :", " -> ".join(result["edge_path"]))
    print(f"Distance      : {result['distance_m']:.2f} m")
    print(f"Free-flow time: {result['base_travel_time_s']:.2f} s")
    print(f"AI route cost : {result['dynamic_cost_s']:.2f} s")
    print("=" * 96)


def analyse_cameras(
    detector: TrafficInferenceV4,
    manager: EdgeTrafficManager,
    camera_args,
    model_dir: Path,
    publisher: BackendEventPublisher,
):
    print("\n" + "=" * 96)
    print("STEP 1 - REAL V4 CNN TRAFFIC ANALYSIS")
    print("=" * 96)

    for camera_id, raw_path in camera_args:
        if camera_id not in manager.camera_edge_map:
            raise KeyError(
                f"Unknown camera '{camera_id}'. Valid cameras: "
                + ", ".join(manager.get_known_camera_ids())
            )

        image = resolve_image_path(raw_path, model_dir)

        if not image.exists():
            raise FileNotFoundError(
                f"Image for {camera_id} not found:\n{image}"
            )

        inference = detector.predict(image)
        density = manager.update_from_inference(camera_id, inference)

        print(f"\n{camera_id}")
        print("  Image              :", image.name)
        print("  CNN detections     :", inference["vehicle_count"])
        print("  Non-ambulance      :", inference["non_ambulance_vehicle_count"])
        print("  Ambulance detected :", inference["ambulance_detected"])
        print(f"  Traffic score      : {density['traffic_score']:.2f}")
        print("  Traffic level      :", density["traffic_level"])
        print("  SUMO edges         :", ", ".join(density["mapped_edges"]))

        publisher.publish(
            "TRAFFIC_OVERVIEW",
            {
                "camera_id": camera_id,
                "image": image.name,
                "edge_ids": density["mapped_edges"],
                "vehicle_count": inference["non_ambulance_vehicle_count"],
                "cnn_detection_count": inference["vehicle_count"],
                "ambulance_detected": inference["ambulance_detected"],
                "traffic_score": round(density["traffic_score"], 2),
                "traffic_level": density["traffic_level"],
                "timestamp": utc_now(),
            },
        )



def _find_camera_image_in_phase(
    phase_dir: Path,
    camera_id: str,
    fallback_name: str | None = None,
) -> Path:
    """Resolve one traffic-camera frame from a realtime phase folder."""
    supported = {".jpg", ".jpeg", ".png"}

    for suffix in supported:
        candidate = phase_dir / f"{camera_id}{suffix}"
        if candidate.exists():
            return candidate

    if fallback_name:
        candidate = phase_dir / fallback_name
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"No realtime frame found for {camera_id} in {phase_dir}. "
        f"Expected a file named after the camera ID or fallback '{fallback_name}'."
    )


def apply_realtime_traffic_phase(
    detector: TrafficInferenceV4,
    manager: EdgeTrafficManager,
    graph: SumoRoadGraph,
    phase_dir: Path,
    phase_name: str,
    publisher: BackendEventPublisher,
    routing_json: Path | None = None,
):
    """
    Re-run CNN traffic analysis for a simulated live CCTV phase,
    update EdgeTrafficManager, and push the new scores into the routing graph.

    Step 1 intentionally updates traffic only. It does not reroute yet.
    """
    fallback_map = REALTIME_PHASE_FALLBACKS.get(phase_name, {})
    camera_ids = list(fallback_map.keys())

    if not phase_dir.exists():
        raise FileNotFoundError(
            f"Realtime traffic phase folder not found:\n{phase_dir}"
        )

    print("\n" + "=" * 96)
    print(f"[REAL-TIME TRAFFIC UPDATE] phase={phase_name}")
    print("=" * 96)

    updated = []

    for camera_id in camera_ids:
        if camera_id not in manager.camera_edge_map:
            print(f"[WARN] Unknown realtime traffic camera: {camera_id}")
            continue

        image = _find_camera_image_in_phase(
            phase_dir,
            camera_id,
            fallback_map.get(camera_id),
        )

        inference = detector.predict(image)
        density = manager.update_from_inference(camera_id, inference)

        print(
            f"{camera_id:24s} "
            f"image={image.name:14s} "
            f"score={density['traffic_score']:6.2f} "
            f"level={density['traffic_level']:6s} "
            f"vehicles={inference['non_ambulance_vehicle_count']:3d}"
        )

        publisher.publish(
            "TRAFFIC_OVERVIEW",
            {
                "camera_id": camera_id,
                "image": image.name,
                "edge_ids": density["mapped_edges"],
                "vehicle_count": inference["non_ambulance_vehicle_count"],
                "cnn_detection_count": inference["vehicle_count"],
                "ambulance_detected": inference["ambulance_detected"],
                "traffic_score": round(density["traffic_score"], 2),
                "traffic_level": density["traffic_level"],
                "source_mode": "realtime_phase_demo",
                "phase": phase_name,
                "timestamp": utc_now(),
            },
        )

        updated.append(camera_id)

    manager.apply_to_graph(graph)

    if routing_json is not None:
        manager.save_routing_json(routing_json)

    print("-" * 96)
    print("Traffic graph updated from latest CNN phase.")
    print("Traffic graph updated. Dynamic reroute evaluation follows.")
    print("=" * 96)

    emit_log(
        publisher,
        f"Realtime traffic phase {phase_name} applied.",
        phase=phase_name,
        updated_cameras=len(updated),
    )


def select_hospital_and_build_route(
    graph: SumoRoadGraph,
    station: str,
    pickup: str,
    hospital_data_file: Path,
    publisher: BackendEventPublisher,
):
    """
    1. Compute station -> pickup.
    2. Evaluate every medically eligible hospital from hospital_data.json.
    3. A* computes pickup -> hospital for each eligible candidate.
    4. Choose the eligible hospital with the lowest traffic-aware route cost.
    """
    leg1 = graph.astar(station, pickup)

    if not leg1:
        raise RuntimeError(
            "A* could not calculate the ambulance station-to-pickup route."
        )

    selector = HospitalSelector.from_json(hospital_data_file)
    selection = selector.select(graph, pickup)

    selected = selection["selected_hospital"]
    leg2 = selected["route"]
    hospital = selected["junction_id"]
    hospital_name = selected["name"]

    full_route = list(leg1["edge_path"]) + list(leg2["edge_path"])

    print("\n" + "=" * 96)
    print("STEP 2B - DYNAMIC HOSPITAL EVALUATION")
    print("=" * 96)

    for candidate in selection["candidates"]:
        if candidate["eligible"]:
            print(
                f"{candidate['name']:24s} "
                f"junction={candidate['junction_id']:4s} "
                f"beds={candidate['beds_available']:2d} "
                f"doctors={candidate['doctors_available']:2d} "
                f"route_cost={candidate['dynamic_cost_s']:.2f} s "
                f"distance={candidate['distance_m']:.2f} m"
            )
        else:
            reason = ", ".join(candidate["reasons"]) or "Not eligible"
            print(
                f"{candidate['name']:24s} "
                f"junction={candidate['junction_id']:4s} "
                f"NOT ELIGIBLE - {reason}"
            )

    print("-" * 96)
    print(f"SELECTED HOSPITAL : {hospital_name} ({hospital})")
    print(f"REASON            : {selection['selection_reason']}")
    print("=" * 96)

    publisher.publish(
        "HOSPITAL_SELECTION",
        {
            "pickup": pickup,
            "selected_hospital": {
                "hospital_id": selected["hospital_id"],
                "name": hospital_name,
                "junction_id": hospital,
                "beds_available": selected["beds_available"],
                "doctors_available": selected["doctors_available"],
                "dynamic_cost_s": round(selected["dynamic_cost_s"], 2),
                "distance_m": round(selected["distance_m"], 2),
            },
            "candidates": [
                {
                    "hospital_id": c["hospital_id"],
                    "name": c["name"],
                    "junction_id": c["junction_id"],
                    "beds_available": c["beds_available"],
                    "doctors_available": c["doctors_available"],
                    "eligible": c["eligible"],
                    "reasons": c["reasons"],
                    "dynamic_cost_s": (
                        round(c["dynamic_cost_s"], 2)
                        if c["dynamic_cost_s"] is not None
                        else None
                    ),
                    "distance_m": (
                        round(c["distance_m"], 2)
                        if c["distance_m"] is not None
                        else None
                    ),
                }
                for c in selection["candidates"]
            ],
            "selection_reason": selection["selection_reason"],
            "timestamp": utc_now(),
        },
    )

    emit_log(
        publisher,
        f"Hospital selected: {hospital_name} ({hospital}).",
        hospital_id=selected["hospital_id"],
        hospital_name=hospital_name,
        hospital_junction=hospital,
        beds_available=selected["beds_available"],
        doctors_available=selected["doctors_available"],
        dynamic_cost_s=round(selected["dynamic_cost_s"], 2),
    )

    return leg1, leg2, full_route, hospital, hospital_name, selection

def publish_route(
    publisher: BackendEventPublisher,
    leg1: dict,
    leg2: dict,
    full_route: list[str],
    station: str,
    pickup: str,
    hospital: str,
    hospital_name: str,
):
    publisher.publish(
        "AI_ROUTE",
        {
            "ambulance_id": AMBULANCE_ID,
            "station": station,
            "pickup": pickup,
            "destination": hospital,
            "destination_name": hospital_name,
            "route": full_route,
            "station_to_pickup": {
                "junction_path": leg1["junction_path"],
                "edge_path": leg1["edge_path"],
                "distance_m": round(leg1["distance_m"], 2),
                "free_flow_time_s": round(leg1["base_travel_time_s"], 2),
                "dynamic_cost_s": round(leg1["dynamic_cost_s"], 2),
            },
            "pickup_to_hospital": {
                "junction_path": leg2["junction_path"],
                "edge_path": leg2["edge_path"],
                "distance_m": round(leg2["distance_m"], 2),
                "free_flow_time_s": round(leg2["base_travel_time_s"], 2),
                "dynamic_cost_s": round(leg2["dynamic_cost_s"], 2),
            },
            # Routing cost, not measured SUMO arrival time.
            "route_cost_s": round(
                leg1["dynamic_cost_s"] + leg2["dynamic_cost_s"],
                2,
            ),
            "timestamp": utc_now(),
        },
    )



def build_junction_camera_image_map(
    junction_camera_manager: JunctionCameraManager,
    image_dir: Path,
) -> dict[str, Path]:
    """Assign prerecorded ambulance-demo frames to logical junction cameras."""
    if not image_dir.exists():
        raise FileNotFoundError(
            f"Junction-camera image folder not found:\n{image_dir}"
        )

    images = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    if not images:
        raise FileNotFoundError(
            f"No .jpg/.jpeg/.png ambulance demo images found in:\n{image_dir}"
        )

    mapping = {}
    camera_ids = list(junction_camera_manager.camera_by_id.keys())

    for index, camera_id in enumerate(camera_ids):
        mapping[camera_id] = images[index % len(images)]

    print("\nJUNCTION CAMERA PRERECORDED FRAME MAP")
    print("-" * 72)
    for camera_id in camera_ids:
        camera = junction_camera_manager.camera_by_id[camera_id]
        print(
            f"{camera_id:14s} -> {camera['junction_id']:4s} "
            f"-> {mapping[camera_id].name}"
        )
    print("-" * 72)
    print(
        "Source mode: prerecorded_demo "
        f"({len(images)} validated frame(s) reused across "
        f"{len(camera_ids)} logical junction cameras)"
    )

    return mapping


def run_junction_camera_inference(
    detector: TrafficInferenceV4,
    junction_camera_manager: JunctionCameraManager,
    camera_image_map: dict[str, Path],
    approach: dict,
    simulation_time: float,
):
    """Run one CNN inference for the logical camera on the current TLS approach."""
    junction_id = approach["junction_id"]
    camera = junction_camera_manager.get_camera_for_junction(junction_id)

    if camera is None:
        return None

    camera_id = str(camera["camera_id"])
    image = camera_image_map.get(camera_id)

    if image is None:
        raise KeyError(f"No demo image mapped to junction camera {camera_id}")

    inference = detector.predict(image)
    confidence = inference.get("highest_ambulance_confidence")
    confidence = float(confidence) if confidence is not None else 0.0
    detected = bool(inference.get("ambulance_detected", False))

    result = junction_camera_manager.report_detection(
        camera_id=camera_id,
        detected=detected,
        confidence=confidence,
        simulation_time=simulation_time,
        metadata={
            "source_mode": "prerecorded_demo",
            "image": image.name,
            "distance_to_signal_m": round(
                float(approach["distance_to_signal_m"]), 2
            ),
            "incoming_edge": approach["incoming_edge"],
            "outgoing_edge": approach["outgoing_edge"],
            "ambulance_count": inference.get("ambulance_count", 0),
            "ambulance_candidate_count": inference.get(
                "ambulance_candidate_count",
                inference.get("ambulance_count", 0),
            ),
        },
    )

    print(
        f"\n[JUNCTION CAMERA CNN] {camera_id} -> {junction_id}"
        f"\n  Frame              : {image.name}"
        f"\n  Source mode        : prerecorded_demo"
        f"\n  Ambulance detected : {detected}"
        f"\n  Confidence         : {confidence:.4f}"
        f"\n  Distance to signal : {approach['distance_to_signal_m']:.1f} m"
    )

    return result


def _remaining_route_cost(
    graph: SumoRoadGraph,
    route_edges: list[str],
) -> float:
    """
    Return the current dynamic traffic-aware cost for SUMO edge IDs.

    SumoRoadGraph stores RoadEdge objects in graph.edges, and each RoadEdge
    exposes dynamic_time_s as a property.
    """
    total = 0.0

    for edge_id in route_edges:
        edge = graph.edges.get(edge_id)
        if edge is None:
            return float("inf")

        total += float(edge.dynamic_time_s)

    return total


def attempt_dynamic_reroute(
    graph: SumoRoadGraph,
    controller,
    pickup: str,
    pickup_reached: bool,
    hospital: str,
    publisher: BackendEventPublisher,
    sim_time: float,
    last_reroute_time: float,
):
    """
    Recalculate a traffic-aware route from the end of the ambulance's
    current edge.

    BEFORE pickup:
        current position -> pickup -> selected hospital

    AFTER pickup:
        current position -> selected hospital

    TraCI setRoute() requires the current edge to remain the first edge of the
    replacement route, so only the suffix after that edge is recalculated.
    """
    if sim_time - last_reroute_time < REROUTE_COOLDOWN_S:
        return False, last_reroute_time

    if AMBULANCE_ID not in gc.traci.vehicle.getIDList():
        return False, last_reroute_time

    current_edge = gc.traci.vehicle.getRoadID(AMBULANCE_ID)
    if not current_edge or current_edge.startswith(":"):
        return False, last_reroute_time

    current_route = list(gc.traci.vehicle.getRoute(AMBULANCE_ID))
    current_index = gc.traci.vehicle.getRouteIndex(AMBULANCE_ID)

    if current_index < 0 or current_index >= len(current_route):
        return False, last_reroute_time

    edge_nodes = controller.edge_nodes.get(current_edge)
    if not edge_nodes:
        return False, last_reroute_time

    next_junction = edge_nodes[1]

    # Build a candidate suffix that preserves the emergency workflow.
    # The ambulance MUST reach pickup before it is allowed to route directly
    # to the selected hospital.
    try:
        if not pickup_reached:
            if next_junction == pickup:
                to_pickup_edges = []
            else:
                to_pickup = graph.astar(next_junction, pickup)
                to_pickup_edges = list(to_pickup["edge_path"])

            pickup_to_hospital = graph.astar(pickup, hospital)
            candidate_suffix = (
                to_pickup_edges
                + list(pickup_to_hospital["edge_path"])
            )
            routing_target = f"{pickup} -> {hospital}"
            route_stage = "PRE_PICKUP"
        else:
            if next_junction == hospital:
                return False, last_reroute_time

            to_hospital = graph.astar(next_junction, hospital)
            candidate_suffix = list(to_hospital["edge_path"])
            routing_target = hospital
            route_stage = "POST_PICKUP"

    except ValueError as exc:
        print(
            f"[REROUTE] No valid {route_stage if 'route_stage' in locals() else ''} "
            f"route from {next_junction}: {exc}. Keeping current route."
        )
        return False, last_reroute_time

    current_remaining = current_route[current_index:]
    candidate_route = [current_edge] + candidate_suffix

    if candidate_route == current_remaining:
        print(
            f"[REROUTE CHECK t={sim_time:.1f}s] "
            f"Current {route_stage.lower()} route is still optimal."
        )
        return False, last_reroute_time

    # Both alternatives must finish the already-entered current edge, so compare
    # only the suffix after that edge.
    current_suffix = current_remaining[1:]

    old_cost = _remaining_route_cost(graph, current_suffix)
    new_cost = _remaining_route_cost(graph, candidate_suffix)

    if old_cost <= 0.0 or old_cost == float("inf"):
        return False, last_reroute_time

    improvement = (old_cost - new_cost) / old_cost

    print("\n" + "=" * 96)
    print(f"[DYNAMIC REROUTE CHECK] t={sim_time:.1f}s")
    print(f"Route stage         : {route_stage}")
    print(f"Current edge        : {current_edge}")
    print(f"Routing from        : {next_junction}")
    print(f"Required waypoint   : {pickup if not pickup_reached else 'already reached'}")
    print(f"Routing target      : {routing_target}")
    print(f"Current suffix cost : {old_cost:.2f} s")
    print(f"Candidate A* cost   : {new_cost:.2f} s")
    print(f"Improvement         : {improvement * 100.0:.2f}%")
    print(f"Required            : {MIN_REROUTE_IMPROVEMENT * 100.0:.0f}%")

    if improvement < MIN_REROUTE_IMPROVEMENT:
        print("Decision            : KEEP CURRENT ROUTE")
        print("=" * 96)
        return False, last_reroute_time

    try:
        gc.traci.vehicle.setRoute(AMBULANCE_ID, candidate_route)
    except Exception as exc:
        print(f"Decision            : REROUTE FAILED - {exc}")
        print("=" * 96)
        return False, last_reroute_time

    # Rebuild the rolling corridor from the exact route accepted by TraCI.
    controller.update_route(candidate_route)

    print("Decision            : REROUTE APPLIED")
    print("New route           :", " -> ".join(candidate_route))
    print("=" * 96)

    publisher.publish(
        "AI_ROUTE",
        {
            "ambulance_id": AMBULANCE_ID,
            "pickup": pickup,
            "pickup_reached": pickup_reached,
            "destination": hospital,
            "route_stage": route_stage,
            "route": candidate_route,
            "rerouted": True,
            "reroute_from_edge": current_edge,
            "reroute_from_junction": next_junction,
            "old_remaining_cost_s": round(old_cost, 2),
            "new_remaining_cost_s": round(new_cost, 2),
            "improvement_percent": round(improvement * 100.0, 2),
            "simulation_time": sim_time,
            "timestamp": utc_now(),
        },
    )

    emit_log(
        publisher,
        "Ambulance dynamically rerouted after live traffic update.",
        current_edge=current_edge,
        routing_from=next_junction,
        pickup=pickup,
        pickup_reached=pickup_reached,
        destination=hospital,
        route_stage=route_stage,
        improvement_percent=round(improvement * 100.0, 2),
        new_route=candidate_route,
        simulation_time=sim_time,
    )

    return True, sim_time



def configure_emergency_vehicle_priority() -> None:
    """
    Configure the ambulance for smoother emergency movement while preserving
    SUMO safety constraints.

    The blue-light device (enabled in the SUMO command) makes nearby vehicles
    react and form a rescue corridor. These per-vehicle settings additionally
    improve strategic lane choice and speed-gain behavior.
    """
    settings_applied = []

    def try_apply(label, fn):
        try:
            fn()
            settings_applied.append(label)
        except Exception as exc:
            print(f"[EMERGENCY PRIORITY WARN] {label}: {exc}")

    # Ensure the native blue-light visuals/behavior are associated with an
    # emergency-class vehicle.
    try_apply(
        "vehicle class = emergency",
        lambda: gc.traci.vehicle.setVehicleClass(
            AMBULANCE_ID,
            "emergency",
        ),
    )

    try_apply(
        "shape class = emergency",
        lambda: gc.traci.vehicle.setShapeClass(
            AMBULANCE_ID,
            "emergency",
        ),
    )

    # A modest speed preference. SUMO still applies its car-following,
    # collision-avoidance and junction safety logic.
    try_apply(
        f"speed factor = {AMBULANCE_SPEED_FACTOR}",
        lambda: gc.traci.vehicle.setSpeedFactor(
            AMBULANCE_ID,
            AMBULANCE_SPEED_FACTOR,
        ),
    )

    # Explicitly retain normal safety checks rather than turning the ambulance
    # into a collision-ignoring "ghost" vehicle.
    try_apply(
        "speed mode = safe default (31)",
        lambda: gc.traci.vehicle.setSpeedMode(
            AMBULANCE_ID,
            31,
        ),
    )

    # Keep SUMO's default safety-aware lane-change mode. The behavioral
    # parameters below make strategic/speed-gain lane changes more proactive.
    try_apply(
        "lane change mode = safety-aware (1621)",
        lambda: gc.traci.vehicle.setLaneChangeMode(
            AMBULANCE_ID,
            1621,
        ),
    )

    lane_change_params = {
        "lcStrategic": AMBULANCE_LC_STRATEGIC,
        "lcSpeedGain": AMBULANCE_LC_SPEED_GAIN,
        "lcAssertive": AMBULANCE_LC_ASSERTIVE,
    }

    for name, value in lane_change_params.items():
        try_apply(
            f"laneChangeModel.{name} = {value}",
            lambda n=name, v=value: gc.traci.vehicle.setParameter(
                AMBULANCE_ID,
                f"laneChangeModel.{n}",
                str(v),
            ),
        )

    print("\nEMERGENCY VEHICLE PRIORITY")
    print("-" * 72)
    print(
        f"Blue-light reaction distance : "
        f"{AMBULANCE_BLUE_LIGHT_REACTION_DISTANCE_M:.0f} m"
    )
    print(f"Speed factor                 : {AMBULANCE_SPEED_FACTOR:.2f}")
    print("Safety mode                  : collision/junction safety retained")
    print("Lane behavior                : more strategic + assertive")
    print(
        f"Applied settings             : "
        f"{len(settings_applied)}/{5 + len(lane_change_params)}"
    )
    print("-" * 72)




def clear_immediate_ambulance_blocker(
    sim_time: float,
    last_actions: dict[str, float],
) -> None:
    """
    Ask a close leader to yield into an adjacent lane when one exists.

    This is deliberately conservative:
    - only the immediate leader is considered;
    - only leaders within BLOCKER_CLEAR_DISTANCE_M are touched;
    - SUMO's lane-change safety checks remain enabled;
    - no teleporting, collision disabling, or forced speed override is used.
    """
    try:
        leader = gc.traci.vehicle.getLeader(
            AMBULANCE_ID,
            BLOCKER_CLEAR_DISTANCE_M,
        )
    except Exception:
        return

    if not leader:
        return

    leader_id, gap = leader
    gap = float(gap)
    if gap > BLOCKER_FORCE_GAP_M:
        return

    last = float(last_actions.get(leader_id, -9999.0))
    if sim_time - last < BLOCKER_ACTION_COOLDOWN_S:
        return

    try:
        lane_index = int(gc.traci.vehicle.getLaneIndex(leader_id))
        road_id = gc.traci.vehicle.getRoadID(leader_id)
        if not road_id or road_id.startswith(":"):
            return

        lane_count = int(gc.traci.edge.getLaneNumber(road_id))
        candidates = []
        if lane_index - 1 >= 0:
            candidates.append(lane_index - 1)
        if lane_index + 1 < lane_count:
            candidates.append(lane_index + 1)

        if not candidates:
            return

        # Prefer a lane different from the ambulance lane when possible.
        ambulance_lane = int(gc.traci.vehicle.getLaneIndex(AMBULANCE_ID))
        candidates.sort(key=lambda idx: idx == ambulance_lane)

        for target_lane in candidates:
            try:
                gc.traci.vehicle.changeLane(
                    leader_id,
                    target_lane,
                    BLOCKER_LANE_CHANGE_DURATION_S,
                )
                last_actions[leader_id] = float(sim_time)
                print(
                    f"[EMERGENCY PATH CLEAR] leader={leader_id} "
                    f"gap={gap:.1f}m lane={lane_index}->{target_lane}"
                )
                return
            except Exception:
                continue
    except Exception:
        return


def diagnose_ambulance_stop(controller, road_id: str, lane_id: str) -> dict:
    """Collect non-invasive evidence about why the ambulance is stationary."""
    result = {
        "reason": "UNKNOWN",
        "tls_id": None,
        "tls_state": None,
        "tls_distance_m": None,
        "leader_id": None,
        "leader_gap_m": None,
        "road_id": road_id,
        "lane_id": lane_id,
        "near_intersection": False,
    }

    # Vehicle directly ahead is the strongest evidence of traffic blockage.
    try:
        leader = gc.traci.vehicle.getLeader(AMBULANCE_ID, 100.0)
        if leader:
            result["leader_id"] = leader[0]
            result["leader_gap_m"] = float(leader[1])
    except Exception:
        pass

    # Upcoming traffic-light state for this vehicle.
    try:
        tls_info = gc.traci.vehicle.getNextTLS(AMBULANCE_ID)
        if tls_info:
            tls_id, _, distance_m, state = tls_info[0]
            result["tls_id"] = str(tls_id)
            result["tls_distance_m"] = float(distance_m)
            result["tls_state"] = str(state)
            result["near_intersection"] = float(distance_m) <= 40.0
    except Exception:
        pass

    # Internal SUMO roads represent movement through a junction.
    if road_id and road_id.startswith(":"):
        result["near_intersection"] = True

    state = (result["tls_state"] or "").lower()
    gap = result["leader_gap_m"]
    tls_dist = result["tls_distance_m"]

    if gap is not None and gap <= 15.0:
        result["reason"] = "VEHICLE_AHEAD"
    elif (
        tls_dist is not None
        and tls_dist <= 30.0
        and state in {"r", "y"}
    ):
        result["reason"] = "TRAFFIC_SIGNAL"
        result["near_intersection"] = True
    elif result["near_intersection"]:
        result["reason"] = "JUNCTION_CONFLICT_OR_GEOMETRY"
    elif gap is not None:
        result["reason"] = "TRAFFIC_AHEAD"
    else:
        result["reason"] = "CAR_FOLLOWING_OR_LANE_CHANGE"

    return result


def run_sumo(
    cfg_file: Path,
    net_file: Path,
    leg1: dict,
    leg2: dict,
    full_route: list[str],
    threshold: float,
    hold: float,
    delay_ms: int,
    pickup: str,
    hospital: str,
    hospital_name: str,
    publisher: BackendEventPublisher,
    junction_camera_manager: JunctionCameraManager,
    detector: TrafficInferenceV4,
    junction_camera_image_map: dict[str, Path],
    graph: SumoRoadGraph,
    traffic_manager: EdgeTrafficManager,
    realtime_traffic_dir: Path | None = None,
    realtime_update_interval_s: float = REALTIME_TRAFFIC_UPDATE_INTERVAL_S,
    routing_json: Path | None = None,
):
    gc.PREEMPT_DISTANCE_M = max(20.0, threshold)
    gc.GREEN_HOLD_SECONDS = max(5.0, hold)

    edge_nodes = gc.parse_edge_nodes(net_file)
    sumo_gui = gc.find_sumo_gui()

    model_dir = Path(__file__).resolve().parent
    sumo_log = model_dir / "sumo_ai_emergency.log"
    sumo_error_log = model_dir / "sumo_ai_emergency_error.log"

    sumo_cmd = [
        sumo_gui,
        "-c", str(cfg_file),
        "--start",
        "--delay", str(max(0, delay_ms)),
        "--device.bluelight.explicit", AMBULANCE_ID,
        "--device.bluelight.reactiondist",
        str(AMBULANCE_BLUE_LIGHT_REACTION_DISTANCE_M),
        "--log", str(sumo_log),
        "--error-log", str(sumo_error_log),
    ]

    print("\n" + "=" * 96)
    print("STEP 3 - SUMO + TRACI + GREEN CORRIDOR + LIVE BACKEND EVENTS")
    print("=" * 96)
    print("Starting SUMO-GUI...")
    print(f"Green trigger : {gc.PREEMPT_DISTANCE_M:.0f} m before TLS")
    print(f"Green hold    : {gc.GREEN_HOLD_SECONDS:.0f} s")
    print(
        f"Blue-light    : native SUMO rescue-lane behavior, "
        f"{AMBULANCE_BLUE_LIGHT_REACTION_DISTANCE_M:.0f} m reaction"
    )

    emit_log(
        publisher,
        "Starting SUMO emergency simulation.",
        route=full_route,
    )

    gc.traci.start(sumo_cmd)

    controller = None
    arrived = False

    try:
        gc.traci.simulationStep()

        if ROUTE_ID not in gc.traci.route.getIDList():
            gc.traci.route.add(ROUTE_ID, full_route)

        gc.traci.vehicle.add(
            vehID=AMBULANCE_ID,
            routeID=ROUTE_ID,
            typeID="ambulance",
            depart="now",
            departLane="best",
            departPos="base",
            departSpeed="max",
        )

        gc.traci.vehicle.setColor(
            AMBULANCE_ID,
            gc.AMBULANCE_COLOR,
        )

        configure_emergency_vehicle_priority()
        dispatch_time = float(gc.traci.simulation.getTime())

        try:
            gc.traci.gui.trackVehicle("View #0", AMBULANCE_ID)
            gc.traci.gui.setZoom("View #0", 1400)
        except Exception:
            pass

        controller = gc.GreenCorridorController(
            AMBULANCE_ID,
            full_route,
            edge_nodes,
            publisher=publisher,
            camera_manager=junction_camera_manager,
        )

        publisher.publish(
            "AMBULANCE_STATUS",
            {
                "id": AMBULANCE_ID,
                "status": "DISPATCHED",
                "pickup": pickup,
                "destination": hospital,
                "destination_name": hospital_name,
                "route": full_route,
                "timestamp": utc_now(),
            },
        )

        emit_log(
            publisher,
            f"{AMBULANCE_ID} dispatched on AI-selected route.",
        )

        print("\nAmbulance spawned:", AMBULANCE_ID)
        print("The ambulance is following the AI-selected route.")
        print("Green Corridor controller ACTIVE.")
        print("Live backend publishing ACTIVE.\n")

        last_edge = None
        pickup_announced = False
        step = 0
        last_vehicle_publish_time = -9999.0
        processed_junction_camera_approaches = set()

        realtime_phase_dirs = []
        realtime_phase_index = 0
        next_realtime_update_time = float(realtime_update_interval_s)
        last_reroute_time = -9999.0
        # dispatch_time was captured immediately after ambulance configuration.
        pickup_time = None
        arrival_time = None
        reroute_count = 0

        # Stop-diagnostic state.
        STOP_SPEED_KMH = 1.0
        STOP_CONFIRM_SECONDS = 2.0
        stop_started_at = None
        stop_context = None
        confirmed_stop_count = 0
        intersection_stop_count = 0
        longest_stationary_s = 0.0
        minimum_moving_speed_kmh = float("inf")
        blocker_clear_actions = {}

        if realtime_traffic_dir is not None and realtime_traffic_dir.exists():
            realtime_phase_dirs = sorted(
                [
                    p for p in realtime_traffic_dir.iterdir()
                    if p.is_dir() and p.name.lower().startswith("phase_")
                ],
                key=lambda p: p.name.lower(),
            )

        if realtime_phase_dirs:
            print(
                "Realtime traffic phases loaded: "
                + ", ".join(p.name for p in realtime_phase_dirs)
            )
            print(
                f"Realtime traffic update interval: "
                f"{float(realtime_update_interval_s):.0f} simulated seconds\n"
            )
        elif realtime_traffic_dir is not None:
            print(
                f"[WARN] No phase_* folders found under {realtime_traffic_dir}. "
                "Realtime traffic updates disabled."
            )

        while gc.traci.simulation.getMinExpectedNumber() > 0:
            gc.traci.simulationStep()
            step += 1

            sim_time = gc.traci.simulation.getTime()
            vehicle_ids = gc.traci.vehicle.getIDList()

            if (
                realtime_phase_dirs
                and realtime_phase_index < len(realtime_phase_dirs)
                and sim_time >= next_realtime_update_time
            ):
                phase_dir = realtime_phase_dirs[realtime_phase_index]

                apply_realtime_traffic_phase(
                    detector=detector,
                    manager=traffic_manager,
                    graph=graph,
                    phase_dir=phase_dir,
                    phase_name=phase_dir.name,
                    publisher=publisher,
                    routing_json=routing_json,
                )

                realtime_phase_index += 1
                next_realtime_update_time += float(realtime_update_interval_s)

                rerouted, last_reroute_time = attempt_dynamic_reroute(
                    graph=graph,
                    controller=controller,
                    pickup=pickup,
                    pickup_reached=pickup_announced,
                    hospital=hospital,
                    publisher=publisher,
                    sim_time=sim_time,
                    last_reroute_time=last_reroute_time,
                )
                if rerouted:
                    reroute_count += 1

            if AMBULANCE_ID not in vehicle_ids:
                if step > 3:
                    if controller:
                        controller.restore_all()

                    arrived = True
                    arrival_time = float(sim_time)

                    dispatch_to_pickup = (
                        pickup_time - dispatch_time
                        if pickup_time is not None and dispatch_time is not None
                        else None
                    )
                    pickup_to_hospital = (
                        arrival_time - pickup_time
                        if pickup_time is not None
                        else None
                    )
                    total_emergency_time = (
                        arrival_time - dispatch_time
                        if dispatch_time is not None
                        else None
                    )

                    print("\n" + "=" * 96)
                    print("EMERGENCY RESPONSE METRICS")
                    print("=" * 96)
                    print(
                        "Dispatch -> pickup      : "
                        + (
                            f"{dispatch_to_pickup:.1f} simulated s"
                            if dispatch_to_pickup is not None
                            else "unavailable"
                        )
                    )
                    print(
                        "Pickup -> hospital      : "
                        + (
                            f"{pickup_to_hospital:.1f} simulated s"
                            if pickup_to_hospital is not None
                            else "unavailable"
                        )
                    )
                    print(
                        "Total emergency travel : "
                        + (
                            f"{total_emergency_time:.1f} simulated s"
                            if total_emergency_time is not None
                            else "unavailable"
                        )
                    )
                    print(f"Dynamic reroutes       : {reroute_count}")
                    print(f"Confirmed full stops   : {confirmed_stop_count}")
                    print(f"Intersection stops     : {intersection_stop_count}")
                    print(
                        f"Longest stationary     : "
                        f"{longest_stationary_s:.1f} simulated s"
                    )
                    print(
                        "Minimum moving speed    : "
                        + (
                            f"{minimum_moving_speed_kmh:.1f} km/h"
                            if minimum_moving_speed_kmh != float("inf")
                            else "unavailable"
                        )
                    )
                    print("=" * 96)

                    publisher.publish(
                        "EMERGENCY_METRICS",
                        {
                            "ambulance_id": AMBULANCE_ID,
                            "pickup": pickup,
                            "destination": hospital,
                            "destination_name": hospital_name,
                            "dispatch_time_s": dispatch_time,
                            "pickup_time_s": pickup_time,
                            "arrival_time_s": arrival_time,
                            "dispatch_to_pickup_s": (
                                round(dispatch_to_pickup, 2)
                                if dispatch_to_pickup is not None
                                else None
                            ),
                            "pickup_to_hospital_s": (
                                round(pickup_to_hospital, 2)
                                if pickup_to_hospital is not None
                                else None
                            ),
                            "total_emergency_travel_s": (
                                round(total_emergency_time, 2)
                                if total_emergency_time is not None
                                else None
                            ),
                            "dynamic_reroutes": reroute_count,
                            "confirmed_full_stops": confirmed_stop_count,
                            "intersection_stops": intersection_stop_count,
                            "longest_stationary_s": round(
                                longest_stationary_s,
                                2,
                            ),
                            "minimum_moving_speed_kmh": (
                                round(minimum_moving_speed_kmh, 2)
                                if minimum_moving_speed_kmh != float("inf")
                                else None
                            ),
                            "timestamp": utc_now(),
                        },
                    )

                    publisher.publish(
                        "AMBULANCE_STATUS",
                        {
                            "id": AMBULANCE_ID,
                            "status": "ARRIVED",
                            "pickup": pickup,
                            "destination": hospital,
                            "destination_name": hospital_name,
                            "simulation_time": sim_time,
                            "timestamp": utc_now(),
                        },
                    )

                    emit_log(
                        publisher,
                        f"{AMBULANCE_ID} reached {hospital_name} ({hospital}).",
                        simulation_time=sim_time,
                        dispatch_to_pickup_s=dispatch_to_pickup,
                        pickup_to_hospital_s=pickup_to_hospital,
                        total_emergency_travel_s=total_emergency_time,
                        dynamic_reroutes=reroute_count,
                    )

                    print(
                        "\n>>> Ambulance reached destination "
                        "/ left simulation."
                    )
                    break

                continue

            # Run visual ambulance confirmation once when the ambulance enters
            # the preemption zone of a configured junction camera. TraCI
            # provides route/position confirmation; the CNN provides visual
            # ambulance confirmation.
            approach = controller.get_upcoming_tls_approach()
            if approach is not None:
                junction_id = approach["junction_id"]
                if (
                    approach["distance_to_signal_m"] <= gc.PREEMPT_DISTANCE_M
                    and junction_camera_manager.has_camera(junction_id)
                    and junction_id not in processed_junction_camera_approaches
                ):
                    detection = run_junction_camera_inference(
                        detector=detector,
                        junction_camera_manager=junction_camera_manager,
                        camera_image_map=junction_camera_image_map,
                        approach=approach,
                        simulation_time=sim_time,
                    )
                    processed_junction_camera_approaches.add(junction_id)

                    if (
                        detection is not None
                        and detection.detected
                        and detection.confidence
                            >= junction_camera_manager.minimum_confidence
                        and not controller.corridor_armed
                    ):
                        controller.arm_corridor_from_camera(
                            junction_id=detection.junction_id,
                            camera_id=detection.camera_id,
                            confidence=detection.confidence,
                            simulation_time=sim_time,
                        )

            controller.update()

            road_id = gc.traci.vehicle.getRoadID(AMBULANCE_ID)
            route_index = gc.traci.vehicle.getRouteIndex(AMBULANCE_ID)
            live_route = list(gc.traci.vehicle.getRoute(AMBULANCE_ID))
            speed_kmh = gc.traci.vehicle.getSpeed(AMBULANCE_ID) * 3.6
            lane_id = gc.traci.vehicle.getLaneID(AMBULANCE_ID)

            # Active emergency-path clearing: assist the native blue-light
            # behavior when an ordinary vehicle remains directly in front.
            clear_immediate_ambulance_blocker(
                float(sim_time),
                blocker_clear_actions,
            )

            # Stop tracker used to verify the physical-pass stopless policy.
            # behavior; it tells us what is actually causing full stops.
            if speed_kmh > STOP_SPEED_KMH:
                minimum_moving_speed_kmh = min(
                    minimum_moving_speed_kmh,
                    speed_kmh,
                )
                if stop_started_at is not None:
                    stopped_for = float(sim_time - stop_started_at)
                    longest_stationary_s = max(
                        longest_stationary_s,
                        stopped_for,
                    )
                    if stopped_for >= STOP_CONFIRM_SECONDS:
                        confirmed_stop_count += 1
                        if stop_context and stop_context.get("near_intersection"):
                            intersection_stop_count += 1

                        ctx = stop_context or {}
                        print("\n[AMBULANCE STOP DIAGNOSTIC]")
                        print(f"  Duration           : {stopped_for:.1f} s")
                        print(f"  Reason             : {ctx.get('reason', 'UNKNOWN')}")
                        print(f"  Road / lane        : {ctx.get('road_id')} / {ctx.get('lane_id')}")
                        print(
                            f"  Leader             : "
                            f"{ctx.get('leader_id') or 'none'}"
                        )
                        if ctx.get("leader_gap_m") is not None:
                            print(
                                f"  Leader gap         : "
                                f"{ctx['leader_gap_m']:.1f} m"
                            )
                        print(
                            f"  Next TLS           : "
                            f"{ctx.get('tls_id') or 'none'}"
                        )
                        if ctx.get("tls_distance_m") is not None:
                            print(
                                f"  TLS distance       : "
                                f"{ctx['tls_distance_m']:.1f} m"
                            )
                        print(
                            f"  TLS state          : "
                            f"{ctx.get('tls_state') or 'n/a'}"
                        )
                        print(
                            f"  Near intersection  : "
                            f"{bool(ctx.get('near_intersection'))}"
                        )
                    stop_started_at = None
                    stop_context = None
            else:
                if stop_started_at is None:
                    stop_started_at = float(sim_time)
                    stop_context = diagnose_ambulance_stop(
                        controller,
                        road_id,
                        lane_id,
                    )
                else:
                    # Refresh evidence while stopped; a close leader or red
                    # signal that appears later is more informative.
                    latest_context = diagnose_ambulance_stop(
                        controller,
                        road_id,
                        lane_id,
                    )
                    if latest_context.get("reason") != "UNKNOWN":
                        stop_context = latest_context

            position = gc.traci.vehicle.getPosition(AMBULANCE_ID)
            x, y = float(position[0]), float(position[1])

            if sim_time - last_vehicle_publish_time >= VEHICLE_PUBLISH_INTERVAL_S:
                publisher.publish(
                    "VEHICLE_UPDATE",
                    {
                        "vehicle_id": AMBULANCE_ID,
                        "edge_id": road_id,
                        "lane_id": lane_id,
                        "route_index": route_index,
                        "route_length": len(live_route),
                        "speed_kmh": round(speed_kmh, 2),
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "simulation_time": sim_time,
                    },
                )
                last_vehicle_publish_time = sim_time

            if (
                road_id
                and not road_id.startswith(":")
                and road_id != last_edge
            ):
                print(
                    f"[t={sim_time:6.1f}s] "
                    f"edge={road_id:12s} "
                    f"speed={speed_kmh:5.1f} km/h "
                    f"route_index={route_index}/{len(live_route)-1}"
                )

                emit_log(
                    publisher,
                    f"Ambulance entered {road_id}.",
                    edge_id=road_id,
                    route_index=route_index,
                    simulation_time=sim_time,
                )

                last_edge = road_id

            # Pickup is confirmed from actual SUMO movement, not from a fixed
            # route index. After dynamic rerouting, route indexes/lengths can
            # change, so the reliable event is entering an outgoing road whose
            # FROM junction is the pickup junction.
            pickup_departed = False
            if (
                not pickup_announced
                and road_id
                and not road_id.startswith(":")
            ):
                road_nodes = edge_nodes.get(road_id)
                pickup_departed = bool(
                    road_nodes
                    and road_nodes[0] == pickup
                )

            if pickup_departed:
                pickup_time = float(sim_time)
                print(f"\n>>> EMERGENCY PICKUP {pickup} REACHED")
                print(
                    f">>> Patient collected. Continuing to "
                    f"{hospital_name} ({hospital}).\n"
                )

                publisher.publish(
                    "AMBULANCE_STATUS",
                    {
                        "id": AMBULANCE_ID,
                        "status": "EN_ROUTE_TO_HOSPITAL",
                        "pickup": pickup,
                        "pickup_reached": True,
                        "destination": hospital,
                        "destination_name": hospital_name,
                        "simulation_time": sim_time,
                        "timestamp": utc_now(),
                    },
                )

                emit_log(
                    publisher,
                    f"Emergency pickup {pickup} physically reached.",
                    edge_id=road_id,
                    simulation_time=sim_time,
                )

                pickup_announced = True

            time.sleep(0.01)

        if not arrived:
            publisher.publish(
                "AMBULANCE_STATUS",
                {
                    "id": AMBULANCE_ID,
                    "status": "SIMULATION_ENDED",
                    "pickup": pickup,
                    "destination": hospital,
                    "destination_name": hospital_name,
                    "timestamp": utc_now(),
                },
            )

        print("\n" + "=" * 96)
        print("FULL AI EMERGENCY DEMO COMPLETE")
        print("=" * 96)
        print("Runtime chain:")
        print("  V4 CNN")
        print("  -> traffic density")
        print("  -> SUMO edge traffic scores")
        print("  -> dynamic hospital selection")
        print("  -> A* dynamic route")
        print("  -> TraCI ambulance movement")
        print("  -> Junction-camera CNN ambulance confirmation")
        print("  -> Green Corridor preemption/restoration")
        print("  -> FastAPI event publishing")
        print("  -> WebSocket-ready dashboard stream")
        print("=" * 96)

    finally:
        if controller is not None:
            try:
                controller.restore_all()
            except Exception:
                pass

        try:
            gc.traci.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end AI smart ambulance demo with FastAPI/WebSocket "
            "backend publishing."
        )
    )

    parser.add_argument(
        "--camera",
        nargs=2,
        action="append",
        metavar=("CAMERA_ID", "IMAGE_PATH"),
        required=True,
    )
    parser.add_argument("--station", default="J01")
    parser.add_argument("--pickup", default="J23")
    parser.add_argument(
        "--hospital-data",
        default="hospital_data.json",
        help="JSON file containing hospital availability/capacity data.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=gc.PREEMPT_DISTANCE_M,
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=gc.GREEN_HOLD_SECONDS,
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--traffic-json",
        default=None,
    )
    parser.add_argument(
        "--backend-url",
        default="http://127.0.0.1:8000",
        help="FastAPI backend URL.",
    )
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Run simulation without sending backend events.",
    )
    parser.add_argument(
        "--junction-camera-config",
        default="junction_camera_config.json",
        help="JSON configuration for junction ambulance-detection cameras.",
    )
    parser.add_argument(
        "--junction-camera-image-dir",
        default="ambulance demo images",
        help=(
            "Folder containing validated prerecorded ambulance frames used "
            "by the virtual junction-camera demo."
        ),
    )
    parser.add_argument(
        "--realtime-traffic-dir",
        default="realtime_traffic",
        help="Folder containing phase_* subfolders for simulated live traffic.",
    )
    parser.add_argument(
        "--realtime-update-interval",
        type=float,
        default=REALTIME_TRAFFIC_UPDATE_INTERVAL_S,
        help="Simulated seconds between live traffic refreshes.",
    )
    parser.add_argument(
        "--no-realtime-traffic",
        action="store_true",
        help="Disable simulated live traffic updates.",
    )

    args = parser.parse_args()

    model_dir = Path(__file__).resolve().parent
    project_dir = model_dir.parent

    realtime_traffic_dir = None
    if not args.no_realtime_traffic:
        realtime_traffic_dir = Path(args.realtime_traffic_dir)
        if not realtime_traffic_dir.is_absolute():
            realtime_traffic_dir = model_dir / realtime_traffic_dir

    junction_camera_image_dir = Path(args.junction_camera_image_dir)
    if not junction_camera_image_dir.is_absolute():
        junction_camera_image_dir = model_dir / junction_camera_image_dir

    junction_camera_config = Path(args.junction_camera_config)
    if not junction_camera_config.is_absolute():
        junction_camera_config = model_dir / junction_camera_config

    junction_camera_manager = JunctionCameraManager(
        junction_camera_config,
        publisher=None,  # publisher attached after backend publisher is created
    )

    hospital_data_file = Path(args.hospital_data)
    if not hospital_data_file.is_absolute():
        hospital_data_file = model_dir / hospital_data_file

    if not hospital_data_file.exists():
        raise FileNotFoundError(
            f"Hospital data file not found:\n{hospital_data_file}"
        )

    net_file = (
        project_dir
        / "simulation"
        / "bengaluru_structured"
        / "bengaluru_structured.net.xml"
    )

    cfg_file = (
        project_dir
        / "simulation"
        / "bengaluru_structured"
        / "bengaluru_structured.sumocfg"
    )

    if not net_file.exists():
        raise FileNotFoundError(f"SUMO network not found:\n{net_file}")

    if not cfg_file.exists():
        raise FileNotFoundError(f"SUMO config not found:\n{cfg_file}")

    publisher = BackendEventPublisher(
        base_url=args.backend_url,
        enabled=not args.no_backend,
    )

    junction_camera_manager.publisher = publisher

    print("\n" + "=" * 96)
    print("AI SMART AMBULANCE - LIVE BACKEND DEMO")
    print("=" * 96)
    print("Station     :", args.station)
    print("Pickup      :", args.pickup)
    print("Hospital    : AUTO-SELECT (J47/J45 from hospital_data.json)")
    print("Backend     :", "OFF" if args.no_backend else args.backend_url)
    print("Junction cams:", junction_camera_manager.camera_count)
    print("=" * 96)

    emit_log(
        publisher,
        "AI emergency pipeline started.",
    )

    print("\nLoading TrafficDetectorV4 once...")
    detector = TrafficInferenceV4()
    print("Model device:", detector.device)

    junction_camera_image_map = build_junction_camera_image_map(
        junction_camera_manager,
        junction_camera_image_dir,
    )

    manager = EdgeTrafficManager()

    analyse_cameras(
        detector,
        manager,
        args.camera,
        model_dir,
        publisher,
    )

    graph = SumoRoadGraph(net_file)
    manager.apply_to_graph(graph)
    manager.print_status()

    if args.traffic_json is None:
        traffic_json = model_dir / "live_edge_traffic.json"
    else:
        traffic_json = Path(args.traffic_json)

    manager.save_routing_json(traffic_json)

    print("\nTraffic state saved to:")
    print(traffic_json)

    leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = (
        select_hospital_and_build_route(
            graph,
            args.station,
            args.pickup,
            hospital_data_file,
            publisher,
        )
    )

    print_route(
        "STEP 2A - AI ROUTE: AMBULANCE STATION -> PICKUP",
        leg1,
    )
    print_route(
        f"STEP 2C - AI ROUTE: PICKUP -> {selected_hospital_name.upper()} ({selected_hospital})",
        leg2,
    )

    print("\nFULL SUMO EDGE ROUTE:")
    print(" -> ".join(full_route))

    publish_route(
        publisher,
        leg1,
        leg2,
        full_route,
        args.station,
        args.pickup,
        selected_hospital,
        selected_hospital_name,
    )

    emit_log(
        publisher,
        "Congestion-aware A* route calculated.",
        full_route=full_route,
    )

    run_sumo(
        cfg_file=cfg_file,
        net_file=net_file,
        leg1=leg1,
        leg2=leg2,
        full_route=full_route,
        threshold=args.threshold,
        hold=args.hold,
        delay_ms=args.delay,
        pickup=args.pickup,
        hospital=selected_hospital,
        hospital_name=selected_hospital_name,
        publisher=publisher,
        junction_camera_manager=junction_camera_manager,
        detector=detector,
        junction_camera_image_map=junction_camera_image_map,
        graph=graph,
        traffic_manager=manager,
        realtime_traffic_dir=realtime_traffic_dir,
        realtime_update_interval_s=args.realtime_update_interval,
        routing_json=traffic_json,
    )


if __name__ == "__main__":
    main()
