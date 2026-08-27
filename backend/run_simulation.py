import traci

SUMO_BINARY = "sumo-gui"

SUMO_CONFIG = r"..\simulation\config\config.sumocfg"

traci.start([
    SUMO_BINARY,
    "-c",
    SUMO_CONFIG
])

print("Connected to SUMO!")

while traci.simulation.getMinExpectedNumber() > 0:

    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()

    print("Vehicles:", len(vehicles))

    for vehicle_id in vehicles:

        position = traci.vehicle.getPosition(vehicle_id)

        speed = traci.vehicle.getSpeed(vehicle_id)

        road = traci.vehicle.getRoadID(vehicle_id)

        print(
            vehicle_id,
            "Road:", road,
            "Position:", position,
            "Speed:", round(speed, 2)
        )

traci.close()

print("Simulation finished.")