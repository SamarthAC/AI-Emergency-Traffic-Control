r"""Real V4 CNN -> traffic density -> SUMO edge -> A* integration."""
import argparse
from pathlib import Path

from inference_v4 import TrafficInferenceV4
from edge_traffic_manager import EdgeTrafficManager
from traffic_routing import SumoRoadGraph

def show_route(r):
    print("\n" + "=" * 92)
    print("AI CONGESTION-AWARE AMBULANCE ROUTE")
    print("=" * 92)
    print("Junction path :", " -> ".join(r["junction_path"]))
    print("Edge path     :", " -> ".join(r["edge_path"]))
    print(f"Distance      : {r['distance_m']:.2f} m")
    print(f"Free-flow time: {r['base_travel_time_s']:.2f} s")
    print(f"AI route cost : {r['dynamic_cost_s']:.2f} s")
    print("=" * 92)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--camera", nargs=2, action="append",
                   metavar=("CAMERA_ID", "IMAGE_PATH"), required=True)
    p.add_argument("--start", default="J23")
    p.add_argument("--destination", default="J47")
    p.add_argument("--traffic-json", default=None)
    args = p.parse_args()

    model_dir = Path(__file__).resolve().parent
    net = model_dir.parent / "simulation" / "bengaluru_structured" / "bengaluru_structured.net.xml"
    if not net.exists():
        raise FileNotFoundError(f"SUMO network not found:\n{net}")

    print("\nLoading TrafficDetectorV4 once...")
    detector = TrafficInferenceV4()
    print("Model device:", detector.device)
    manager = EdgeTrafficManager()

    print("\n" + "=" * 92)
    print("REAL AI CAMERA TRAFFIC ANALYSIS")
    print("=" * 92)

    for camera_id, raw_path in args.camera:
        if camera_id not in manager.camera_edge_map:
            raise KeyError(
                f"Unknown camera '{camera_id}'. Valid cameras: "
                + ", ".join(manager.get_known_camera_ids())
            )

        image = Path(raw_path)
        if not image.is_absolute():
            if (Path.cwd() / image).exists():
                image = Path.cwd() / image
            elif (model_dir / image).exists():
                image = model_dir / image
        if not image.exists():
            raise FileNotFoundError(f"Image for {camera_id} not found:\n{image}")

        # REAL custom V4 CNN inference.
        inference = detector.predict(image)

        # REAL calibrated density calculation and camera -> SUMO edge mapping.
        density = manager.update_from_inference(camera_id, inference)

        print(f"\n{camera_id}")
        print("  Image              :", image.name)
        print("  CNN detections     :", inference["vehicle_count"])
        print("  Non-ambulance      :", inference["non_ambulance_vehicle_count"])
        print("  Ambulance detected :", inference["ambulance_detected"])
        print(f"  Traffic score      : {density['traffic_score']:.2f}")
        print("  Traffic level      :", density["traffic_level"])
        print("  SUMO edges         :", ", ".join(density["mapped_edges"]))

    graph = SumoRoadGraph(net)
    manager.apply_to_graph(graph)
    route = graph.astar(args.start, args.destination)

    manager.print_status()
    show_route(route)

    out = Path(args.traffic_json) if args.traffic_json else model_dir / "live_edge_traffic.json"
    manager.save_routing_json(out)

    print("\n" + "=" * 92)
    print("REAL AI INTEGRATION RESULT")
    print("=" * 92)
    print("PASS: V4 CNN inference completed for all supplied cameras.")
    print("PASS: traffic_density.py converted detections into traffic scores.")
    print("PASS: camera scores were mapped onto SUMO road edges.")
    print("PASS: A* used the resulting AI congestion costs.")
    print(f"\nTraffic JSON saved to:\n{out}")
    print("=" * 92)

if __name__ == "__main__":
    main()
