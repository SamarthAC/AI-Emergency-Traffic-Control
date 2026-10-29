# Fix the trailing comma on the REALTIME_PHASE_FALLBACKS closing

with open('ai_emergency_demo.py', 'r') as f:
    lines = f.readlines()

# Line 159 (0-indexed: 158) has "},\n" which should be "}\n"
lines[158] = '}\n'

with open('ai_emergency_demo.py', 'w') as f:
    f.writelines(lines)

print('Fixed trailing comma on REALTIME_PHASE_FALLBACKS')