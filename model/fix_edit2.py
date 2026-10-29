with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Fix the broken edit - replace the broken lines
old_text = '''    print(traffic_json)

    leg1, leg2, full_route, selected_hospital, selected_hospital_name, hospital_selection = (
    # Apply initial traffic scores to graph BEFORE computing initial route
    # so that the ambulance uses traffic-aware routing from the start
    manager.apply_to_graph(graph)


        select_hospital_and_build_route(

            graph,

            args.station,

            args.pickup,

            hospital_data_file,

            publisher,

        )

    )'''

new_text = '''    print(traffic_json)

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

        )

    )'''

content = content.replace(old_text, new_text)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Fixed the edit')