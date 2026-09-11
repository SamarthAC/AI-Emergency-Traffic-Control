r"""
FULL AI emergency demo:
V4 CNN -> traffic density -> SUMO edge scores -> A* -> TraCI ambulance
-> adaptive Green Corridor.

Place this file in:
    AI Traffic Control\model\ai_emergency_demo.py

Required beside it:
    inference_v4.py
    traffic_density.py
    edge_traffic_manager.py
    traffic_routing.py
    green_corridor_demo.py
    model_v4.py
    traffic_detector_v4_best.pth

Example:
    python ai_emergency_demo.py ^
      --camera CAM_HOSPITAL_DIRECT_1 density_test\high2.jpg ^
      --camera CAM_HOSPITAL_DIRECT_2 density_test\high3.jpg ^
      --camera CAM_HOSPITAL_DIRECT_3 density_test\high4.jpg ^
      --camera CAM_ORR_NORTH density_test\low1.jpg ^
      --camera CAM_ORR_SOUTH density_test\low2.jpg
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from inference_v4 import TrafficInferenceV4
from edge_traffic_manager import EdgeTrafficManager
from traffic_routing import SumoRoadGraph

# Reuse the already-tested Green Corridor implementation instead of
# duplicating its TraCI / signal-phase logic.
import green_corridor_demo as gc


AMBULANCE_ID = "AI_AMB_001"
ROUTE_ID = "AI_DYNAMIC_EMERGENCY_ROUTE"


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
        density = manager.update_from_inference(
            camera_id,
            inference,
        )

        print(f"\n{camera_id}")
        print("  Image              :", image.name)
        print("  CNN detections     :", inference["vehicle_count"])
        print(
            "  Non-ambulance      :",
            inference["non_ambulance_vehicle_count"],
        )
        print(
            "  Ambulance detected :",
            inference["ambulance_detected"],
        )
        print(
            f"  Traffic score      : "
            f"{density['traffic_score']:.2f}"
        )
        print(
            "  Traffic level      :",
            density["traffic_level"],
        )
        print(
            "  SUMO edges         :",
            ", ".join(density["mapped_edges"]),
        )


def build_ai_route(
    graph: SumoRoadGraph,
    station: str,
    pickup: str,
    hospital: str,
):
    # One graph, one resolved traffic state.
    # Both legs therefore use the same current AI traffic knowledge.
    leg1 = graph.astar(station, pickup)
    leg2 = graph.astar(pickup, hospital)

    if not leg1 or not leg2:
        raise RuntimeError(
            "A* could not calculate one of the ambulance route legs."
        )

    full_route = (
        list(leg1["edge_path"])
        + list(leg2["edge_path"])
    )

    return leg1, leg2, full_route


def run_sumo(
    cfg_file: Path,
    net_file: Path,
    leg1: dict,
    leg2: dict,
    full_route: list[str],
    threshold: float,
    hold: float,
    delay_ms: int,
):
    # Update the tested Green Corridor module's runtime settings.
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
    print("STEP 3 - SUMO + TRACI + GREEN CORRIDOR")
    print("=" * 96)
    print("Starting SUMO-GUI...")
    print(
        f"Green trigger : {gc.PREEMPT_DISTANCE_M:.0f} m before TLS"
    )
    print(
        f"Green hold    : {gc.GREEN_HOLD_SECONDS:.0f} s"
    )

    gc.traci.start(sumo_cmd)

    controller = None

    try:
        # Initialize SUMO.
        gc.traci.simulationStep()

        # Register the EXACT AI-selected full route.
        if ROUTE_ID not in gc.traci.route.getIDList():
            gc.traci.route.add(
                ROUTE_ID,
                full_route,
            )

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
            gc.traci.gui.trackVehicle(
                "View #0",
                AMBULANCE_ID,
            )
            gc.traci.gui.setZoom(
                "View #0",
                1400,
            )
        except Exception:
            pass

        # Generic controller: it derives signal movements from whatever
        # route A* selected above.
        controller = gc.GreenCorridorController(
            AMBULANCE_ID,
            full_route,
            edge_nodes,
        )

        print("\nAmbulance spawned:", AMBULANCE_ID)
        print(
            "The ambulance is following the AI-selected route, "
            "not a hard-coded hospital path."
        )
        print("Green Corridor controller ACTIVE.\n")

        last_edge = None
        pickup_announced = False
        step = 0

        while gc.traci.simulation.getMinExpectedNumber() > 0:
            gc.traci.simulationStep()
            step += 1

            vehicle_ids = gc.traci.vehicle.getIDList()

            if AMBULANCE_ID not in vehicle_ids:
                if step > 3:
                    if controller:
                        controller.restore_all()

                    print(
                        "\n>>> Ambulance reached destination "
                        "/ left simulation."
                    )
                    break

                continue

            controller.update()

            road_id = gc.traci.vehicle.getRoadID(
                AMBULANCE_ID
            )
            route_index = gc.traci.vehicle.getRouteIndex(
                AMBULANCE_ID
            )
            speed_kmh = (
                gc.traci.vehicle.getSpeed(AMBULANCE_ID)
                * 3.6
            )

            if (
                road_id
                and not road_id.startswith(":")
                and road_id != last_edge
            ):
                print(
                    f"[t={gc.traci.simulation.getTime():6.1f}s] "
                    f"edge={road_id:12s} "
                    f"speed={speed_kmh:5.1f} km/h "
                    f"route_index={route_index}/{len(full_route)-1}"
                )
                last_edge = road_id

            if (
                not pickup_announced
                and route_index >= len(leg1["edge_path"])
            ):
                print("\n>>> EMERGENCY PICKUP J23 REACHED")
                print(
                    ">>> Continuing on the AI-selected "
                    "hospital route to J47.\n"
                )
                pickup_announced = True

            time.sleep(0.01)

        print("\n" + "=" * 96)
        print("FULL AI EMERGENCY DEMO COMPLETE")
        print("=" * 96)
        print("Validated runtime chain:")
        print("  V4 CNN")
        print("  -> traffic density")
        print("  -> SUMO edge traffic scores")
        print("  -> A* dynamic route")
        print("  -> TraCI ambulance movement")
        print("  -> Green Corridor preemption/restoration")
        print("  -> Hospital arrival")
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
            "End-to-end AI smart ambulance demo using real V4 CNN traffic "
            "inference, dynamic A* routing, SUMO TraCI and Green Corridor."
        )
    )

    parser.add_argument(
        "--camera",
        nargs=2,
        action="append",
        metavar=("CAMERA_ID", "IMAGE_PATH"),
        required=True,
        help=(
            "Camera ID + road image. Repeat for each monitored road/camera."
        ),
    )

    parser.add_argument(
        "--station",
        default="J01",
    )
    parser.add_argument(
        "--pickup",
        default="J23",
    )
    parser.add_argument(
        "--hospital",
        default="J47",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=gc.PREEMPT_DISTANCE_M,
        help="Green Corridor preemption distance in metres.",
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=gc.GREEN_HOLD_SECONDS,
        help="Green phase hold duration in seconds.",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=60,
        help="SUMO-GUI delay in milliseconds.",
    )
    parser.add_argument(
        "--traffic-json",
        default=None,
        help="Optional path for the full resolved edge traffic JSON.",
    )

    args = parser.parse_args()

    model_dir = Path(__file__).resolve().parent
    project_dir = model_dir.parent

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
        raise FileNotFoundError(
            f"SUMO network not found:\n{net_file}"
        )

    if not cfg_file.exists():
        raise FileNotFoundError(
            f"SUMO config not found:\n{cfg_file}"
        )

    print("\n" + "=" * 96)
    print("AI SMART AMBULANCE - END-TO-END DEMO")
    print("=" * 96)
    print("Station  :", args.station)
    print("Pickup   :", args.pickup)
    print("Hospital :", args.hospital)
    print("=" * 96)

    print("\nLoading TrafficDetectorV4 once...")
    detector = TrafficInferenceV4()
    print("Model device:", detector.device)

    manager = EdgeTrafficManager()

    analyse_cameras(
        detector,
        manager,
        args.camera,
        model_dir,
    )

    # Build SUMO graph and assign EVERY edge either:
    # - a real AI score, or
    # - the configured unobserved-road baseline.
    graph = SumoRoadGraph(net_file)
    manager.apply_to_graph(graph)

    manager.print_status()

    if args.traffic_json is None:
        traffic_json = model_dir / "live_edge_traffic.json"
    else:
        traffic_json = Path(args.traffic_json)

    manager.save_routing_json(
        traffic_json
    )

    print("\nTraffic state saved to:")
    print(traffic_json)

    leg1, leg2, full_route = build_ai_route(
        graph,
        args.station,
        args.pickup,
        args.hospital,
    )

    print_route(
        "STEP 2A - AI ROUTE: AMBULANCE STATION -> PICKUP",
        leg1,
    )

    print_route(
        "STEP 2B - AI ROUTE: PICKUP -> HOSPITAL",
        leg2,
    )

    print("\nFULL SUMO EDGE ROUTE:")
    print(" -> ".join(full_route))

    run_sumo(
        cfg_file=cfg_file,
        net_file=net_file,
        leg1=leg1,
        leg2=leg2,
        full_route=full_route,
        threshold=args.threshold,
        hold=args.hold,
        delay_ms=args.delay,
    )


if __name__ == "__main__":
    main()
