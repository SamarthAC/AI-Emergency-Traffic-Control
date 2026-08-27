# Smart Ambulance Routing & Adaptive Traffic Signal Control — Frontend

A production-quality **frontend only** for the Final Year Engineering Project.
Runs entirely on mock JSON data today; built so a Python **FastAPI + WebSocket
+ SUMO + AI routing model** backend can be dropped in later with minimal
frontend changes.

No backend, AI/ML, or real data is implemented here — see [Backend
Integration](#backend-integration-later) for exactly what to build next and
how it plugs in.

---

## Tech stack

- React 19 + TypeScript + Vite
- Tailwind CSS (v3) — dark "Smart City Control Center" theme
- Framer Motion — card entrances, pulsing emergency states, animated signal lamps
- Zustand — single application store (`src/store/simulationStore.ts`)
- react-icons — UI iconography
- SVG (not Canvas/Pixi) for the intersection scene — chosen so each vehicle,
  road, and traffic light is a real, inspectable React component, per the
  component list in the brief. The animation engine (`src/utils/pathEngine.ts`)
  is renderer-agnostic, so swapping the intersection to Canvas/PixiJS later
  only means rewriting `Intersection.tsx`/`Road.tsx`/`Vehicle.tsx` — the math
  and state layers are untouched.

## Getting started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build      # production build -> dist/
npm run preview    # serve the production build locally
```

## Project structure

```
src/
  components/
    layout/          Navbar
    dashboard/        TrafficOverview, EmergencyStatus, AIRoutingCard,
                       TrafficSignalCard, VehicleCountCard, SimulationControls,
                       Legend, SystemLogs
    intersection/      Intersection (scene), Road (static geometry)
    trafficlights/      TrafficLight
    vehicles/           Vehicle (dispatcher), Car, Bus, Truck, Bike, Ambulance
    common/             Card, StatRow
  hooks/
    useAnimationFrame.ts     generic RAF hook
    useSimulationLoop.ts     drives store.tick() every frame (today's "engine")
    useSimulationSocket.ts   FUTURE backend hook (no-op until VITE_WS_URL is set)
    useCountUp.ts            animated dashboard numbers
  store/
    simulationStore.ts   Zustand store: vehicles, junction/signals, ambulance,
                          AI routing info, traffic overview, logs, sim controls
  utils/
    pathEngine.ts     pure waypoint-following math (the reusable "animation engine")
    sceneConfig.ts    shared geometry constants (lane positions, junction box)
  types/
    index.ts          all shared TS interfaces + the WebSocket message contract
  data/mock/
    vehicles.json, junction.json, aiRouting.json, trafficOverview.json,
    ambulanceStatus.json, logs.json
```

No component contains hardcoded simulation values — everything flows in as
props derived from `useSimulationStore`, which today is seeded from
`src/data/mock/*.json`.

## How the animation works

`src/utils/pathEngine.ts` is a small set of **pure functions** with no
React/Zustand/DOM dependency:

- `resolvePosition(waypoints, segmentIndex, progress)` → `{x, y, heading}`
- `advanceAlongPath(waypoints, segmentIndex, progress, speed, deltaSeconds)` →
  next `{segmentIndex, progress, position, completed}`

Every vehicle (car, bus, truck, bike, and the ambulance) is just a
`VehicleState` holding an ordered `Waypoint[]` array plus its current segment
index and progress. Each animation frame, `simulationStore.tick(dt)` calls
`advanceAlongPath` for every vehicle and writes the new position back into
the store; `Vehicle.tsx` only ever reads `vehicle.position`/`vehicle.heading`
and draws — it does no motion math itself.

**This is the piece designed to survive backend integration unchanged.**
Today, `Waypoint[]` arrays are hand-authored in `src/data/mock/vehicles.json`
to match the intersection geometry in `src/utils/sceneConfig.ts`. Later, an
AI-predicted shortest path (Dijkstra/A*/ML) computed in SUMO/FastAPI just
needs to be sent down as the same `Waypoint[]` shape — the ambulance will
smoothly follow it with zero changes to rendering or animation code.

## Emergency Mode / Green Corridor

Clicking **Emergency Mode** in the navbar (`toggleEmergency` in the store):

1. Swaps the ambulance's route from its idle `cruiseRoute` to its
   `emergencyRoute` (a longer waypoint array demonstrating a turn),
   raises its speed, and flags `hasPriority`.
2. Forces the traffic signals on the ambulance's approach axis to green and
   the cross-axis to red for the duration of the emergency (overriding the
   normal N-S / E-W adaptive cycle timer).
3. Regular vehicles check the signal for their own approach direction each
   frame and stop at the stop line if it isn't green — including being held
   back by the forced cross-axis red during the emergency.
4. When the ambulance reaches the end of its route, emergency mode clears,
   signals return to the normal adaptive cycle, and logs are appended.

The highlighted cyan route drawn under the ambulance during emergency mode
is rendered directly from the same `emergencyRoute` waypoint array — another
example of one data source driving two things (motion + visualization).

## Backend integration (later)

The exact contract the frontend expects is defined in `src/types/index.ts`:

```ts
type ServerMessage =
  | { type: "VEHICLE_UPDATE"; payload: VehicleState[] }
  | { type: "SIGNAL_UPDATE"; payload: JunctionState }
  | { type: "AMBULANCE_STATUS"; payload: AmbulanceStatus }
  | { type: "AI_ROUTE"; payload: { vehicleId: string; route: Route } }
  | { type: "TRAFFIC_OVERVIEW"; payload: TrafficOverviewStats }
  | { type: "LOG"; payload: LogEntry };
```

To connect a real backend:

1. Set `VITE_WS_URL` in `.env` (see `.env.example`) to your FastAPI WebSocket
   endpoint, e.g. `ws://localhost:8000/ws/simulation`.
2. `src/hooks/useSimulationSocket.ts` will open the connection and parse
   incoming `ServerMessage`s. It currently only wires up the `LOG` case as a
   worked example — add the remaining cases (`VEHICLE_UPDATE`,
   `SIGNAL_UPDATE`, etc.) to call matching setter actions you add to
   `simulationStore.ts` (mirroring the existing `addLog` action).
3. Decide whether the local `useSimulationLoop` RAF tick keeps running for
   client-side interpolation between backend ticks, or is disabled entirely
   in favor of server-authoritative positions — both are compatible with the
   current component tree since components only ever read from the store.
4. On the backend, waypoints for `AI_ROUTE` (Dijkstra/A*/ML-predicted) should
   be emitted in the same scene coordinate system defined in
   `src/utils/sceneConfig.ts` (`SCENE`, `LANES`, `STOP_LINES`), or the backend
   should own coordinate space entirely and this file becomes a
   projection/mapping layer instead of hardcoded constants.

## Notes

- Tailwind is pinned to v3 (not v4) for a conventional `tailwind.config.js`
  workflow that's easy to extend as the project grows.
- `prefers-reduced-motion` is respected globally (see `src/styles/globals.css`).
- The layout is desktop-first with a responsive fallback (dashboard becomes
  scrollable, intersection panel keeps a minimum height) down to tablet widths.
