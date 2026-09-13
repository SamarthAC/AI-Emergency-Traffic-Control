r"""
Green Corridor demo for the Bengaluru structured SUMO network.

Place this file in:
    AI Traffic Control\model\

Required beside it:
    traffic_routing.py

Run:
    python green_corridor_demo.py

What this script proves:
1. A* computes the ambulance route.
2. TraCI inserts the ambulance into SUMO.
3. The controller detects the next traffic-light junction.
4. It finds the exact incoming -> outgoing ambulance movement.
5. It selects an EXISTING safe SUMO phase that gives that movement green.
6. It holds the green while the ambulance approaches/crosses.
7. It restores the normal traffic-light program after passage.
"""

from __future__ import annotations

import os
import sys
import time
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------
# SUMO / TraCI import
# ---------------------------------------------------------------------
def load_traci():
    try:
        import traci
        return traci
    except ImportError:
        pass

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
        "Could not import TraCI. Check your SUMO tools folder or SUMO_HOME."
    )


traci = load_traci()

try:
    from traffic_routing import SumoRoadGraph
except ImportError as exc:
    raise RuntimeError(
        "Could not import traffic_routing.py. Keep this file in the same model folder."
    ) from exc


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
AMBULANCE_ID = "AI_AMB_001"
ROUTE_ID = "AI_GREEN_CORRIDOR_ROUTE"

# Start preemption this far before the signal.
PREEMPT_DISTANCE_M = 220.0

# Keep selected green alive long enough for the ambulance to pass.
GREEN_HOLD_SECONDS = 30.0

# Rolling route-wide Green Corridor settings.
CORRIDOR_LOOKAHEAD_SIGNALS = 2
CORRIDOR_LOOKAHEAD_DISTANCE_M = 900.0

# Red ambulance in SUMO.
AMBULANCE_COLOR = (255, 0, 0, 255)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def find_sumo_gui() -> str:
    candidates = [
        Path(r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"),
        Path(r"C:\Program Files\Eclipse\Sumo\bin\sumo-gui.exe"),
    ]

    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidates.insert(0, Path(sumo_home) / "bin" / "sumo-gui.exe")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return "sumo-gui"


def parse_edge_nodes(net_file: Path):
    """
    Returns:
        edge_nodes[edge_id] = (from_junction, to_junction)
    """
    root = ET.parse(net_file).getroot()
    edge_nodes = {}

    for edge in root.findall("edge"):
        edge_id = edge.get("id", "")
        if (
            not edge_id
            or edge_id.startswith(":")
            or edge.get("function") == "internal"
        ):
            continue

        from_node = edge.get("from")
        to_node = edge.get("to")

        if from_node and to_node:
            edge_nodes[edge_id] = (from_node, to_node)

    return edge_nodes


def build_full_route(graph):
    leg1 = graph.astar("J01", "J23")
    leg2 = graph.astar("J23", "J47")

    full_edges = list(leg1["edge_path"]) + list(leg2["edge_path"])
    return leg1, leg2, full_edges


def movement_link_indices(tls_id: str, incoming_edge: str, outgoing_edge: str):
    """
    Find SUMO signal link indices controlling the requested movement.

    traci.trafficlight.getControlledLinks(tls_id) returns entries such as:
        (
            (incomingLane, outgoingLane, viaLane),
            ...
        )

    A road may have multiple lanes, so one movement can correspond to
    multiple signal indices.
    """
    controlled = traci.trafficlight.getControlledLinks(tls_id)
    indices = []

    incoming_prefix = incoming_edge + "_"
    outgoing_prefix = outgoing_edge + "_"

    for signal_index, connections in enumerate(controlled):
        if not connections:
            continue

        for connection in connections:
            incoming_lane = connection[0]
            outgoing_lane = connection[1]

            if (
                incoming_lane.startswith(incoming_prefix)
                and outgoing_lane.startswith(outgoing_prefix)
            ):
                indices.append(signal_index)
                break

    return sorted(set(indices))


def choose_green_phase(tls_id: str, required_indices: list[int]):
    """
    Select an EXISTING traffic-light phase in which every signal index
    required by the ambulance movement is green ('G' or 'g').

    We do not create an unsafe all-green state.
    """
    if not required_indices:
        return None

    logics = traci.trafficlight.getAllProgramLogics(tls_id)
    current_program = traci.trafficlight.getProgram(tls_id)

    # Prefer the active program.
    logic = None
    for item in logics:
        if item.programID == current_program:
            logic = item
            break

    if logic is None and logics:
        logic = logics[0]

    if logic is None:
        return None

    candidates = []

    for phase_index, phase in enumerate(logic.phases):
        state = phase.state

        valid = True
        for idx in required_indices:
            if idx >= len(state) or state[idx] not in ("G", "g"):
                valid = False
                break

        if valid:
            # Prefer phases with fewer total greens, since they are usually
            # more movement-specific while remaining part of the legal program.
            green_count = sum(1 for c in state if c in ("G", "g"))
            candidates.append((green_count, phase_index, state))

    if not candidates:
        return None

    candidates.sort()
    _, phase_index, state = candidates[0]
    return phase_index, state



class GreenCorridorController:
    """
    Rolling route-wide Green Corridor controller.

    One valid ambulance detection at any configured junction camera arms the
    corridor. After that, upcoming traffic lights on the already-selected
    ambulance route are preempted automatically in a rolling window.
    """

    def __init__(
        self,
        ambulance_id: str,
        route_edges: list[str],
        edge_nodes: dict,
        publisher=None,
        camera_manager=None,
    ):
        self.ambulance_id = ambulance_id
        self.route_edges = list(route_edges)
        self.edge_nodes = edge_nodes
        self.publisher = publisher
        self.camera_manager = camera_manager

        self.tls_ids = set(traci.trafficlight.getIDList())
        self.active = {}
        self.completed_tls = set()

        self.corridor_armed = False
        self.corridor_trigger = None

        self.route_edge_lengths = {}
        for edge_id in self.route_edges:
            try:
                self.route_edge_lengths[edge_id] = float(
                    traci.lane.getLength(f"{edge_id}_0")
                )
            except Exception:
                self.route_edge_lengths[edge_id] = 0.0

        self.route_signal_plan = []
        for i in range(len(self.route_edges) - 1):
            incoming = self.route_edges[i]
            outgoing = self.route_edges[i + 1]

            edge_data = self.edge_nodes.get(incoming)
            if not edge_data:
                continue

            junction = edge_data[1]
            if junction not in self.tls_ids:
                continue

            indices = movement_link_indices(junction, incoming, outgoing)
            selected = choose_green_phase(junction, indices)

            self.route_signal_plan.append(
                {
                    "junction_id": junction,
                    "incoming_route_index": i,
                    "incoming_edge": incoming,
                    "outgoing_edge": outgoing,
                    "controlled_links": indices,
                    "selected_phase": selected,
                }
            )

        print("\nTraffic lights available in SUMO:", len(self.tls_ids))
        self.print_route_signals()

    def print_route_signals(self):
        print("\nGREEN CORRIDOR SIGNAL PLAN")
        print("-" * 90)

        for item in self.route_signal_plan:
            selected = item["selected_phase"]
            phase_text = (
                "NO GREEN PHASE FOUND"
                if selected is None
                else f"phase {selected[0]}"
            )

            print(
                f"{item['junction_id']:5s}: "
                f"{item['incoming_edge']:12s} -> {item['outgoing_edge']:12s} "
                f"links={item['controlled_links']}  {phase_text}"
            )

        print("-" * 90)
        print(
            f"Traffic-light junctions on ambulance route: "
            f"{len(self.route_signal_plan)}"
        )
        print(
            f"Rolling corridor: next {CORRIDOR_LOOKAHEAD_SIGNALS} route signals, "
            f"max {CORRIDOR_LOOKAHEAD_DISTANCE_M:.0f} m lookahead\n"
        )

    def arm_corridor_from_camera(
        self,
        junction_id: str,
        camera_id: str,
        confidence: float,
        simulation_time: float | None = None,
    ) -> bool:
        if self.corridor_armed:
            return False

        self.corridor_armed = True
        self.corridor_trigger = {
            "junction_id": junction_id,
            "camera_id": camera_id,
            "confidence": float(confidence),
            "simulation_time": (
                float(simulation_time)
                if simulation_time is not None
                else float(traci.simulation.getTime())
            ),
        }

        print(
            "\n[GREEN CORRIDOR ARMED]"
            f"\n  Trigger camera      : {camera_id}"
            f"\n  Detection junction  : {junction_id}"
            f"\n  Confidence          : {float(confidence):.4f}"
            f"\n  Policy              : rolling route-wide preemption"
            f"\n  Lookahead signals   : {CORRIDOR_LOOKAHEAD_SIGNALS}"
            f"\n  Lookahead distance  : {CORRIDOR_LOOKAHEAD_DISTANCE_M:.0f} m\n"
        )

        if self.publisher is not None:
            self.publisher.publish(
                "GREEN_CORRIDOR_STATUS",
                {
                    "armed": True,
                    "ambulance_id": self.ambulance_id,
                    "trigger_camera_id": camera_id,
                    "trigger_junction_id": junction_id,
                    "confidence": round(float(confidence), 4),
                    "lookahead_signals": CORRIDOR_LOOKAHEAD_SIGNALS,
                    "lookahead_distance_m": CORRIDOR_LOOKAHEAD_DISTANCE_M,
                    "simulation_time": traci.simulation.getTime(),
                },
            )

        return True

    def update_route(self, new_route_edges: list[str]) -> None:
        """
        Replace the remaining ambulance route used by the rolling corridor.

        Any currently preempted signal is restored first, because it may belong
        only to the old route. The corridor remains armed and a fresh signal
        plan is then built for the new TraCI route.
        """
        self.restore_all()
        self.route_edges = list(new_route_edges)
        self.completed_tls.clear()

        self.route_edge_lengths = {}
        for edge_id in self.route_edges:
            try:
                self.route_edge_lengths[edge_id] = float(
                    traci.lane.getLength(f"{edge_id}_0")
                )
            except Exception:
                self.route_edge_lengths[edge_id] = 0.0

        self.route_signal_plan = []
        for i in range(len(self.route_edges) - 1):
            incoming = self.route_edges[i]
            outgoing = self.route_edges[i + 1]

            edge_data = self.edge_nodes.get(incoming)
            if not edge_data:
                continue

            junction = edge_data[1]
            if junction not in self.tls_ids:
                continue

            indices = movement_link_indices(junction, incoming, outgoing)
            selected = choose_green_phase(junction, indices)

            self.route_signal_plan.append(
                {
                    "junction_id": junction,
                    "incoming_route_index": i,
                    "incoming_edge": incoming,
                    "outgoing_edge": outgoing,
                    "controlled_links": indices,
                    "selected_phase": selected,
                }
            )

        print("\n[GREEN CORRIDOR ROUTE UPDATED]")
        print("  New edges :", " -> ".join(self.route_edges))
        print(
            f"  Route TLS : "
            f"{', '.join(item['junction_id'] for item in self.route_signal_plan) or 'none'}"
        )

        if self.publisher is not None:
            self.publisher.publish(
                "GREEN_CORRIDOR_STATUS",
                {
                    "armed": self.corridor_armed,
                    "ambulance_id": self.ambulance_id,
                    "route_updated": True,
                    "route": self.route_edges,
                    "simulation_time": traci.simulation.getTime(),
                },
            )

    def get_upcoming_tls_approach(self):
        if self.ambulance_id not in traci.vehicle.getIDList():
            return None

        route_index = traci.vehicle.getRouteIndex(self.ambulance_id)
        if route_index < 0 or route_index >= len(self.route_edges) - 1:
            return None

        current_road = traci.vehicle.getRoadID(self.ambulance_id)
        if not current_road or current_road.startswith(":"):
            return None

        incoming_edge = self.route_edges[route_index]
        outgoing_edge = self.route_edges[route_index + 1]

        if current_road != incoming_edge:
            return None

        edge_data = self.edge_nodes.get(incoming_edge)
        if not edge_data:
            return None

        junction = edge_data[1]
        if junction not in self.tls_ids:
            return None

        distance = self._distance_to_end_of_current_edge()
        if distance is None:
            return None

        return {
            "junction_id": junction,
            "incoming_edge": incoming_edge,
            "outgoing_edge": outgoing_edge,
            "route_index": route_index,
            "distance_to_signal_m": float(distance),
        }

    def _distance_to_end_of_current_edge(self):
        road_id = traci.vehicle.getRoadID(self.ambulance_id)
        if not road_id or road_id.startswith(":"):
            return None

        lane_id = traci.vehicle.getLaneID(self.ambulance_id)
        lane_position = traci.vehicle.getLanePosition(self.ambulance_id)

        try:
            lane_length = traci.lane.getLength(lane_id)
        except Exception:
            return None

        return max(0.0, lane_length - lane_position)

    def _distance_to_route_index(self, current_index: int, target_index: int):
        if target_index < current_index:
            return 0.0

        remaining = self._distance_to_end_of_current_edge()
        distance = float(remaining) if remaining is not None else 0.0

        if target_index == current_index:
            return distance

        for idx in range(current_index + 1, target_index + 1):
            edge_id = self.route_edges[idx]
            distance += self.route_edge_lengths.get(edge_id, 0.0)

        return distance

    def _activate_signal(self, plan_item: dict, distance_to_signal: float):
        junction = plan_item["junction_id"]

        if junction in self.active or junction in self.completed_tls:
            return False

        selected = plan_item["selected_phase"]
        if selected is None:
            print(
                f"[WARN] {junction}: no legal green phase for "
                f"{plan_item['incoming_edge']} -> {plan_item['outgoing_edge']}."
            )
            self.completed_tls.add(junction)
            return False

        green_phase, phase_state = selected

        current_program = traci.trafficlight.getProgram(junction)
        current_phase = traci.trafficlight.getPhase(junction)

        try:
            next_switch = traci.trafficlight.getNextSwitch(junction)
            now = traci.simulation.getTime()
            remaining = max(1.0, next_switch - now)
        except Exception:
            remaining = 5.0

        self.active[junction] = {
            "program": current_program,
            "phase": current_phase,
            "remaining_duration": remaining,
            "incoming_route_index": plan_item["incoming_route_index"],
            "incoming_edge": plan_item["incoming_edge"],
            "outgoing_edge": plan_item["outgoing_edge"],
        }

        traci.trafficlight.setPhase(junction, green_phase)
        traci.trafficlight.setPhaseDuration(junction, GREEN_HOLD_SECONDS)

        print(
            f"\n[GREEN CORRIDOR ON]  TLS={junction}"
            f"\n  Ambulance movement : "
            f"{plan_item['incoming_edge']} -> {plan_item['outgoing_edge']}"
            f"\n  Route lookahead    : {distance_to_signal:.1f} m"
            f"\n  Controlled links   : {plan_item['controlled_links']}"
            f"\n  Selected phase     : {green_phase}"
            f"\n  Phase state        : {phase_state}"
            f"\n  Hold               : {GREEN_HOLD_SECONDS:.0f} s\n"
        )

        if self.publisher is not None:
            self.publisher.publish(
                "SIGNAL_UPDATE",
                {
                    "junction_id": junction,
                    "state": "GREEN_CORRIDOR_ACTIVE",
                    "green_corridor_active": True,
                    "corridor_armed": self.corridor_armed,
                    "ambulance_id": self.ambulance_id,
                    "incoming_edge": plan_item["incoming_edge"],
                    "outgoing_edge": plan_item["outgoing_edge"],
                    "distance_to_signal_m": round(distance_to_signal, 2),
                    "controlled_links": plan_item["controlled_links"],
                    "selected_phase": green_phase,
                    "phase_state": phase_state,
                    "hold_seconds": GREEN_HOLD_SECONDS,
                    "simulation_time": traci.simulation.getTime(),
                },
            )

        return True

    def _restore(self, tls_id: str):
        saved = self.active.pop(tls_id, None)
        if not saved:
            return

        try:
            traci.trafficlight.setProgram(tls_id, saved["program"])
            traci.trafficlight.setPhase(tls_id, saved["phase"])
            traci.trafficlight.setPhaseDuration(
                tls_id,
                max(1.0, saved["remaining_duration"]),
            )

            print(
                f"[GREEN CORRIDOR OFF] {tls_id} restored "
                f"to program={saved['program']} phase={saved['phase']}"
            )

            if self.publisher is not None:
                self.publisher.publish(
                    "SIGNAL_UPDATE",
                    {
                        "junction_id": tls_id,
                        "state": "NORMAL",
                        "green_corridor_active": False,
                        "corridor_armed": self.corridor_armed,
                        "ambulance_id": self.ambulance_id,
                        "restored_program": saved["program"],
                        "restored_phase": saved["phase"],
                        "incoming_edge": saved["incoming_edge"],
                        "outgoing_edge": saved["outgoing_edge"],
                        "simulation_time": traci.simulation.getTime(),
                    },
                )
        except Exception as exc:
            print(f"[WARN] Could not restore TLS {tls_id}: {exc}")

        self.completed_tls.add(tls_id)

    def restore_all(self):
        for tls_id in list(self.active.keys()):
            self._restore(tls_id)

    def update(self):
        if self.ambulance_id not in traci.vehicle.getIDList():
            self.restore_all()
            return

        route_index = traci.vehicle.getRouteIndex(self.ambulance_id)
        if route_index < 0 or route_index >= len(self.route_edges):
            return

        for tls_id, saved in list(self.active.items()):
            if route_index > saved["incoming_route_index"]:
                self._restore(tls_id)

        if not self.corridor_armed:
            return

        # IMPORTANT:
        # setPhaseDuration() only controls the current SUMO phase timer.
        # If a route signal was activated far ahead, that timer could expire
        # before the ambulance arrived, causing the light to resume its normal
        # cycle and potentially turn red. Refresh the selected ambulance phase
        # on every simulation step until the ambulance has passed it.
        for tls_id, saved in list(self.active.items()):
            plan_item = next(
                (
                    item
                    for item in self.route_signal_plan
                    if item["junction_id"] == tls_id
                ),
                None,
            )
            if plan_item is None:
                continue

            selected = plan_item["selected_phase"]
            if selected is None:
                continue

            green_phase, _ = selected

            try:
                if traci.trafficlight.getPhase(tls_id) != green_phase:
                    traci.trafficlight.setPhase(tls_id, green_phase)

                traci.trafficlight.setPhaseDuration(
                    tls_id,
                    GREEN_HOLD_SECONDS,
                )
            except Exception as exc:
                print(
                    f"[WARN] Could not maintain Green Corridor at "
                    f"{tls_id}: {exc}"
                )

        upcoming = []

        for item in self.route_signal_plan:
            idx = item["incoming_route_index"]

            if idx < route_index:
                continue

            junction = item["junction_id"]
            if junction in self.completed_tls:
                continue

            distance = self._distance_to_route_index(route_index, idx)

            if idx != route_index and distance > CORRIDOR_LOOKAHEAD_DISTANCE_M:
                continue

            upcoming.append((idx, distance, item))

        upcoming.sort(key=lambda item: (item[0], item[1]))
        allowed = upcoming[:CORRIDOR_LOOKAHEAD_SIGNALS]
        allowed_ids = {item["junction_id"] for _, _, item in allowed}

        for tls_id in list(self.active.keys()):
            saved = self.active[tls_id]
            if (
                saved["incoming_route_index"] >= route_index
                and tls_id not in allowed_ids
            ):
                self._restore(tls_id)

        for _, distance, item in allowed:
            self._activate_signal(item, distance)


def main():
    global PREEMPT_DISTANCE_M, GREEN_HOLD_SECONDS

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold",
        type=float,
        default=PREEMPT_DISTANCE_M,
        help="Preemption distance before signal in metres."
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=GREEN_HOLD_SECONDS,
        help="How long to hold the ambulance green phase."
    )
    args = parser.parse_args()

    PREEMPT_DISTANCE_M = max(20.0, args.threshold)
    GREEN_HOLD_SECONDS = max(5.0, args.hold)

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
    leg1, leg2, full_route = build_full_route(graph)
    edge_nodes = parse_edge_nodes(net_file)

    print("\n" + "=" * 92)
    print("AI GREEN CORRIDOR DEMO")
    print("=" * 92)
    print("Station  : J01")
    print("Pickup   : J23")
    print("Hospital : J47")
    print("Leg 1    :", " -> ".join(leg1["junction_path"]))
    print("Leg 2    :", " -> ".join(leg2["junction_path"]))
    print("Edges    :", " -> ".join(full_route))
    print(f"Trigger  : {PREEMPT_DISTANCE_M:.0f} m before TLS")
    print(f"Hold     : {GREEN_HOLD_SECONDS:.0f} s")
    print("=" * 92)

    sumo_gui = find_sumo_gui()

    sumo_log = script_dir / "sumo_green_corridor.log"
    sumo_error_log = script_dir / "sumo_green_corridor_error.log"

    sumo_cmd = [
        sumo_gui,
        "-c", str(cfg_file),
        "--start",
        "--delay", "60",
        "--log", str(sumo_log),
        "--error-log", str(sumo_error_log),

        # Temporary because the existing background auto_west flow contains
        # an invalid route. Remove this after fixing the .rou.xml flow.
        "--ignore-route-errors",
    ]

    print("\nStarting SUMO-GUI...")
    traci.start(sumo_cmd)

    controller = None

    try:
        traci.simulationStep()

        if ROUTE_ID not in traci.route.getIDList():
            traci.route.add(ROUTE_ID, full_route)

        traci.vehicle.add(
            vehID=AMBULANCE_ID,
            routeID=ROUTE_ID,
            typeID="ambulance",
            depart="now",
            departLane="best",
            departPos="base",
            departSpeed="max",
        )

        traci.vehicle.setColor(AMBULANCE_ID, AMBULANCE_COLOR)

        try:
            traci.gui.trackVehicle("View #0", AMBULANCE_ID)
            traci.gui.setZoom("View #0", 1400)
        except Exception:
            pass

        controller = GreenCorridorController(
            AMBULANCE_ID,
            full_route,
            edge_nodes
        )

        print(f"Ambulance spawned: {AMBULANCE_ID}")
        print("Green Corridor controller ACTIVE.\n")

        last_edge = None
        pickup_announced = False
        step = 0

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1

            vehicle_ids = traci.vehicle.getIDList()

            if AMBULANCE_ID not in vehicle_ids:
                if step > 3:
                    if controller:
                        controller.restore_all()

                    print("\nAmbulance reached destination / left simulation.")
                    break
                continue

            controller.update()

            road_id = traci.vehicle.getRoadID(AMBULANCE_ID)
            route_index = traci.vehicle.getRouteIndex(AMBULANCE_ID)
            speed = traci.vehicle.getSpeed(AMBULANCE_ID) * 3.6

            if (
                road_id
                and not road_id.startswith(":")
                and road_id != last_edge
            ):
                print(
                    f"[t={traci.simulation.getTime():6.1f}s] "
                    f"edge={road_id:12s} "
                    f"speed={speed:5.1f} km/h "
                    f"route_index={route_index}/{len(full_route)-1}"
                )
                last_edge = road_id

            if (
                not pickup_announced
                and route_index >= len(leg1["edge_path"])
            ):
                print("\n>>> PICKUP J23 REACHED")
                print(">>> Continuing to Main Hospital J47.\n")
                pickup_announced = True

            time.sleep(0.01)

        print("\n" + "=" * 92)
        print("GREEN CORRIDOR TEST COMPLETE")
        print("=" * 92)
        print("Check the console above for:")
        print("  [GREEN CORRIDOR ON]")
        print("  [GREEN CORRIDOR OFF]")
        print("If these appear and the ambulance reaches J47, signal preemption is working.")

    finally:
        if controller is not None:
            try:
                controller.restore_all()
            except Exception:
                pass

        try:
            traci.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
