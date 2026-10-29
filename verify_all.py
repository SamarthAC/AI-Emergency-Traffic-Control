import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, 'model')
sys.path.insert(0, 'frontend')

import main as backend_main
import ai_emergency_demo as demo
from frontend.src.utils.networkTopology import CAMERA_DEFINITIONS
from edge_traffic_manager import CAMERA_EDGE_MAP

print('=== CAMERA CONFIGURATION SUMMARY ===')
print()

print('=== BACKEND (main.py) ===')
print('LIVE_TRAFFIC_CAMERA_IDS: ' + str(len(backend_main.LIVE_TRAFFIC_CAMERA_IDS)) + ' cameras')
for c in sorted(backend_main.LIVE_TRAFFIC_CAMERA_IDS):
    print('  ' + c)

print()
print('=== DEMO (ai_emergency_demo.py) ===')
print('LIVE_TRAFFIC_CAMERA_IDS: ' + str(len(demo.LIVE_TRAFFIC_CAMERA_IDS)))
print('Phase 1: ' + str(len(demo.REALTIME_PHASE_FALLBACKS['phase_1'])))
print('Phase 2: ' + str(len(demo.REALTIME_PHASE_FALLBACKS['phase_2'])))

print()
print('=== EDGE_TRAFFIC_MANAGER ===')
from edge_traffic_manager import CAMERA_EDGE_MAP
print('CAMERA_EDGE_MAP: ' + str(len(CAMERA_EDGE_MAP)) + ' cameras')
missing = [c for c in demo.LIVE_TRAFFIC_CAMERA_IDS if c not in CAMERA_EDGE_MAP]
print('Missing in EdgeTrafficManager: ' + (str(missing) if missing else 'None'))

print()
print('=== FRONTEND NETWORK TOPOLOGY ===')
from frontend.src.utils.networkTopology import CAMERA_DEFINITIONS
traffic_cams = [c for c in CAMERA_DEFINITIONS if CAMERA_DEFINITIONS[c].type == 'traffic']
junction_cams = [c for c in CAMERA_DEFINITIONS if CAMERA_DEFINITIONS[c].type == 'junction']
print('Traffic cameras: ' + str(len(traffic_cams)))
for c in traffic_cams:
    cam = CAMERA_DEFINITIONS[c]
    print('  ' + cam.id + ': ' + cam.name + ' - edges: ' + str(cam.edgeIds))
junction_cams = [c for c in CAMERA_DEFINITIONS if CAMERA_DEFINITIONS[c].type == 'junction']
print('Junction cameras: ' + str(len(junction_cams)))
for c in junction_cams:
    cam = CAMERA_DEFINITIONS[c]
    print('  ' + cam.id + ': junction ' + cam.junctionId)

print()
print('=== VERIFICATION ===')
backend_cams = set(backend_main.LIVE_TRAFFIC_CAMERA_IDS)
demo_cams = set(demo.LIVE_TRAFFIC_CAMERA_IDS)
edge_cams = set(CAMERA_EDGE_MAP.keys())
frontend_traffic = set([c for c in CAMERA_DEFINITIONS if CAMERA_DEFINITIONS[c].type == 'traffic'])

print('Backend == Demo: ' + str(backend_cams == demo_cams))
print('Demo subset of EdgeManager: ' + str(demo_cams.issubset(set(CAMERA_EDGE_MAP.keys()))))
print('Demo subset of Frontend traffic: ' + str(demo_cams.issubset(frontend_traffic)))
print('Backend == Frontend traffic: ' + str(set(backend_main.LIVE_TRAFFIC_CAMERA_IDS) == frontend_traffic))
print()
if (backend_cams == demo_cams and demo_cams.issubset(set(CAMERA_EDGE_MAP.keys())) and demo_cams.issubset(frontend_traffic)):
    print('ALL CHECKS PASSED!')
else:
    print('ISSUES FOUND!')