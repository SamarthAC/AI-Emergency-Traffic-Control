from backend_bridge import BackendEventPublisher

publisher = BackendEventPublisher()

events = [
    (
        "TRAFFIC_OVERVIEW",
        {
            "camera_id": "CAM_TEST",
            "edge_ids": ["J23_J24", "J24_J32"],
            "vehicle_count": 17,
            "traffic_score": 38.71,
            "traffic_level": "LOW",
        },
    ),
    (
        "AI_ROUTE",
        {
            "ambulance_id": "AI_AMB_001",
            "station": "J01",
            "pickup": "J23",
            "destination": "J47",
            "route": [
                "J01_J10",
                "J10_J11",
                "J11_J12",
                "J12_J13",
                "J13_J14",
                "J14_J23",
                "J23_J24",
                "J24_J32",
                "J32_J40",
                "J40_J48",
                "J48_J47",
            ],
        },
    ),
    (
        "AMBULANCE_STATUS",
        {
            "id": "AI_AMB_001",
            "status": "DISPATCHED",
            "pickup": "J23",
            "destination": "J47",
        },
    ),
    (
        "VEHICLE_UPDATE",
        {
            "vehicle_id": "AI_AMB_001",
            "edge_id": "J01_J10",
            "route_index": 0,
            "route_length": 11,
            "speed_kmh": 42.4,
            "x": 100.0,
            "y": 200.0,
            "simulation_time": 2.0,
        },
    ),
    (
        "SIGNAL_UPDATE",
        {
            "junction_id": "J10",
            "state": "GREEN_CORRIDOR_ACTIVE",
            "green_corridor_active": True,
            "ambulance_id": "AI_AMB_001",
        },
    ),
    (
        "LOG",
        {
            "level": "INFO",
            "message": "Step 4 backend state-store test.",
        },
    ),
]

passed = 0

for event_type, data in events:
    ok = publisher.publish(event_type, data)
    print(f"{event_type:20s} -> {'PASS' if ok else 'FAIL'}")
    passed += int(ok)

print(f"\nPublished {passed}/{len(events)} test events.")
print("Now open: http://127.0.0.1:8000/api/state")
