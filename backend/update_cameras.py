import re

with open('main.py', 'r') as f:
    content = f.read()

old = '''LIVE_TRAFFIC_CAMERA_IDS = {
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
};'''

new = '''LIVE_TRAFFIC_CAMERA_IDS = {
    "CAM_STATION_APPROACH",
    "CAM_STATION_J02",
    "CAM_J02_J03",
    "CAM_J03_J04",
    "CAM_CBD_WEST",
    "CAM_J10_J18",
    "CAM_CBD_EAST",
    "CAM_J12_J20",
    "CAM_PICKUP_CORRIDOR",
    "CAM_J14_J15",
    "CAM_J15_J16",
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_J39_J40",
    "CAM_J40_J48",
    "CAM_J48_J47",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_J23_J24",
    "CAM_J24_J32",
    "CAM_J32_J40",
    "CAM_ALT_HOSPITAL_1",
    "CAM_ALT_HOSPITAL_2",
    "CAM_J11_J19",
    "CAM_J13_J21",
    "CAM_J21_J22",
};'''

content = content.replace(old, new)
with open('main.py', 'w') as f:
    f.write(content)
print('Done')