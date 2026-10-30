import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# 1. Replace REALTIME_PHASE_FALLBACKS completely with new 10 cameras
old_phase = r'REALTIME_PHASE_FALLBACKS\s*=\s*\{[^}]+\}'
new_phase = '''REALTIME_PHASE_FALLBACKS = {

    "phase_1": {
        "CAM_STATION": "low1.jpeg",
        "CAM_CBD_ENTRY": "low2.jpg",
        "CAM_CBD_MID": "low1.jpeg",
        "CAM_CBD_EXIT": "low2.jpg",
        "CAM_ORR_NORTH": "low1.jpeg",
        "CAM_ORR_MID": "low2.jpg",
        "CAM_ORR_HOSPITAL": "low1.jpeg",
        "CAM_DIRECT_HOSPITAL": "high2.jpg",
        "CAM_ALT_HOSPITAL": "high3.jpg",
        "CAM_HOSPITAL_ZONE": "high4.jpg",
    },

    "phase_2": {
        "CAM_STATION": "high2.jpg",
        "CAM_CBD_ENTRY": "high3.jpg",
        "CAM_CBD_MID": "high4.jpg",
        "CAM_CBD_EXIT": "high2.jpg",
        "CAM_ORR_NORTH": "high3.jpg",
        "CAM_ORR_MID": "high4.jpg",
        "CAM_ORR_HOSPITAL": "high2.jpg",
        "CAM_DIRECT_HOSPITAL": "low1.jpeg",
        "CAM_ALT_HOSPITAL": "low1.jpeg",
        "CAM_HOSPITAL_ZONE": "low1.jpeg",
    },

}'''

content = re.sub(old_phase, new_phase, content, flags=re.DOTALL)

# 2. Update LIVE_TRAFFIC_CAMERA_IDS to use new camera IDs
old_live_ids = r'LIVE_TRAFFIC_CAMERA_IDS\s*=\s*tuple\(REALTIME_PHASE_FALLBACKS\["phase_1"\]\.keys\(\)\)'
new_live_ids = '''LIVE_TRAFFIC_CAMERA_IDS = (
    "CAM_STATION",
    "CAM_CBD_ENTRY",
    "CAM_CBD_MID",
    "CAM_CBD_EXIT",
    "CAM_ORR_NORTH",
    "CAM_ORR_MID",
    "CAM_ORR_HOSPITAL",
    "CAM_DIRECT_HOSPITAL",
    "CAM_ALT_HOSPITAL",
    "CAM_HOSPITAL_ZONE",
)'''

content = re.sub(old_live_ids, new_live_ids, content)

# 3. Update the pickup replan comment
content = content.replace(
    'J23 -> hospital corridor',
    'J10 -> hospital corridor'
)

# 4. Update the camera count comment
content = content.replace(
    'five camera-ID frames',
    'ten camera-ID frames'
)

content = content.replace(
    'the five camera-ID frames',
    'the ten camera-ID frames'
)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Done')