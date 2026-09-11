BENGALURU-INSPIRED REALISTIC V2
================================
Synthetic city network designed for the AI ambulance-routing project.
It is inspired by Bengaluru road hierarchy, NOT an exact geographic copy.

Scale / topology
- Junctions: 48
- Physical road links: 102
- Directed SUMO edges: 204
- Approx area: 4.3 km x 3.1 km

Important locations
- N01 Ambulance Station
- N23 Emergency Pickup Zone
- N40 Alternate Hospital
- N45 Main Hospital

Design improvements over V1
- Curved road geometry
- Sparse/irregular local roads rather than a uniform mesh
- T-junction-like local topology
- Main arterial corridors
- 3-lane ORR-style eastern bypass
- 2-lane main roads
- 1-lane collectors/residential roads
- Multiple realistic alternative ambulance corridors

Build:
1. Extract all files into simulation\bengaluru_realistic_v2
2. Run build_v2.bat
3. The script builds bengaluru_v2.net.xml and opens NETEDIT.
4. Do NOT open .edg.xml / .nod.xml directly as finished networks.

No traffic/routes are included yet on purpose.
First validate the network visually; then traffic demand will be added.
