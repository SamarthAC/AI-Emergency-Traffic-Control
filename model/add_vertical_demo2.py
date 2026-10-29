import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Update phase_1
old_phase1 = '''    "phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpeg",

        "CAM_ORR_SOUTH": "high4.jpeg",

        "CAM_ALT_HOSPITAL": "high3.jpeg",

    },'''

new_phase1 = '''    "phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpeg",

        "CAM_ORR_SOUTH": "high4.jpeg",

        "CAM_ALT_HOSPITAL": "high3.jpeg",

        "CAM_VERTICAL_RIGHT_1": "low1.jpeg",

        "CAM_VERTICAL_RIGHT_2": "low2.jpeg",

    },'''

content = content.replace(old_phase1, new_phase1)

# Update phase_2
old_phase2 = '''    "phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpeg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpeg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpeg",

        "CAM_ALT_HOSPITAL": "low1.jpeg",

    },'''

new_phase2 = '''    "phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpeg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpeg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpeg",

        "CAM_ALT_HOSPITAL": "low1.jpeg",

        "CAM_VERTICAL_RIGHT_1": "high3.jpeg",

        "CAM_VERTICAL_RIGHT_2": "high4.jpeg",

    },'''

content = content.replace(old_phase2, new_phase2)

# Update LIVE_TRAFFIC_CAMERA_IDS
old_live = '''LIVE_TRAFFIC_CAMERA_IDS = (
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_ALT_HOSPITAL",
)'''

new_live = '''LIVE_TRAFFIC_CAMERA_IDS = (
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_ALT_HOSPITAL",
    "CAM_VERTICAL_RIGHT_1",
    "CAM_VERTICAL_RIGHT_2",
)'''

content = content.replace(old_live, new_live)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Demo updated with vertical cameras')