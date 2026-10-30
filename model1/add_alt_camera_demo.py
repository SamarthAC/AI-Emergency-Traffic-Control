with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Update REALTIME_PHASE_FALLBACKS phase_1
old_phase1 = '''    "phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpg",

        "CAM_ORR_SOUTH": "high4.jpg",

    },'''

new_phase1 = '''    "phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpg",

        "CAM_ORR_SOUTH": "high4.jpg",

        "CAM_ALT_HOSPITAL": "high3.jpg",

    },'''

content = content.replace(old_phase1, new_phase1)

# Update REALTIME_PHASE_FALLBACKS phase_2
old_phase2 = '''    "phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpg",

    },'''

new_phase2 = '''    "phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpeg",

        "CAM_ALT_HOSPITAL": "low1.jpeg",

    },'''

content = content.replace(old_phase2, new_phase2)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Updated demo with CAM_ALT_HOSPITAL')