with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Fix apply_live_camera_changes to skip cameras without images
old_apply = '''def apply_live_camera_changes(
    detector: TrafficInferenceV4,
    manager: EdgeTrafficManager,
    graph: SumoRoadGraph,
    live_camera_dir: Path,
    signatures: dict[str, tuple[int, int]],
    publisher: BackendEventPublisher,
    simulation_time: float,
    routing_json: Path | None = None,
) -> list[str]:
    """Process overwritten live traffic frames and update the routing graph."""
    changed_cameras = []

    for camera_id in LIVE_TRAFFIC_CAMERA_IDS:
        try:
            image = _find_live_camera_image(live_camera_dir, camera_id)
            signature = _live_camera_signature(image)
        except Exception as exc:
            print(f"[LIVE CAMERA WARN] {camera_id}: {exc}")
            continue

        if signatures.get(camera_id) == signature:
            continue

        print("\n" + "=" * 96)
        print(f"[LIVE CAMERA CHANGE DETECTED] {camera_id}")
        print(f"Frame           : {image.name}")
        print(f"Simulation time : {simulation_time:.1f} s")

        try:
            inference = detector.predict(image)
            density = manager.update_from_inference(camera_id, inference)
        except Exception as exc:
            print(f"[LIVE CAMERA RETRY] Could not process {image.name}: {exc}")
            print("Previous traffic state retained; this frame will be retried.")
            print("=" * 96)
            continue

        signatures[camera_id] = signature
        changed_cameras.append(camera_id)

        print(f"CNN detections  : {inference['vehicle_count']}")
        print(f"Non-ambulance   : {inference['non_ambulance_vehicle_count']}")
        print(f"Traffic score   : {density['traffic_score']:.2f}")
        print(f"Traffic level   : {density['traffic_level']}")
        print("SUMO edges      :", ", ".join(density["mapped_edges"]))
        print("=" * 96)

        publisher.publish(
            "TRAFFIC_OVERVIEW",
            {
                "camera_id": camera_id,
                "image": image.name,
                "image_url": f"/api/images/traffic/{camera_id}",
                "edge_ids": density["mapped_edges"],
                "vehicle_count": inference["non_ambulance_vehicle_count"],
                "cnn_detection_count": inference["vehicle_count"],
                "ambulance_detected": inference["ambulance_detected"],
                "traffic_score": round(density["traffic_score"], 2),
                "traffic_level": density["traffic_level"],
                "source_mode": "live_camera_watch",
                "simulation_time": float(simulation_time),
                "image_version": str(signature[0]),
                "timestamp": utc_now(),
            },
        )

    if not changed_cameras:
        return []

    manager.apply_to_graph(graph)
    if routing_json is not None:
        manager.save_routing_json(routing_json)

    print("\n[LIVE TRAFFIC GRAPH UPDATED]")
    print("Changed cameras :", ", ".join(changed_cameras))
    print("A* route re-evaluation requested.")

    emit_log(
        publisher,
        "Live traffic camera frame changed; CNN traffic state refreshed.",
        changed_cameras=changed_cameras,
        simulation_time=float(simulation_time),
    )

    return changed_cameras'''

new_apply = '''def apply_live_camera_changes(
    detector: TrafficInferenceV4,
    manager: EdgeTrafficManager,
    graph: SumoRoadGraph,
    live_camera_dir: Path,
    signatures: dict[str, tuple[int, int]],
    publisher: BackendEventPublisher,
    simulation_time: float,
    routing_json: Path | None = None,
) -> list[str]:
    """Process overwritten live traffic frames and update the routing graph.
    Skips cameras that don't have image files in the live_inputs folder.
    """
    changed_cameras = []

    for camera_id in LIVE_TRAFFIC_CAMERA_IDS:
        image = _find_live_camera_image(live_camera_dir, camera_id)
        if image is None:
            continue

        try:
            signature = _live_camera_signature(image)
        except Exception as exc:
            print(f"[LIVE CAMERA WARN] {camera_id}: {exc}")
            continue

        if signatures.get(camera_id) == signature:
            continue

        print("\n" + "=" * 96)
        print(f"[LIVE CAMERA CHANGE DETECTED] {camera_id}")
        print(f"Frame           : {image.name}")
        print(f"Simulation time : {simulation_time:.1f} s")

        try:
            inference = detector.predict(image)
            density = manager.update_from_inference(camera_id, inference)
        except Exception as exc:
            print(f"[LIVE CAMERA RETRY] Could not process {image.name}: {exc}")
            print("Previous traffic state retained; this frame will be retried.")
            print("=" * 96)
            continue

        signatures[camera_id] = signature
        changed_cameras.append(camera_id)

        print(f"CNN detections  : {inference['vehicle_count']}")
        print(f"Non-ambulance   : {inference['non_ambulance_vehicle_count']}")
        print(f"Traffic score   : {density['traffic_score']:.2f}")
        print(f"Traffic level   : {density['traffic_level']}")
        print("SUMO edges      :", ", ".join(density["mapped_edges"]))
        print("=" * 96)

        publisher.publish(
            "TRAFFIC_OVERVIEW",
            {
                "camera_id": camera_id,
                "image": image.name,
                "image_url": f"/api/images/traffic/{camera_id}",
                "edge_ids": density["mapped_edges"],
                "vehicle_count": inference["non_ambulance_vehicle_count"],
                "cnn_detection_count": inference["vehicle_count"],
                "ambulance_detected": inference["ambulance_detected"],
                "traffic_score": round(density["traffic_score"], 2),
                "traffic_level": density["traffic_level"],
                "source_mode": "live_camera_watch",
                "simulation_time": float(simulation_time),
                "image_version": str(signature[0]),
                "timestamp": utc_now(),
            },
        )

    if not changed_cameras:
        return []

    manager.apply_to_graph(graph)
    if routing_json is not None:
        manager.save_routing_json(routing_json)

    print("\n[LIVE TRAFFIC GRAPH UPDATED]")
    print("Changed cameras :", ", ".join(changed_cameras))
    print("A* route re-evaluation requested.")

    emit_log(
        publisher,
        "Live traffic camera frame changed; CNN traffic state refreshed.",
        changed_cameras=changed_cameras,
        simulation_time=float(simulation_time),
    )

    return changed_cameras'''

content = content.replace(old_apply, new_apply)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Fixed apply_live_camera_changes to skip missing cameras')