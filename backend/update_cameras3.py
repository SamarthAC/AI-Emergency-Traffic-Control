import re

with open('main.py', 'r') as f:
    content = f.read()

# Replace LIVE_TRAFFIC_CAMERA_IDS with the new 10 cameras
pattern = r'LIVE_TRAFFIC_CAMERA_IDS\s*=\s*\{[^}]+\}'
replacement = '''LIVE_TRAFFIC_CAMERA_IDS = {
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
};'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)
print('Done')