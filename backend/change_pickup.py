import re

with open('main.py', 'r') as f:
    content = f.read()

# Change default pickup from J23 to J10
content = content.replace('parser.add_argument("--pickup", default="J23")', 'parser.add_argument("--pickup", default="J10")')

with open('main.py', 'w') as f:
    f.write(content)

print('Backend pickup changed to J10')