with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

content = content.replace('parser.add_argument("--pickup", default="J23")', 'parser.add_argument("--pickup", default="J10")')

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Demo pickup changed to J10')