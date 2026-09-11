BENGALURU STRUCTURED SUMO SIMULATION
====================================

Purpose
-------
Synthetic Bengaluru-inspired road network for:
- AI-based smart ambulance routing
- adaptive traffic signal control
- green corridor demonstration
- congestion-aware A* / Dijkstra routing

This is intentionally structured to resemble the approved infographic.
It is NOT an exact geographic copy of Bengaluru.

Network
-------
Junctions: 48
Physical road links: 95
Directed road edges: 190

Key locations
-------------
J01  Ambulance station area
J23  Emergency pickup zone
J45  Alternate hospital
J47  Main hospital

Visual districts
----------------
- Northwest residential area
- West university/mixed-use area
- Central CBD
- East commercial area
- Southwest residential area
- Southeast hospital district
- Eastern ORR-style corridor

Road hierarchy
--------------
local       1 lane, 30 km/h
collector   1 lane, 40 km/h
arterial    2 lanes, 50 km/h
orr         3 lanes, 60 km/h
hospital    1 lane, 35 km/h

Included files
--------------
bengaluru_structured.nod.xml   junctions
bengaluru_structured.edg.xml   roads
bengaluru_structured.typ.xml   road classes
bengaluru_structured.add.xml   zones and POIs
bengaluru_structured.rou.xml   mixed traffic + ambulance
bengaluru_structured.sumocfg   simulation configuration
build_and_run.bat              builds network and launches SUMO-GUI
open_netedit.bat               opens generated net in NETEDIT
README.txt                     this file

How to run
----------
1. Extract everything into:
   simulation\bengaluru_structured\

2. Double-click:
   build_and_run.bat

3. It will create:
   bengaluru_structured.net.xml

4. SUMO-GUI will launch using the config, traffic and additional files.

Notes
-----
- The traffic file already includes cars, bikes, autos, buses, trucks and one ambulance.
- Traffic lights are placed only at major junctions.
- The ORR-style eastern corridor uses 3 lanes per direction.
- Arterials are 2 lanes per direction.
- The network is designed to leave meaningful alternative routes for AI routing.
- Current ambulance trip is only a starter route to the pickup region.
  Dynamic hospital routing / green-corridor control will later be done through TraCI.
