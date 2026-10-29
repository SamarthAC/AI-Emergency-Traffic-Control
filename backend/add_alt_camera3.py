import re

with open('main.py', 'r') as f:
    content = f.read()

# Use regex to find and replace the entire LIVE_TRAFFIC_CAMERA_IDS block
pattern = r'LIVE_TRAFFIC_CAMERA_IDS\s*=\s*\{[^}]+\}'
replacement = '''LIVE_TRAFFIC_CAMERA_IDS = {
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_ALT_HOSPITAL",
}'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)

print('Done with regex')