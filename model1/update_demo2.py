import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# 1. Update REALTIME_PHASE_FALLBACKS for 10 cameras
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
        "CAM_ALT_HOSPITAL": "low2.jpeg",
        "CAM_HOSPITAL_ZONE": "low1.jpeg",
    },

}'''

content = content.replace(old_phase_fallbacks, new_phase_fallbacks)

# 2. Change default pickup from J23 to J10
content = content.replace('parser.add_argument("--pickup", default="J23")', 'parser.add_argument("--pickup", default="J10")')

# 3. Update the comment about pickup replan
content = content.replace(
    '# Optional presentation/mission-transition mode. When enabled, live camera\n# changes before pickup update the traffic graph/UI but do not change the\n# hospital leg immediately. A fresh A* plan is committed as the ambulance\n# reaches the pickup junction, so the entire J23 -> hospital corridor can\n# change as one clean routing decision.',
    '# Optional presentation/mission-transition mode. When enabled, live camera\n# changes before pickup update the traffic graph/UI but do not change the\n# hospital leg immediately. A fresh A* plan is committed as the ambulance\n# reaches the pickup junction, so the entire J10 -> hospital corridor can\n# change as one clean routing decision.'
)

# 4. Update the live_inputs folder comment
content = content.replace(
    'Then overwrite the five camera-ID frames in model/live_inputs while SUMO runs.',
    'Then overwrite the ten camera-ID frames in model/live_inputs while SUMO runs.'
)

# 4. Update the comment about Live camera mode
content = content.replace(
    'Live camera mode:\n\n    python ai_emergency_demo.py --live-cameras --delay 500\n\nThen overwrite the five camera-ID frames in model/live_inputs while SUMO runs.',
    'Live camera mode:\n\n    python ai_emergency_demo.py --live-cameras --delay 500\n\nThen overwrite the ten camera-ID frames in model/live_inputs while SUMO runs.'
)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Done')