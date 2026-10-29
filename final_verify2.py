import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, 'model')
sys.path.insert(0, 'frontend/src')

import main as backend_main
import ai_emergency_demo as demo
from edge_traffic_manager import CAMERA_EDGE_MAP
from utils.networkTopology import NETWORK_EDGES

print('=== FINAL VERIFICATION ===')
print()

print('=== BACKEND ===')
print('Cameras:', len(backend_main.LIVE_TRAFFIC_CAMERA_IDS))
for c in sorted(backend_main.LIVE_TRAFFIC_CAMERA_IDS):
    print('  ' + c)

print()
print('=== DEMO ===')
import ai_emergency_demo as demo
print('LIVE_TRAFFIC_CAMERA_IDS:', len(demo.LIVE_TRAFFIC_CAMERA_IDS))
print('Phase 1:', len(demo.REALTIME_PHASE_FALLBACKS['phase_1']))
print('Phase 2:', str(len(demo.REALTIME_PHASE_FALLBACKS['phase_2'])))

print()
print('=== EDGE_TRAFFIC_MANAGER ===')
from edge_traffic_manager import CAMERA_EDGE_MAP
print('CAMERA_EDGE_MAP: ' + str(len(CAMERA_EDGE_MAP)) + ' cameras')
missing = [c for c in demo.LIVE_TRAFFIC_CAMERA_IDS if c not in CAMERA_EDGE_MAP]
print('Missing in EdgeTrafficManager:', missing if missing else 'None')

print()
print('=== NETWORK EDGES ===')
from utils.networkTopology import NETWORK_EDGES
j14_j22 = [e for e in NETWORK_EDGES if e.id == 'J14_J22']
print('J14_J22 in NETWORK_EDGES:', len(j14_j22) > 0)
if j14_j22:
    print('  Edge:', j14_j22[0].id, j14_j22[0].from_node, '->', j14_j22[0].to_node)

print()
print('=== CONSISTENCY CHECK ===')
backend_cams = set(backend_main.LIVE_TRAFFIC_CAMERA_IDS)
demo_cams = set(demo.LIVE_TRAFFIC_CAMERA_IDS)
edge_cams = set(CAMERA_EDGE_MAP.keys())

print('Backend == Demo:', backend_cams == demo_cams)
print('Demo subset of EdgeManager:', demo_cams.issubset(set(CAMERA_EDGE_MAP.keys())))
print('Backend cams:', len(backend_cams))
print('Demo cams:', len(demo_cams))
print('Edge cams:', len(edge_cams))
print()
if (backend_cams == demo_cams and demo_cams.issubset(set(CAMERA_EDGE_MAP.keys()))):
    print('ALL CHECKS PASSED!')
else:
    print('ISSUES FOUND!')