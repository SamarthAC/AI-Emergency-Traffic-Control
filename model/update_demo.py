import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# 1. Update REALTIME_PHASE_FALLBACKS
old_phase_fallbacks = '''REALTIME_PHASE_FALLBACKS = {

    "phase_1": {

        "CAM_HOSPITAL_DIRECT_1": "low1.jpeg",

        "CAM_HOSPITAL_DIRECT_2": "low2.jpg",

        "CAM_HOSPITAL_DIRECT_3": "low1.jpeg",

        "CAM_ORR_NORTH": "high3.jpg",

        "CAM_ORR_SOUTH": "high4.jpg",

    },

    "phase_2": {

        "CAM_HOSPITAL_DIRECT_1": "high2.jpg",

        "CAM_HOSPITAL_DIRECT_2": "high3.jpg",

        "CAM_HOSPITAL_DIRECT_3": "high4.jpg",

        "CAM_ORR_NORTH": "low1.jpeg",

        "CAM_ORR_SOUTH": "low2.jpg",

    },

}'''

new_phase_fallbacks = '''REALTIME_PHASE_FALLBACKS = {

    "phase_1": {
        "CAM_STATION_APPROACH": "low1.jpeg",
        "CAM_STATION_J02": "low1.jpeg",
        "CAM_J02_J03": "low2.jpg",
        "CAM_J03_J04": "low1.jpeg",
        "CAM_CBD_WEST": "low2.jpg",
        "CAM_J10_J18": "low1.jpeg",
        "CAM_CBD_EAST": "low1.jpeg",
        "CAM_J12_J20": "low2.jpg",
        "CAM_PICKUP_CORRIDOR": "low2.jpg",
        "CAM_J14_J15": "low1.jpeg",
        "CAM_J15_J16": "low2.jpg",
        "CAM_HOSPITAL_DIRECT_1": "high2.jpg",
        "CAM_HOSPITAL_DIRECT_2": "high3.jpg",
        "CAM_HOSPITAL_DIRECT_3": "high4.jpg",
        "CAM_J39_J40": "high3.jpg",
        "CAM_J40_J48": "high4.jpg",
        "CAM_J48_J47": "high4.jpg",
        "CAM_ORR_NORTH": "high3.jpg",
        "CAM_ORR_SOUTH": "high4.jpg",
        "CAM_J23_J24": "low1.jpeg",
        "CAM_J24_J32": "low2.jpg",
        "CAM_J32_J40": "low1.jpeg",
        "CAM_ALT_HOSPITAL_1": "high2.jpg",
        "CAM_ALT_HOSPITAL_2": "high3.jpg",
        "CAM_J11_J19": "low1.jpeg",
        "CAM_J13_J21": "low2.jpg",
        "CAM_J21_J22": "low1.jpeg",
    },

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

}'''

content = content.replace(old_phase_fallbacks, new_phase_fallbacks)

# 2. Update LIVE_TRAFFIC_CAMERA_IDS
old_live_ids = '''LIVE_TRAFFIC_CAMERA_IDS = tuple(REALTIME_PHASE_FALLBACKS["phase_1"].keys())'''

new_live_ids = '''LIVE_TRAFFIC_CAMERA_IDS = tuple(REALTIME_PHASE_FALLBACKS["phase_1"].keys())'''

# The LIVE_TRAFFIC_CAMERA_IDS will automatically update since it's derived from phase_1 keys
# But we need to ensure the pickup default is changed

# 3. Change default pickup from J23 to J10
content = content.replace('parser.add_argument("--pickup", default="J23")', 'parser.add_argument("--pickup", default="J10")')

# 4. Update the comment about pickup replan
content = content.replace(
    '# Optional presentation/mission-transition mode. When enabled, live camera\n# changes before pickup update the traffic graph/UI but do not change the\n# hospital leg immediately. A fresh A* plan is committed as the ambulance\n# reaches the pickup junction, so the entire J23 -> hospital corridor can\n# change as one clean routing decision.',
    '# Optional presentation/mission-transition mode. When enabled, live camera\n# changes before pickup update the traffic graph/UI but do not change the\n# hospital leg immediately. A fresh A* plan is committed as the ambulance\n# reaches the pickup junction, so the entire J10 -> hospital corridor can\n# change as one clean routing decision.'
)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Done')