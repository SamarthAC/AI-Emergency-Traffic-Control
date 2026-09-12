from hospital_selector import HospitalSelector

class FakeGraph:
    def __init__(self, costs):
        self.costs = costs

    def astar(self, start, end):
        if end not in self.costs:
            return None
        cost = self.costs[end]
        return {
            "junction_path": [start, end],
            "edge_path": [f"{start}_{end}"],
            "distance_m": cost * 8.0,
            "base_travel_time_s": cost * 0.75,
            "dynamic_cost_s": float(cost),
        }

def run_case(title, costs):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)

    selector = HospitalSelector.from_json("hospital_data.json")
    result = selector.select(FakeGraph(costs), "J23")

    for c in result["candidates"]:
        print(
            f"{c['name']:20s} eligible={str(c['eligible']):5s} "
            f"beds={c['beds_available']} doctors={c['doctors_available']} "
            f"route_cost={c['dynamic_cost_s']}"
        )

    selected = result["selected_hospital"]
    print("\nSELECTED:", selected["name"], "at", selected["junction_id"])
    print("REASON  :", result["selection_reason"])

run_case(
    "CASE 1 - Main Hospital route is cheaper",
    {"J47": 280.0, "J45": 360.0},
)

run_case(
    "CASE 2 - Alternate Hospital route is cheaper",
    {"J47": 430.0, "J45": 310.0},
)
