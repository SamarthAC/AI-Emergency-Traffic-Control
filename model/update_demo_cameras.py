import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Update phase_1
old_phase1 = r'"phase_1"\s*:\s*\{[^}]+\}'
new_phase1 = '''"phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpeg",

        "CAM_ORR_SOUTH": "high4.jpeg",

        "CAM_ALT_HOSPITAL": "high3.jpeg",

        "CAM_VERTICAL_RIGHT_1": "low1.jpeg",

        "CAM_VERTICAL_RIGHT_2": "low2.jpeg",

        "CAM_J14_J13": "low2.jpeg",

        "CAM_J21_J29": "low1.jpeg",

        "CAM_J22_J23": "low1.jpeg",

        "CAM_J22_J30": "low1.jpeg",

    }'''

content = re.sub(old_phase1, new_phase1, content, flags=re.DOTALL)

# Update phase_2
old_phase2 = r'"phase_2"\s*:\s*\{[^}]+\}'
new_phase2 = '''"phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpeg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpeg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpeg",

        "CAM_ALT_HOSPITAL": "low1.jpeg",

        "CAM_VERTICAL_RIGHT_1": "high3.jpeg",

        "CAM_VERTICAL_RIGHT_2": "high4.jpeg",

        "CAM_J14_J13": "high3.jpeg",

        "CAM_J21_J29": "high2.jpeg",

        "CAM_J22_J23": "high2.jpeg",

        "CAM_J22_J30": "high2.jpeg",

    }'''

content = re.sub(old_phase2, new_phase2, content, flags=re.DOTALL)

# Update LIVE_TRAFFIC_CAMERA_IDS
old_live = r'LIVE_TRAFFIC_CAMERA_IDS\s*=\s*\([^)]+\)'
new_live = '''LIVE_TRAFFIC_CAMERA_IDS = (
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_ALT_HOSPITAL",
    "CAM_VERTICAL_RIGHT_1",
    "CAM_VERTICAL_RIGHT_2",
    "CAM_J14_J13",
    "CAM_J21_J29",
    "CAM_J22_J23",
    "CAM_J22_J30",
)'''

content = re.sub(old_live, new_live, content, flags=re.DOTALL)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Demo updated with new cameras')