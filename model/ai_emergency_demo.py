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
        "--log", str(sumo_log),
        "--error-log", str(sumo_error_log),
    ]

    print("\n" + "=" * 96)
    print("STEP 3 - SUMO + TRACI + GREEN CORRIDOR + LIVE BACKEND EVENTS")
    print("=" * 96)
    print("Starting SUMO-GUI...")
    print(f"Green trigger : {gc.PREEMPT_DISTANCE_M:.0f} m before TLS")
    print(f"Green hold    : {gc.GREEN_HOLD_SECONDS:.0f} s")

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

        while gc.traci.simulation.getMinExpectedNumber() > 0:
            gc.traci.simulationStep()
            step += 1

            sim_time = gc.traci.simulation.getTime()
            vehicle_ids = gc.traci.vehicle.getIDList()

            if AMBULANCE_ID not in vehicle_ids:
                if step > 3:
                    if controller:
                        controller.restore_all()

                    arrived = True

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
            speed_kmh = gc.traci.vehicle.getSpeed(AMBULANCE_ID) * 3.6
            lane_id = gc.traci.vehicle.getLaneID(AMBULANCE_ID)

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
                        "route_length": len(full_route),
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
                    f"route_index={route_index}/{len(full_route)-1}"
                )

                emit_log(
                    publisher,
                    f"Ambulance entered {road_id}.",
                    edge_id=road_id,
                    route_index=route_index,
                    simulation_time=sim_time,
                )

                last_edge = road_id

            if (
                not pickup_announced
                and route_index >= len(leg1["edge_path"])
            ):
                print(f"\n>>> EMERGENCY PICKUP {pickup} REACHED")
                print(
                    f">>> Continuing on the AI-selected hospital route "
                    f"to {hospital}.\n"
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
                    f"Emergency pickup {pickup} reached.",
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

    args = parser.parse_args()

    model_dir = Path(__file__).resolve().parent
    project_dir = model_dir.parent

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
    )


if __name__ == "__main__":
    main()
