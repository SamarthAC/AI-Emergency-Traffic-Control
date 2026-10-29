# Fix the duplicate phase_2 section in ai_emergency_demo.py

with open('ai_emergency_demo.py', 'r') as f:
    lines = f.readlines()

# Find the line numbers to remove
# We need to remove lines 160-191 (0-indexed: 159-190)
# That's the duplicate "phase_2" section and extra closing braces

# Keep lines 0-159 (up to the correct closing of REALTIME_PHASE_FALLBACKS)
# Then skip lines 160-191 (the duplicate)
# Then continue from line 192 onwards

new_lines = lines[:160] + lines[192:]

with open('ai_emergency_demo.py', 'w') as f:
    f.writelines(new_lines)

print('Fixed duplicate phase_2 section')