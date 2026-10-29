import re

with open('main.py', 'r') as f:
    content = f.read()

# Replace CAM_J11_J29 with CAM_COL3_VERTICAL
content = content.replace('"CAM_J11_J29"', '"CAM_COL3_VERTICAL"')

with open('main.py', 'w') as f:
    f.write(content)

print('Backend updated')