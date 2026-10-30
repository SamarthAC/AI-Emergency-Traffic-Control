# Fix the trailing comma that makes REALTIME_PHASE_FALLBACKS a tuple

with open('ai_emergency_demo.py', 'r') as f:
    lines = f.readlines()

# Line 159 (0-indexed: 158) has "},\n" which should be "}\n" (no trailing comma)
# This is the closing brace of REALTIME_PHASE_FALLBACKS dict

# Find the line with just "},\n" after the phase_2 closing
for i, line in enumerate(lines):
    if line.strip() == '},' and i > 155 and i < 165:
        print(f'Found trailing comma at line {i+1}: {repr(line)}')
        lines[i] = '}\n'
        break

with open('ai_emergency_demo.py', 'w') as f:
    f.writelines(lines)

print('Fixed trailing comma')