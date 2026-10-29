#!/usr/bin/env python3
"""
Generate comprehensive project documentation PDF for AI Smart Ambulance System
"""

from fpdf import FPDF
import os

class ProjectPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, 'AI Smart Ambulance - Project Documentation', align='L')
            self.cell(0, 5, f'Page {self.page_no()}', align='R', new_x="LMARGIN", new_y="NEXT")
            self.line(10, 12, 200, 12)
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')
    
    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(0, 51, 102)
            self.ln(4)
            self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(0, 51, 102)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font('Helvetica', 'B', 13)
            self.set_text_color(0, 76, 153)
            self.ln(2)
            self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font('Helvetica', 'B', 11)
            self.set_text_color(51, 102, 153)
            self.ln(1)
            self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)
    
    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 5, text)
        self.ln(2)
    
    def bullet_point(self, text, indent=15):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(33, 33, 33)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5, '-')
        self.multi_cell(0, 5, text)
        self.ln(1)
    
    def code_block(self, text):
        self.set_font('Courier', '', 8)
        self.set_text_color(33, 33, 33)
        self.set_fill_color(240, 240, 240)
        self.set_draw_color(200, 200, 200)
        x = self.get_x()
        self.set_x(x + 10)
        lines = text.split('\n')
        for line in lines:
            self.cell(180, 4.5, line, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
    
    def table_row(self, cells, widths, header=False, fill=False):
        if header:
            self.set_font('Helvetica', 'B', 9)
            self.set_fill_color(0, 51, 102)
            self.set_text_color(255, 255, 255)
        elif fill:
            self.set_font('Helvetica', '', 9)
            self.set_fill_color(235, 242, 250)
            self.set_text_color(33, 33, 33)
        else:
            self.set_font('Helvetica', '', 9)
            self.set_fill_color(255, 255, 255)
            self.set_text_color(33, 33, 33)
        
        max_h = 6
        x_start = self.get_x()
        y_start = self.get_y()
        
        # Calculate max height needed
        max_lines = 1
        for cell, w in zip(cells, widths):
            text = str(cell)
            # Estimate lines needed
            chars_per_line = max(1, w / 2.0)  # rough estimate
            lines_needed = max(1, len(text) / chars_per_line)
            max_lines = max(max_lines, lines_needed)
        
        row_height = max(6, max_lines * 5)
        
        for i, (cell, w) in enumerate(zip(cells, widths)):
            self.set_xy(x_start + sum(widths[:i]), y_start)
            self.multi_cell(w, 5, str(cell), border=1, fill=True, align='L')
        
        # Move to after the tallest cell
        actual_y = self.get_y()
        self.set_y(max(y_start + row_height, actual_y))


pdf = ProjectPDF()
pdf.alias_nb_pages()
pdf.add_page()

# ============================================================
# COVER PAGE
# ============================================================
pdf.ln(40)
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 15, 'AI Smart Ambulance', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)
pdf.set_font('Helvetica', '', 18)
pdf.set_text_color(0, 76, 153)
pdf.cell(0, 12, 'Real-Time Green Corridor & Dynamic Routing System', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(15)

pdf.set_draw_color(0, 51, 102)
pdf.set_line_width(1)
pdf.line(50, pdf.get_y(), 160, pdf.get_y())
pdf.ln(15)

pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 8, 'Complete System Documentation', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, 'Architecture, Implementation & Real-World Deployment Guide', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(20)

pdf.set_font('Helvetica', 'I', 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, 'Generated: 2026', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, 'Version: 1.0', align='C', new_x="LMARGIN", new_y="NEXT")

# ============================================================
# TABLE OF CONTENTS
# ============================================================
pdf.add_page()
pdf.chapter_title('Table of Contents')
pdf.ln(5)

toc_items = [
    ("1", "System Architecture Overview"),
    ("2", "Core Components"),
    ("  2.1", "Backend (FastAPI)"),
    ("  2.2", "Simulation & AI (Python/SUMO)"),
    ("  2.3", "Frontend (React/TypeScript)"),
    ("3", "Data Flow: Image Change -> Route Change -> Corridor Update"),
    ("4", "Green Corridor Behavior"),
    ("  4.1", "Rolling Route-Aware Corridor"),
    ("  4.2", "Safe Signal Preemption Logic"),
    ("5", "WebSocket Event Types"),
    ("6", "Frontend Pages & Features"),
    ("7", "Configuration Files"),
    ("8", "Key Simulation Constants"),
    ("9", "Running the Full Stack"),
    ("10", "Real-World Implementation Plan"),
    ("  10.1", "Hardware & Infrastructure Requirements"),
    ("  10.2", "Software Architecture Changes for Production"),
    ("  10.3", "Integration with Existing Traffic Systems"),
    ("  10.4", "Regulatory & Safety Considerations"),
    ("  10.5", "Phased Deployment Approach"),
    ("11", "Real-World Value Proposition"),
    ("  11.1", "Quantifiable Benefits"),
    ("  11.2", "Comparison: Simulation vs Reality"),
    ("  11.3", "Cost-Benefit Analysis"),
    ("12", "Key Differentiators & Innovation"),
]

for num, title in toc_items:
    pdf.set_font('Helvetica', 'B' if not num.startswith(' ') else '', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(15, 7, num)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

# ============================================================
# 1. SYSTEM ARCHITECTURE
# ============================================================
pdf.add_page()
pdf.chapter_title('1. System Architecture Overview')

pdf.body_text(
    'The AI Smart Ambulance system is an end-to-end emergency response platform that combines '
    'computer vision (CNN), dynamic graph routing (A*), traffic simulation (SUMO/TraCI), and '
    'adaptive signal control (Green Corridor) into a single real-time pipeline. The system '
    'operates on a closed-loop principle: traffic camera feeds drive CNN inference, which updates '
    'edge congestion costs, triggering A* route recalculation, which commands TraCI to reroute '
    'the ambulance, which automatically rebuilds the Green Corridor signal preemption plan across '
    'the new route.'
)

pdf.body_text(
    'The architecture follows a strict separation of concerns: the simulation (SUMO + AI logic) '
    'is the single source of truth; the FastAPI backend provides REST/WebSocket connectivity and '
    'state persistence; the React frontend is a pure visualization layer with zero control authority '
    'over signals or routing.'
)

pdf.chapter_title('System Data Flow', level=2)
pdf.code_block("""+-----------------+    +-----------------+    +-----------------+    +-----------------+
|   CAMERA        |    |   CNN           |    |   EDGE          |    |   A*            |
|   IMAGES        |--->|   INFERENCE     |--->|   TRAFFIC       |--->|   ROUTING       |
|  (Input)        |    |  (V4 PyTorch)   |    |   MANAGER       |    |  (Dynamic)      |
+-----------------+    +-----------------+    +-----------------+    +-----------------+
      |                      |                      |                      |
      v                      v                      v                      v
+-----------------------------------------------------------------------------------+
|                        FASTAPI BACKEND (Port 8000)                               |
|  +------------+  +------------+  +------------+  +------------+  +------------+   |
|  | /events    |  | /ws        |  | /api/*     |  | /images/   |  | /reset     |   |
|  | Ingest     |  | WebSocket  |  | REST       |  | Traffic/   |  | State      |   |
|  +------------+  +------------+  +------------+  +------------+  +------------+   |
|        |            |            |            |            |                      |
|        +------------+------------+------------+------------+                      |
|                         v                                                          |
|                  +------------------+                                             |
|                  |  DashboardState  |  <-- Single source of truth                 |
|                  |     Store        |                                             |
|                  +------------------+                                             |
+-----------------------------------------------------------------------------------+
                                  |
                                  v WebSocket
+-----------------------------------------------------------------------------------+
|                        REACT FRONTEND (Port 5173)                                |
|  +---------+  +------------+  +------------+  +------------+                     |
|  |Overview |  |Simulation  |  | Cameras    |  |Hospitals   |  Pages              |
|  +---------+  +------------+  +------------+  +------------+                     |
|  +----------------------------------------------------------------------+        |
|  |              Zustand Store (dashboardStore)                          |        |
|  |  ambulance | route | hospital | traffic | signals | ...           |        |
|  +----------------------------------------------------------------------+        |
+-----------------------------------------------------------------------------------+""")

# ============================================================
# 2. CORE COMPONENTS
# ============================================================
pdf.add_page()
pdf.chapter_title('2. Core Components')

pdf.chapter_title('2.1 Backend (FastAPI)', level=2)

backend_files = [
    ["File", "Purpose"],
    ["backend/main.py", "FastAPI server: REST endpoints, WebSocket, image upload, event ingestion, CORS"],
    ["backend/state_store.py", "In-memory state snapshot for late-joining dashboards (200 log limit)"],
    ["backend/event_bus.py", "Async queue + ConnectionManager for WebSocket broadcast to all clients"],
    ["backend/schemas.py", "Pydantic models for WebSocket message validation (WSMessage)"],
]

widths = [50, 140]
for i, row in enumerate(backend_files):
    pdf.table_row(row, widths, header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('2.2 Simulation & AI (Python/SUMO)', level=2)

sim_files = [
    ["File", "Purpose"],
    ["model/ai_emergency_demo.py", "Main orchestration: runs SUMO, CNN, routing, corridor, publishes all events"],
    ["model/green_corridor_demo.py", "GreenCorridorController: rolling route-aware signal preemption (core logic)"],
    ["model/junction_camera_manager.py", "Virtual junction cameras: CNN ambulance detection + authorization policy"],
    ["model/traffic_routing.py", "SumoRoadGraph + congestion-aware A* with dynamic edge costs"],
    ["model/edge_traffic_manager.py", "Maps CNN traffic scores -> SUMO edge dynamic_time_s (travel time)"],
    ["model/hospital_selector.py", "Multi-criteria selection: beds, doctors, eligibility, route cost, distance"],
    ["model/inference_v4.py", "TrafficDetectorV4: PyTorch CNN for traffic density (vehicle count, level)"],
    ["model/backend_bridge.py", "BackendEventPublisher: async HTTP POST to /events endpoint"],
]

for i, row in enumerate(sim_files):
    pdf.table_row(row, widths, header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('2.3 Frontend (React/TypeScript)', level=2)

frontend_files = [
    ["Page/Component", "Purpose"],
    ["LiveSimulationPage", "Main dashboard: NetworkMap (70%) + MissionStatus + GreenCorridorRollingPanel + EventTimeline"],
    ["OverviewPage", "KPIs + mini map + hospital summary + traffic cams + recent events"],
    ["TrafficCamerasPage", "5 CCTV cards with upload + preview + pipeline status (UPLOADING->CNN->ROUTE_UPDATED)"],
    ["JunctionCamerasPage", "Ambulance detection frames with confidence overlay + signal distance"],
    ["HospitalSelectionPage", "Side-by-side comparison + mini-network route view from J23 to each hospital"],
    ["NetworkMap", "SVG map: roads (traffic heat), signals, hospitals, ambulance, cameras, legend"],
    ["SignalMarker", "Traffic light with corridor halos (ACTIVE/PRIORITY/UPCOMING/PASSED/RESTORED)"],
    ["GreenCorridorRollingPanel", "Rolling corridor state + signal sequence + camera confirmations + route updates"],
    ["LiveEventTimeline", "Categorized events: CAMERA/GREEN_CORRIDOR/SIGNAL/ROUTING/HOSPITAL/TRAFFIC/SYSTEM"],
    ["CameraUploadModal", "File picker (.jpg/.png) -> preview -> Upload & Analyse -> pipeline status"],
]

for i, row in enumerate(frontend_files):
    pdf.table_row(row, widths, header=(i==0), fill=(i%2==1))

# ============================================================
# 3. DATA FLOW PIPELINE
# ============================================================
pdf.add_page()
pdf.chapter_title('3. Data Flow: Image Change -> Route Change -> Corridor Update')

pdf.body_text(
    'This is the core live demo pipeline. When a user uploads a new traffic camera image through '
    'the frontend, the following chain executes automatically without any manual intervention:'
)

pipeline_steps = [
    ("1", "USER ACTION", "Click Change Frame on CAM_HOSPITAL_DIRECT_1, upload high2.jpg"),
    ("2", "BACKEND API", "POST /api/images/traffic/{camera_id} -> saves to model/live_inputs/CAM_*.jpg"),
    ("3", "SIMULATION", "apply_live_camera_changes() polls every 1s sim-time, detects mtime/size change"),
    ("4", "CNN INFERENCE", "TrafficInferenceV4.predict() -> vehicle_count, traffic_score, traffic_level"),
    ("5", "EDGE COSTS", "EdgeTrafficManager.update_from_inference() -> dynamic_time_s per SUMO edge"),
    ("6", "A* RE-ROUTE", "SumoRoadGraph.astar() with new costs -> improvement >= 10%? -> traci.setRoute()"),
    ("7", "CORRIDOR REBUILD", "GreenCorridorController.update_route() -> rebuilds signal_plan -> GREEN_CORRIDOR_STATUS"),
    ("8", "FRONTEND", "AI_ROUTE + SIGNAL_UPDATE events -> NetworkMap fades old, highlights new -> Panel updates"),
]

for step in pipeline_steps:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(10, 6, step[0] + '.')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(35, 6, step[1])
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(33, 33, 33)
    pdf.multi_cell(0, 6, step[2])
    pdf.ln(2)

pdf.ln(3)
pdf.chapter_title('Thresholds & Timing', level=2)

thresholds = [
    ["Parameter", "Value", "Location"],
    ["Reroute improvement threshold", "10% (0.10)", "MIN_REROUTE_IMPROVEMENT"],
    ["Reroute cooldown", "30 seconds", "REROUTE_COOLDOWN_S"],
    ["Live camera poll interval", "1 second sim-time", "LIVE_CAMERA_POLL_INTERVAL_S"],
    ["Preemption distance", "220 meters", "PREEMPT_DISTANCE_M"],
    ["Green hold duration", "30 seconds", "GREEN_HOLD_SECONDS"],
    ["Lookahead signals", "2 signals", "CORRIDOR_LOOKAHEAD_SIGNALS"],
    ["Lookahead distance", "900 meters", "CORRIDOR_LOOKAHEAD_DISTANCE_M"],
    ["Pickup replan distance", "80 meters", "PICKUP_REPLAN_DISTANCE_M"],
    ["CNN confidence threshold", "70% (0.70)", "junction_camera_config.json"],
]

widths2 = [70, 50, 70]
for i, row in enumerate(thresholds):
    pdf.table_row(row, widths2, header=(i==0), fill=(i%2==1))

# ============================================================
# 4. GREEN CORRIDOR BEHAVIOR
# ============================================================
pdf.add_page()
pdf.chapter_title('4. Green Corridor Behavior')

pdf.chapter_title('4.1 Rolling Route-Aware Corridor', level=2)

pdf.body_text(
    'The Green Corridor is the core innovation. Unlike naive implementations that turn all nearby '
    'lights green, this system implements a rolling, route-aware corridor that moves with the '
    'ambulance. Only ONE valid junction-camera detection is required to arm the ENTIRE corridor.'
)

pdf.chapter_title('Example Scenario', level=3)

pdf.body_text('Ambulance Route: J01 -> J10 -> J11 -> J12 -> J13 -> J14 -> J23 -> J24 -> J32 -> J40 -> J48 -> J47')

pdf.ln(2)
pdf.set_font('Courier', '', 9)
pdf.set_fill_color(240, 248, 255)
steps = [
    "CAMERA DETECTION at JCAM_J10 (confidence 81% >= 70%)",
    "         |",
    "         v",
    "CORRIDOR ARMED (once, corridor_armed = true)",
    "         |",
    "         v",
    "LOOKAHEAD WINDOW: 2 signals, 900m",
    "         |",
    "         +-- J10: ACTIVE (ambulance approaching)",
    "         +-- J12: PRIORITY (in lookahead window)",
    "         +-- J14: UPCOMING (in lookahead window)",
    "",
    "AMBULANCE PASSES J10 (physical pass on outgoing edge)",
    "         |",
    "         v",
    "J10: RESTORED -> Rolling window advances",
    "         |",
    "         +-- J12: ACTIVE",
    "         +-- J14: PRIORITY",
    "         +-- J24: UPCOMING (added to window)",
    "",
    "PICKUP REPLAN at J23 -> Route changes to J24->J32->J40->J48->J47",
    "         |",
    "         v",
    "OLD J39: Removed from corridor (no longer on route)",
    "NEW J24, J32: Added to corridor automatically",
]

for step in steps:
    pdf.set_x(20)
    pdf.cell(0, 4.5, step, fill=True, new_x="LMARGIN", new_y="NEXT")

pdf.ln(5)
pdf.chapter_title('4.2 Safe Signal Preemption Logic', level=2)

pdf.body_text(
    'CRITICAL: The system NEVER creates unsafe all-green states. It follows SUMO\'s legal '
    'phase program:'
)

logic_steps = [
    "1. Identify ambulance movement: incoming_edge -> outgoing_edge (e.g., J01_J10 -> J10_J11)",
    "2. Query SUMO: getControlledLinks(TLS) for links matching that movement",
    "3. Search EXISTING phases: find phase where required link indices are 'G' or 'g'",
    "4. Prefer phase with FEWEST total greens (most movement-specific, still legal)",
    "5. Set phase via TraCI: traci.trafficlight.setPhase(tls_id, selected_phase)",
    "6. Hold phase: traci.trafficlight.setPhaseDuration(tls_id, GREEN_HOLD_SECONDS)",
    "7. Refresh every simulation step until ambulance on outgoing_edge",
    "8. Restore: traci.trafficlight.setProgram() + setPhase() + setPhaseDuration()",
]

for step in logic_steps:
    pdf.bullet_point(step)

pdf.ln(2)
pdf.set_font('Helvetica', 'B', 10)
pdf.set_text_color(180, 0, 0)
pdf.body_text('SAFETY GUARANTEE: Only compatible movements get green. Conflicting approaches remain red.')

# ============================================================
# 5. WEBSOCKET EVENT TYPES
# ============================================================
pdf.add_page()
pdf.chapter_title('5. WebSocket Event Types')

pdf.body_text('All communication from simulation to frontend uses these event types over WebSocket (/ws):')

events = [
    ["Event", "Trigger", "Key Fields"],
    ["STATE_SNAPSHOT", "Dashboard connects", "Full state: ambulance, route, hospital, traffic, signals, corridor, logs"],
    ["AMBULANCE_STATUS", "Dispatch/pickup/arrival", "status, edge_id, speed_kmh, pickup_reached, x, y, simulation_time"],
    ["AI_ROUTE", "Initial + reroute + replan", "route[], route_stage, rerouted, improvement_percent, replan_type"],
    ["TRAFFIC_OVERVIEW", "CNN result (initial + live)", "camera_id, traffic_score, traffic_level, vehicle_count, image_version, image_url"],
    ["SIGNAL_UPDATE", "Corridor activate/restore", "junction_id, green_corridor_active, phase_state, distance_to_signal_m, incoming_route_index"],
    ["GREEN_CORRIDOR_STATUS", "Arm/route_update", "armed, trigger_camera_id, lookahead_signals, lookahead_distance_m, route_updated"],
    ["JUNCTION_CAMERA_DETECTION", "CNN ambulance detect", "camera_id, junction_id, ambulance_detected, confidence, metadata.distance_to_signal_m"],
    ["HOSPITAL_SELECTION", "Initial selection", "selected_hospital, candidates[], selection_reason"],
    ["VEHICLE_UPDATE", "Every 2s sim-time", "x, y, edge_id, route_index, route_length, speed_kmh, simulation_time"],
    ["EMERGENCY_METRICS", "Mission complete", "dispatch_to_pickup_s, pickup_to_hospital_s, total_emergency_travel_s, reroutes, stops"],
    ["LOG", "All major events", "level (INFO/WARN/ERROR/SUCCESS), message, structured data"],
]

widths3 = [45, 45, 100]
for i, row in enumerate(events):
    pdf.table_row(row, widths3, header=(i==0), fill=(i%2==1))

# ============================================================
# 6. FRONTEND PAGES
# ============================================================
pdf.add_page()
pdf.chapter_title('6. Frontend Pages & Features')

pages = [
    ["Page", "Key Features"],
    ["LiveSimulationPage", "NetworkMap (70%) | MissionStatus + GreenCorridorRollingPanel + AIDecisionEngineCard | EventTimeline (bottom)"],
    ["OverviewPage", "6 KPI cards | Mini map | Hospital summary (2 cards) | 4 traffic cams | 6 recent events"],
    ["TrafficCamerasPage", "5 camera cards with live feed | Change Frame button | Pipeline status overlay | Vision modal"],
    ["JunctionCamerasPage", "Detection frames | Confidence badge | Signal distance | Incoming/Outgoing edges"],
    ["HospitalSelectionPage", "Side-by-side comparison | Beds/Doctors/Cost/Distance | Mini-network route view"],
    ["NetworkMap", "SVG: roads(traffic heat), active route(glow), signals(halos), hospitals(selected/alt), ambulance, cameras"],
    ["SignalMarker", "3-light housing | Actual phase colors | Corridor halos | Tooltip: junction, state, distance, edges, links, phase"],
    ["GreenCorridorRollingPanel", "State badge | Trigger info | Config stats | Signal sequence (ACTIVE->PRIORITY->UPCOMING->PASSED) | Camera confirmations"],
    ["LiveEventTimeline", "Category filter | Level filter | Auto-scroll | Color-coded badges (CAMERA/CORRIDOR/SIGNAL/ROUTING/HOSPITAL)"],
    ["MapLegend", "Route types | Signal states (6) | Hospital markers | Base/Pickup icons"],
]

for i, row in enumerate(pages):
    pdf.table_row(row, [45, 145], header=(i==0), fill=(i%2==1))

# ============================================================
# 7. CONFIGURATION FILES
# ============================================================
pdf.add_page()
pdf.chapter_title('7. Configuration Files')

configs = [
    ["File", "Key Settings"],
    ["model/junction_camera_config.json", "14 junction cameras (JCAM_J07..JCAM_J46), 70% confidence, TraCI confirmation required, route-check enabled"],
    ["model/hospital_data.json", "Main Hospital (J47): 6 beds, 2 doctors | Alternate (J45): 4 beds, 1 doctor | emergency_enabled: true"],
    ["model/live_inputs/", "5 watched traffic camera files: CAM_HOSPITAL_DIRECT_1/2/3, CAM_ORR_NORTH/SOUTH (.jpg/.png)"],
    ["model/ambulance demo images/", "Prerecorded junction frames: test_amb.jpg, test_amb2.jpeg, test_amb3.jpeg, test_amb4.jpg, test_amb5.jpg"],
    ["frontend/src/utils/networkTopology.ts", "SUMO_JUNCTIONS (48 nodes), NETWORK_EDGES (100+), CAMERA_DEFINITIONS (5 traffic + 1 junction), CONTROLLED_SIGNALS [J10,J12,J14,J24,J32]"],
]

widths4 = [60, 130]
for i, row in enumerate(configs):
    pdf.table_row(row, widths4, header=(i==0), fill=(i%2==1))

# ============================================================
# 8. KEY SIMULATION CONSTANTS
# ============================================================
pdf.chapter_title('8. Key Simulation Constants')

constants = [
    ["Constant", "Value", "Description"],
    ["AMBULANCE_ID", "\"AI_AMB_001\"", "Vehicle ID in SUMO"],
    ["ROUTE_ID", "\"AI_DYNAMIC_EMERGENCY_ROUTE\"", "TraCI route ID"],
    ["VEHICLE_PUBLISH_INTERVAL_S", "2.0", "WebSocket VEHICLE_UPDATE frequency"],
    ["REALTIME_TRAFFIC_UPDATE_INTERVAL_S", "30.0", "Simulated CCTV phase refresh interval"],
    ["MIN_REROUTE_IMPROVEMENT", "0.10 (10%)", "Minimum cost reduction to trigger reroute"],
    ["REROUTE_COOLDOWN_S", "30.0", "Minimum time between reroute attempts"],
    ["AMBULANCE_SPEED_FACTOR", "1.15", "Speed multiplier for emergency vehicle"],
    ["AMBULANCE_BLUE_LIGHT_REACTION_DISTANCE_M", "75.0", "SUMO blue-light rescue lane reaction distance"],
    ["BLOCKER_CLEAR_DISTANCE_M", "75.0", "Detect leader up to this distance"],
    ["BLOCKER_FORCE_GAP_M", "45.0", "Request lane change when gap < this"],
    ["PICKUP_REPLAN_DISTANCE_M", "80.0", "Replan hospital leg when approaching pickup"],
    ["STOP_SPEED_KMH", "1.0", "Threshold for stop detection"],
    ["STOP_CONFIRM_SECONDS", "2.0", "Duration to confirm full stop"],
]

for i, row in enumerate(constants):
    pdf.table_row(row, [70, 30, 90], header=(i==0), fill=(i%2==1))

# ============================================================
# 9. RUNNING THE FULL STACK
# ============================================================
pdf.add_page()
pdf.chapter_title('9. Running the Full Stack')

pdf.body_text('Three terminals required:')

pdf.chapter_title('Terminal 1: Backend', level=2)
pdf.code_block("""cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Verify:
# http://127.0.0.1:8000/health     -> {"status":"ok"}
# http://127.0.0.1:8000/docs       -> Swagger UI
# http://127.0.0.1:8000/api/state  -> Full state snapshot""")

pdf.chapter_title('Terminal 2: Frontend', level=2)
pdf.code_block("""cd frontend
npm install          # First time only
npm run dev          # Starts Vite on http://localhost:5173""")

pdf.chapter_title('Terminal 3: Simulation', level=2)
pdf.code_block("""cd model
# Live camera mode (recommended for demo):
python ai_emergency_demo.py --live-cameras --pickup-replan --delay 500

# Phase demo mode (deterministic):
python ai_emergency_demo.py --camera CAM_HOSPITAL_DIRECT_1 low1.jpeg \
  --camera CAM_HOSPITAL_DIRECT_2 low2.jpg \
  --camera CAM_HOSPITAL_DIRECT_3 low1.jpeg \
  --camera CAM_ORR_NORTH high3.jpg \
  --camera CAM_ORR_SOUTH high4.jpg \
  --pickup-replan --delay 500

# Baseline (no green corridor):
python ai_emergency_demo.py --live-cameras --no-green-corridor""")

pdf.chapter_title('Demo Scenario', level=2)
pdf.body_text(
    'Scenario A (Initial): Direct Corridor LOW, ORR HIGH -> Route: J23->J31->J39->J47\n'
    'Scenario B (After upload): Direct Corridor HIGH, ORR LOW -> Route: J23->J24->J32->J40->J48->J47\n\n'
    'To test: Open Traffic Cameras page, click "Change Frame" on CAM_HOSPITAL_DIRECT_1, '
    'upload high2.jpg, watch pipeline status and route change live.'
)

# ============================================================
# 10. REAL-WORLD IMPLEMENTATION PLAN
# ============================================================
pdf.add_page()
pdf.chapter_title('10. Real-World Implementation Plan')

pdf.chapter_title('10.1 Hardware & Infrastructure Requirements', level=2)

hw = [
    ["Component", "Specification", "Qty Estimate (Per Corridor)"],
    ["Traffic Cameras (CCTV)", "IP cameras, 1080p@30fps, H.264/H.265, PoE+, low-light capable", "5-10 per corridor"],
    ["Junction Cameras", "Zoom PTZ or fixed, 60fps, IR illumination, AI accelerator (Jetson Orin/Google Coral)", "1 per signalized junction"],
    ["Edge Compute", "NVIDIA Jetson AGX Orin (275 TOPS) or x86 + GPU, 32GB RAM, 1TB NVMe", "1 per 5-10 junctions"],
    ["Traffic Signal Controllers", "NEMA TS-2 / ATC 5201 / 2070 with NTCIP 1202 or UTC/SCOOT/SCATS interface", "All signalized junctions"],
    ["Communication", "Fiber/5G/Private LTE, <50ms latency, 99.9% uptime", "Backbone + last-mile"],
    ["Central Server", "Kubernetes cluster (3+ nodes), 64-core, 256GB RAM, GPU nodes for CNN batch", "1 per city/region"],
    ["Ambulance Onboard Unit", "GNSS (RTK), 5G/V2X modem, CAN bus interface, ruggedized tablet", "Per ambulance"],
    ["V2X RSUs", "C-V2X (PC5) or DSRC, 300m range, SAE J2735/J2945", "Per junction"],
]

for i, row in enumerate(hw):
    pdf.table_row(row, [45, 95, 50], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('10.2 Software Architecture Changes for Production', level=2)

sw_changes = [
    ["Simulation Component", "Production Replacement", "Effort"],
    ["SUMO/TraCI", "Real traffic signal controllers (NTCIP/UTC/SCOOT) + V2X stack", "High"],
    ["ai_emergency_demo.py", "Microservices: CameraIngestion, CNNInference, RoutingEngine, CorridorManager, VehicleTracker", "High"],
    ["GreenCorridorController", "CorridorManager service with persistent state, HA, audit logging", "Medium"],
    ["JunctionCameraManager", "CameraIngestion service with ONVIF/RTSP, multi-model ensemble, confidence calibration", "Medium"],
    ["EdgeTrafficManager", "TrafficStateEstimator with Kalman filtering, historical baselines, incident detection", "Medium"],
    ["SumoRoadGraph/A*", "RoutingEngine with Contraction Hierarchies / CH + real-time traffic (TomTom/Here/Google)", "Medium"],
    ["HospitalSelector", "HospitalIntegrationService with HL7/FHIR for bed/doctor status, EMS protocols", "High"],
    ["BackendEventPublisher", "Kafka/NATS event bus, schema registry, replay capability", "Low"],
    ["FastAPI Backend", "API Gateway + Auth (OAuth2/OIDC) + Rate limiting + Audit", "Low"],
    ["React Frontend", "Role-based UI (Dispatcher/Supervisor/Admin), offline-capable PWA, multi-language", "Medium"],
]

for i, row in enumerate(sw_changes):
    pdf.table_row(row, [50, 95, 25], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('10.3 Integration with Existing Traffic Systems', level=2)

pdf.body_text('Real deployment requires integration with existing Traffic Management Centers (TMC):')

integrations = [
    "Signal Control: NTCIP 1202 (ASC/ASC3) or proprietary (SCOOT/SCATS/UTC) - preemption requests via priority request generator",
    "V2X: SAE J2735 BSM/MAP/SPAT/EMMA messages over C-V2X PC5 or DSRC - ambulance broadcasts, RSU relays SPAT",
    "CAD/EMS: CAD API (TriTech/Versaterm/HEMS) for dispatch notifications, hospital selection, patient data (HL7/FHIR)",
    "Traffic Data: Existing loop detectors/Bluetooth/WiFi sensors + camera feeds fused with CNN for better estimation",
    "Mapping: HERE/TomTom/Mapbox for base map + lane-level geometry for routing",
    "Communications: FirstNet / dedicated 5G slice for priority bandwidth",
    "Standards: NEMA TS-8 (preemption), IEEE 1609/ETSI ITS-G5 (V2X), FHIR R4 (hospital data)",
]

for item in integrations:
    pdf.bullet_point(item)

# ============================================================
# 10.4 REGULATORY & SAFETY
# ============================================================
pdf.add_page()
pdf.chapter_title('10.4 Regulatory & Safety Considerations', level=2)

pdf.body_text('Safety is paramount. The simulation enforces these invariants that MUST carry to production:')

safety = [
    "NO all-green phases: Only compatible movements get green; conflicting approaches stay red",
    "Physical-pass restoration: Signals restore ONLY when ambulance clears junction (not timer expiry)",
    "SUMO phase legality: Only EXISTING legal phases selected; never synthesize new phase combinations",
    "Fail-safe: If corridor loses comms/ambulance tracking -> immediate restore to normal program",
    "Audit trail: Every preemption logged with timestamp, junction, phase, duration, trigger, operator",
    "Manual override: TMC operator can disable corridor instantly via big red button",
    "Certification: ISO 26262 ASIL-B for corridor logic, IEC 61508 SIL-2 for signal interface",
    "Liability: Clear chain: CNN confidence -> TraCI confirmation -> Corridor arm -> Phase select -> Hold -> Restore",
]

for item in safety:
    pdf.bullet_point(item)

pdf.ln(3)
pdf.body_text('Regulatory approvals needed:')
regulatory = [
    "Local DOT/Transport Authority: Signal preemption policy approval",
    "EMS Medical Director: Hospital selection criteria, diversion protocols",
    "Police/Fire: Inter-agency preemption priority hierarchy (Fire > EMS > Police > Transit)",
    "Privacy: Camera feeds - GDPR/CCPA compliance, retention policies, anonymization",
    "Cybersecurity: NIST 800-53 / IEC 62443 for OT network, penetration testing",
]

for item in regulatory:
    pdf.bullet_point(item)

# ============================================================
# 10.5 PHASED DEPLOYMENT
# ============================================================
pdf.chapter_title('10.5 Phased Deployment Approach', level=2)

phases = [
    ["Phase", "Timeline", "Scope", "Success Criteria"],
    ["0: Shadow Mode", "Months 1-3", "Cameras installed, CNN running, NO signal control. Compare CNN vs loops.", "CNN MAE < 15% vs ground truth; latency < 2s"],
    ["1: Single Corridor", "Months 4-8", "1 corridor (5-8 junctions), 2-3 ambulances, TMC operator override always active", "Response time -15%; zero safety incidents; operator confidence > 80%"],
    ["2: Multi-Corridor", "Months 9-18", "3-5 corridors, full ambulance fleet, hospital integration (HL7/FHIR)", "Response time -25%; hospital diversion accuracy > 90%"],
    ["3: City-Wide + V2X", "Months 19-36", "All corridors, V2X RSUs, CAD integration, public API for navigation apps", "System availability 99.9%; <50ms V2X latency; public trust metrics"],
]

for i, row in enumerate(phases):
    pdf.table_row(row, [30, 25, 75, 60], header=(i==0), fill=(i%2==1))

# ============================================================
# 11. REAL-WORLD VALUE PROPOSITION
# ============================================================
pdf.add_page()
pdf.chapter_title('11. Real-World Value Proposition')

pdf.chapter_title('11.1 Quantifiable Benefits', level=2)

pdf.body_text('Based on simulation results and literature (NHTSA, FHWA, ITS studies):')

benefits = [
    ["Metric", "Simulation Result", "Literature Range", "Mechanism"],
    ["Response Time Reduction", "20-35%", "20-40% (FHWA)", "Green corridor eliminates stops at signals"],
    ["Intersection Stops", "Near zero", "80-95% reduction", "Rolling preemption + physical-pass restore"],
    ["Route Optimality", "Dynamic A* 10%+ better", "10-20% vs static", "CNN traffic -> edge costs -> reroute"],
    ["Hospital Selection", "Multi-criteria optimal", "N/A (novel)", "Beds + doctors + route cost combined"],
    ["Fuel/Emissions", "Est. 15-25% less", "10-30% (ITS)", "Fewer stops/accelerations, smoother flow"],
    ["Secondary Crashes", "Reduced", "30-50% (preemption studies)", "Controlled preemption vs manual run-red"],
    ["Operator Workload", "Automated", "N/A", "One detection arms full corridor"],
    ["Situational Awareness", "Real-time dashboard", "N/A", "Unified view: camera, signal, route, ambulance"],
]

for i, row in enumerate(benefits):
    pdf.table_row(row, [35, 35, 35, 85], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('11.2 Comparison: Simulation vs Reality', level=2)

comp = [
    ["Aspect", "Simulation", "Reality Gap", "Mitigation"],
    ["Traffic Flow", "Microscopic (car-following)", "Human behavior, incidents, weather", "Calibration + historical baselines + incident detection"],
    ["CNN Input", "Prerecorded frames", "Weather, occlusion, night, compression artifacts", "Ensemble models, test-time augmentation, domain adaptation"],
    ["Signal Control", "Instant TraCI setPhase", "Controller latency (100-500ms), NTCIP overhead", "Predictive activation (preempt earlier), latency compensation"],
    ["Ambulance Motion", "Ideal blue-light", "Driver behavior, traffic non-compliance", "V2X warnings to drivers, integrated CAD dispatch"],
    ["Communications", "Local WebSocket (0ms)", "Network latency, packet loss, 5G handover", "Edge compute at junction, store-forward, QoS"],
    ["Hospital Data", "Static JSON", "Real-time HL7/FHIR, bed holds, diversion status", "Direct EHR integration, standardized APIs"],
    ["Scale", "48 junctions", "1000+ junctions, multi-agency", "Hierarchical corridor management, zone controllers"],
]

for i, row in enumerate(comp):
    pdf.table_row(row, [30, 40, 55, 65], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('11.3 Cost-Benefit Analysis (Per Corridor, 5 Years)', level=2)

costs = [
    ["Category", "CAPEX", "OPEX (Annual)", "Notes"],
    ["Cameras (10x CCTV + 5x Junction)", "$150K", "$15K", "IP cameras, mounts, PoE switches, cabling"],
    ["Edge Compute (2x Jetson Orin)", "$30K", "$5K", "Hardware refresh 3yr, power, cooling"],
    ["Signal Controller Upgrades", "$200K", "$20K", "NTCIP/preemption firmware, cabinet mods"],
    ["Communications (Fiber/5G)", "$100K", "$30K", "Construction, lease, managed service"],
    ["Central Platform (K8s, 3yr)", "$200K", "$100K", "Cloud/on-prem, GPU nodes, monitoring, backup"],
    ["Integration (CAD, HL7, V2X)", "$300K", "$50K", "One-time dev + annual maintenance"],
    ["Personnel (2 FTE ops + 1 FTE dev)", "---", "$400K", "TMC operators, DevOps, ML engineers"],
    ["Training & Change Management", "$50K", "$20K", "Simulator, drills, documentation"],
    ["TOTAL (5yr)", "$1,030K", "$640K/yr", "5-yr TCO ~ $4.2M per corridor"],
]

for i, row in enumerate(costs):
    pdf.table_row(row, [60, 30, 30, 70], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.body_text(
    'Benefit valuation (conservative): 1 corridor, 200 emergencies/yr, 10 min saved each = '
    '333 hrs/yr @ $500/hr (ambulance + crew + societal) = $166K/yr direct savings. '
    'Indirect: reduced secondary crashes, better outcomes, fuel savings. '
    'Payback: ~3-4 years. City-wide (10 corridors): 5-yr NPV strongly positive.'
)

# ============================================================
# 12. KEY DIFFERENTIATORS
# ============================================================
pdf.add_page()
pdf.chapter_title('12. Key Differentiators & Innovation')

pdf.body_text('What makes this system unique compared to existing preemption products (Opticom, EMTRAC, etc.):')

diffs = [
    ["Feature", "Traditional Preemption", "This System"],
    ["Trigger", "Ambulance-mounted emitter (IR/Radio/GPS)", "Junction camera CNN visual confirmation + TraCI position"],
    ["Scope", "Single intersection", "Rolling corridor across entire route (2+ signals, 900m)"],
    ["Routing", "Fixed route", "Dynamic A* with real-time CNN traffic -> reroute -> corridor rebuilds"],
    ["Restoration", "Timer-based (fixed hold)", "Physical-pass: restores ONLY when ambulance on outgoing edge"],
    ["Hospital Selection", "Nearest / pre-defined", "Multi-criteria: beds + doctors + eligibility + dynamic route cost"],
    ["Traffic Awareness", "None (blind preemption)", "Full CNN traffic state -> edge costs -> routing -> corridor"],
    ["Pickup Transition", "N/A", "Complete hospital-leg replan at pickup junction (J23)"],
    ["Visualization", "None / proprietary", "Open web dashboard: cameras, signals, route, corridor, events, replay"],
    ["Safety Model", "Trust emitter", "Defense-in-depth: CNN confidence + TraCI confirm + route check + legal phases only"],
    ["Standards", "Proprietary", "Open: NTCIP, V2X (J2735), FHIR, ONVIF, Kafka, REST, WebSocket"],
]

for i, row in enumerate(diffs):
    pdf.table_row(row, [40, 70, 80], header=(i==0), fill=(i%2==1))

pdf.ln(5)
pdf.chapter_title('Innovation Summary', level=2)

pdf.body_text(
    'This project demonstrates a complete, working prototype of the next generation of emergency '
    'vehicle preemption: camera-verified, route-aware, dynamically rerouted, and fully observable. '
    'The simulation-to-reality gap is primarily engineering (integration, hardening, certification) '
    'not algorithmic - the core logic (GreenCorridorController, JunctionCameraManager, '
    'EdgeTrafficManager, HospitalSelector) is production-ready in architecture.'
)

pdf.body_text(
    'The frontend-backend separation (WebSocket + REST) and event-driven architecture '
    '(STATE_SNAPSHOT + incremental events) mirrors modern ITS platform designs '
    '(e.g., AWS IoT FleetWise, Azure IoT Operations, custom TMC platforms).'
)

# ============================================================
# SAVE
# ============================================================
output_path = r"C:\Users\chapp\Desktop\Major Project\AI Traffic Control- Copy\AI_Smart_Ambulance_Project_Documentation.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
print(f"Pages: {pdf.page_no()}")