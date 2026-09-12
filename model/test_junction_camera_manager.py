from pathlib import Path

from junction_camera_manager import JunctionCameraManager


def main():
    script_dir = Path(__file__).resolve().parent
    manager = JunctionCameraManager(
        script_dir / "junction_camera_config.json",
        detection_ttl_s=8.0,
    )

    manager.describe()

    print("\nTEST 1 - no detection yet")
    print(manager.authorize_preemption("J10", simulation_time=100.0))

    print("\nTEST 2 - low-confidence ambulance")
    manager.report_detection(
        "JCAM_J10",
        detected=True,
        confidence=0.55,
        simulation_time=101.0,
    )
    print(manager.authorize_preemption("J10", simulation_time=102.0))

    print("\nTEST 3 - valid ambulance detection")
    manager.report_detection(
        "JCAM_J10",
        detected=True,
        confidence=0.91,
        simulation_time=103.0,
    )
    print(manager.authorize_preemption("J10", simulation_time=104.0))

    print("\nTEST 4 - stale detection")
    print(manager.authorize_preemption("J10", simulation_time=120.0))

    print("\nTEST 5 - junction with no camera")
    print(manager.authorize_preemption("J03", simulation_time=120.0))


if __name__ == "__main__":
    main()
