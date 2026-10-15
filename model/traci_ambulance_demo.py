r"""
TraCI ambulance demo for the Bengaluru structured SUMO network.

Run from:
    C:\Users\chapp\Desktop\Major Project\AI Traffic Control\model

Commands:
    python traci_ambulance_demo.py
    python traci_ambulance_demo.py --demo-congestion

What it does:
1. Opens SUMO-GUI through TraCI.
2. Uses traffic_routing.py to compute:
      J01 -> J23 -> J47
3. Adds a NEW AI-controlled ambulance to SUMO.
4. Makes SUMO follow the selected edge route.
5. Prints live ambulance edge, speed, position and remaining route.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------
# SUMO / TraCI setup
# ---------------------------------------------------------------------
def load_traci():
    try:
        import traci
        return traci
    except ImportError:
        pass

    # Common Windows SUMO installation paths.
    candidates = [
        Path(r"C:\Program Files (x86)\Eclipse\Sumo\tools"),
        Path(r"C:\Program Files\Eclipse\Sumo\tools"),
    ]

    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidates.insert(0, Path(sumo_home) / "tools")

    for tools_dir in candidates:
        if tools_dir.exists():
            sys.path.append(str(tools_dir))
            try:
                import traci
                return traci
            except ImportError:
                continue

    raise RuntimeError(
        "Could not import TraCI.\n"
        "SUMO is installed, but Python could not find SUMO/tools.\n"
        r"Expected something like: C:\Program Files (x86)\Eclipse\Sumo\tools"
    )


traci = load_traci()

# Import the routing module we already validated.
try:
    from traffic_routing import SumoRoadGraph, demo_congestion
except ImportError as exc:
    raise RuntimeError(
        "Could not import traffic_routing.py.\n"
        "Keep traci_ambulance_demo.py in the SAME model folder as traffic_routing.py."
    ) from exc


AMBULANCE_ID = "AI_AMB_001"
ROUTE_ID = "AI_AMB_ROUTE_001"


def find_sumo_gui() -> str:
    candidates = [
        Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"),
        Path(r"C:\Program Files\Eclipse\Sumo\bin\sumo-gui.exe"),
    ]

    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidates.insert(0, Path(sumo_home) / "bin" / "sumo-gui.exe")

    for p in candidates:
        if p.exists():
            return str(p)

    # Fall back to PATH.
    return "sumo-gui"


def combine_routes(leg1: dict, leg2: dict) -> list[str]:
    """
    Leg 1 ends at pickup junction J23.
    Leg 2 starts at J23.
    Therefore the edge lists can be concatenated directly.
    """
    return list(leg1["edge_path"]) + list(leg2["edge_path"])


def build_route(graph: SumoRoadGraph, use_demo_congestion: bool):
    graph.reset_traffic()

    # Station -> pickup
    leg1 = graph.astar("J01", "J23")

    # Pickup -> hospital
    graph.reset_traffic()
    free_leg2 = graph.astar("J23", "J47")

    if use_demo_congestion:
        scores = demo_congestion(graph, free_leg2)
        graph.set_traffic_scores(scores)
        leg2 = graph.astar("J23", "J47")
    else:
        leg2 = free_leg2

    full_route = combine_routes(leg1, leg2)
    return leg1, leg2, full_route


def print_route(leg1, leg2, full_route, use_demo_congestion):
    print("\n" + "=" * 92)
    print("TRACI AMBULANCE ROUTE")
    print("=" * 92)
    print("Scenario :", "DEMO CONGESTION" if use_demo_congestion else "FREE FLOW")
    print("Leg 1    :", " -> ".join(leg1["junction_path"]))
    print("Leg 2    :", " -> ".join(leg2["junction_path"]))
    print("SUMO route:")
    print(" -> ".join(full_route))
    print(f"Total route edges: {len(full_route)}")
    print("=" * 92)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo-congestion",
        action="store_true",
        help="Force the hospital leg to avoid the congested direct corridor."
    )
    parser.add_argument(
        "--no-gui-delay",
        action="store_true",
        help="Run the TraCI simulation without slowing Python output."
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

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
        raise FileNotFoundError(f"Network not found:\n{net_file}")
    if not cfg_file.exists():
        raise FileNotFoundError(f"SUMO config not found:\n{cfg_file}")

    graph = SumoRoadGraph(net_file)
    leg1, leg2, full_route = build_route(graph, args.demo_congestion)
    print_route(leg1, leg2, full_route, args.demo_congestion)

    sumo_gui = find_sumo_gui()

    sumo_log = script_dir / "sumo_run.log"
    sumo_error_log = script_dir / "sumo_error.log"

    sumo_cmd = [
        sumo_gui,
        "-c", str(cfg_file),
        "--start",
        "--delay", "60",
        "--log", str(sumo_log),
        "--error-log", str(sumo_error_log),
        "--ignore-route-errors",
    ]

    print("\nStarting SUMO-GUI through TraCI...")
    traci.start(sumo_cmd)

    try:
        # Advance once so the simulation is initialized.
        traci.simulationStep()

        # Register the AI route.
        if ROUTE_ID in traci.route.getIDList():
            # Normally impossible in a fresh SUMO session, but safe.
            pass
        else:
            traci.route.add(ROUTE_ID, full_route)

        # Add our own ambulance. The .rou.xml contains AMB_001;
        # we deliberately use AI_AMB_001 to avoid an ID collision.
        traci.vehicle.add(
            vehID=AMBULANCE_ID,
            routeID=ROUTE_ID,
            typeID="ambulance",
            depart="now",
            departLane="best",
            departPos="base",
            departSpeed="max",
        )

        # Make it visually obvious in SUMO-GUI.
        traci.vehicle.setColor(AMBULANCE_ID, (255, 0, 0, 255))

        try:
            traci.gui.trackVehicle("View #0", AMBULANCE_ID)
            traci.gui.setZoom("View #0", 1400)
        except Exception:
            # Tracking/zoom is cosmetic only.
            pass

        print(f"\nAmbulance spawned: {AMBULANCE_ID}")
        print("Watch SUMO-GUI. Live status will appear below.\n")

        step = 0
        last_edge = None
        pickup_announced = False

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1

            vehicle_ids = traci.vehicle.getIDList()

            if AMBULANCE_ID not in vehicle_ids:
                # It may have arrived and been removed from the simulation.
                if step > 3:
                    print("\nAmbulance completed its route / left the simulation.")
                    break
                continue

            edge_id = traci.vehicle.getRoadID(AMBULANCE_ID)
            speed_ms = traci.vehicle.getSpeed(AMBULANCE_ID)
            lane_pos = traci.vehicle.getLanePosition(AMBULANCE_ID)
            route_index = traci.vehicle.getRouteIndex(AMBULANCE_ID)
            route = traci.vehicle.getRoute(AMBULANCE_ID)

            # Print on edge changes rather than every single second.
            if edge_id != last_edge and edge_id and not edge_id.startswith(":"):
                print(
                    f"[t={traci.simulation.getTime():6.1f}s] "
                    f"edge={edge_id:12s} "
                    f"speed={speed_ms * 3.6:5.1f} km/h  "
                    f"route_index={route_index}/{len(route)-1}"
                )
                last_edge = edge_id

            # J23 pickup is reached after traversing J14_J23 in the free-flow leg.
            # We detect pickup by entering the first edge whose from-node is J23.
            if not pickup_announced and route_index >= len(leg1["edge_path"]):
                print("\n>>> EMERGENCY PICKUP REACHED AT J23")
                print(">>> Ambulance continuing toward Main Hospital J47.\n")
                pickup_announced = True

            # Optional slight delay for readable console output.
            if not args.no_gui_delay:
                time.sleep(0.01)

        print("\n" + "=" * 92)
        print("TRACI TEST COMPLETE")
        print("=" * 92)
        print("If you saw the red AI ambulance move through SUMO,")
        print("our routing -> TraCI -> SUMO vehicle-control connection is working.")

    finally:
        try:
            traci.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
