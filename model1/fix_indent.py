import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Fix the duplicate phase_2 and trailing garbage
# The structure should be:
# REALTIME_PHASE_FALLBACKS = {
#     "phase_1": {...},
#     "phase_2": {...},
# }
# Then LIVE_TRAFFIC_CAMERA_IDS = ...

# Find and fix the malformed section
old_malformed = '''    },

    "phase_2": {
        "CAM_STATION_APPROACH": "high2.jpg",
        "CAM_STATION_J02": "high3.jpg",
        "CAM_J02_J03": "high4.jpg",
        "CAM_J03_J04": "high2.jpg",
        "CAM_CBD_WEST": "high3.jpg",
        "CAM_J10_J18": "high4.jpg",
        "CAM_CBD_EAST": "high2.jpg",
        "CAM_J12_J20": "high3.jpg",
        "CAM_PICKUP_CORRIDOR": "high4.jpg",
        "CAM_J14_J15": "high2.jpg",
        "CAM_J15_J16": "high3.jpg",
        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",
        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",
        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",
        "CAM_J39_J40": "low2.jpg",
        "CAM_J40_J48": "low1.jpeg",
        "CAM_J48_J47": "low2.jpg",
        "CAM_ORR_NORTH": "low1.jpeg",
        "CAM_ORR_SOUTH": "low2.jpg",
        "CAM_J23_J24": "high2.jpg",
        "CAM_J24_J32": "high3.jpg",
        "CAM_J32_J40": "high4.jpg",
        "CAM_ALT_HOSPITAL_1": "low1.jpeg",
        "CAM_ALT_HOSPITAL_2": "low2.jpg",
        "CAM_J11_J19": "high2.jpg",
        "CAM_J13_J21": "high3.jpg",
        "CAM_J21_J22": "high4.jpg",
    },

}

# Filesystem-watched traffic-camera mode'''

new_fixed = '''

# Filesystem-watched traffic-camera mode'''

content = content.replace(old_malformed, new_fixed)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Fixed!')