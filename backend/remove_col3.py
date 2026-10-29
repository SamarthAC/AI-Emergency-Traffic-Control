with open('main.py', 'r') as f:
    content = f.read()

old = '''LIVE_TRAFFIC_CAMERA_IDS = {
    "CAM_HOSPITAL_DIRECT_1",
    "CAM_HOSPITAL_DIRECT_2",
    "CAM_HOSPITAL_DIRECT_3",
    "CAM_ORR_NORTH",
    "CAM_ORR_SOUTH",
    "CAM_ALT_HOSPITAL",
    "CAM_VERTICAL_RIGHT_1",
    "CAM_VERTICAL_RIGHT_2",
    "CAM_J14_J13",
    "CAM_COL3_VERTICAL",
    "CAM_J21_J29",
};'''

new = '''LIVE_TRAFFIC_CAMERA_IDS = {
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
};'''

content = content.replace(old, new)

with open('main.py', 'w') as f:
    f.write(content)

print('Backend updated - removed CAM_COL3_VERTICAL')