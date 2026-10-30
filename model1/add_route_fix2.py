import re

with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Find the exact location and replace
old_text = '''    print("\\nTraffic state saved to:")
    print(traffic_json)

    leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = (

        select_hospital_and_build_route(

            graph,

            args.station,

            args.pickup,

            hospital_data_file,

            publisher,

        )

    )'''

new_text = '''    print("\\nTraffic state saved to:")
    print(traffic_json)

    # Apply initial traffic scores to graph BEFORE computing initial route
    # so that the ambulance uses traffic-aware routing from the start
    manager.apply_to_graph(graph)

    leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = (

        select_hospital_and_build_route(

            graph,

            args.station,

            args.pickup,

            hospital_data_file,

            publisher,

        )'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('ai_emergency_demo.py', 'w') as f:
        f.write(content)
    print('Successfully added manager.apply_to_graph(graph) before select_hospital_and_build_route')
else:
    print('Could not find the target text')
    # Let's find what we have
    idx = content.find('print("\\nTraffic state saved to:")')
    if idx >= 0:
        print('Found at index:', idx)
        print(repr(content[idx:idx+200]))

import re
pattern = re.compile(r'print\("Traffic state saved to:"\)\s*print\(traffic_json\)\s*leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = \(', re.DOTALL)
if pattern.search(content):
    print('Pattern found!')
else:
    print('Pattern not found')