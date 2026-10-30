with open('ai_emergency_demo.py', 'r') as f:
    lines = f.readlines()

# Find the line where "leg1, leg2, full_route" starts
target_line = -1
for i, line in enumerate(lines):
    if 'leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = (' in line:
        target_line = i
        break

if target_line >= 0:
    # Insert the new lines before this line
    # We need to insert after the empty line after print(traffic_json)
    # The empty line is at index 3789 (0-indexed: 3788)
    # We'll insert at index 3790 (after the empty line, before the leg1 line)
    
    new_lines = [
        '    # Apply initial traffic scores to graph BEFORE computing initial route\n',
        '    # so that the ambulance uses traffic-aware routing from the start\n',
        '    manager.apply_to_graph(graph)\n',
        '\n'
    ]
    
    # Insert at line 3790 (0-indexed: 3789)
    lines[3790:3790] = new_lines
    
    with open('ai_emergency_demo.py', 'w') as f:
        f.writelines(lines)
    
    print('Successfully inserted manager.apply_to_graph(graph) before select_hospital_and_build_route')
else:
    print('Could not find target line')