import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, 'model')

import main as backend_main
import ai_emergency_demo as demo
from edge_traffic_manager import CAMERA_EDGE_MAP

print('=== FINAL VERIFICATION ===')
print()
print('=== BACKEND (main.py) ===')
print('Cameras: ' + str(len(backend_main.LIVE_TRAFFIC_CAMERA_IDS)))
for c in sorted(backend_main.LIVE_TRAFFIC_CAMERA_IDS):
    print('  ' + c)

print()
print('=== DEMO ===')
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
print('=== CONSISTENCY CHECK ===')
backend_cams = set(backend_main.LIVE_TRAFFIC_CAMERA_IDS)
demo_cams = set(demo.LIVE_TRAFFIC_CAMERA_IDS)
edge_cams = set(CAMERA_EDGE_MAP.keys())

print('Backend == Demo: ' + str(backend_cams == demo_cams))
print('Demo subset of EdgeManager: ' + str(demo_cams.issubset(set(CAMERA_EDGE_MAP.keys()))))
print('Backend cams: ' + str(len(backend_cams)))
print('Demo cams: ' + str(len(demo_cams)))
print('Edge cams: ' + str(len(edge_cams)))
print()
if (backend_cams == demo_cams and demo_cams.issubset(set(CAMERA_EDGE_MAP.keys()))):
    print('ALL CHECKS PASSED!')
else:
    print('ISSUES FOUND!')