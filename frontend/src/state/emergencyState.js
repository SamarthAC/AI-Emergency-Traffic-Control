import { useCallback, useRef, useState } from 'react'
import * as api from '../services/api.js'

export const PHASE = {
  IDLE: 'IDLE',
  EMERGENCY: 'EMERGENCY',
  DISPATCHED: 'DISPATCHED',
  PATIENT_PICKUP: 'PATIENT_PICKUP',
  TRAFFIC_ANALYSIS: 'TRAFFIC_ANALYSIS',
  ROUTE_OPTIMIZATION: 'ROUTE_OPTIMIZATION',
  HOSPITAL_SELECTION: 'HOSPITAL_SELECTION',
  GREEN_CORRIDOR: 'GREEN_CORRIDOR',
  EN_ROUTE: 'EN_ROUTE',
  ARRIVAL: 'ARRIVAL',
  COMPLETED: 'COMPLETED',
}

// Maps internal phases -> the 6 bottom workflow steps from the original UI
const WORKFLOW_STEPS = [
  { key: 'emergency', label: 'Emergency', phases: [PHASE.EMERGENCY] },
  { key: 'dispatch', label: 'Dispatch', phases: [PHASE.DISPATCHED] },
  { key: 'pickup', label: 'Patient Pickup', phases: [PHASE.PATIENT_PICKUP] },
  {
    key: 'hospital',
    label: 'Hospital Selection',
    phases: [PHASE.TRAFFIC_ANALYSIS, PHASE.ROUTE_OPTIMIZATION, PHASE.HOSPITAL_SELECTION],
  },
  { key: 'corridor', label: 'Green Corridor', phases: [PHASE.GREEN_CORRIDOR, PHASE.EN_ROUTE] },
  { key: 'arrival', label: 'Arrival', phases: [PHASE.ARRIVAL, PHASE.COMPLETED] },
]

const ROAD_IDS = ['A', 'B', 'C']

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

let feedCounter = 0

export function useEmergencyState() {
  const [phase, setPhase] = useState(PHASE.IDLE)
  const [priority, setPriority] = useState(null)
  const [ambulanceId] = useState('AMB-07')
  const [ambulanceStatus, setAmbulanceStatus] = useState('STANDBY')
  const [eta, setEta] = useState('--:--')
  const [feed, setFeed] = useState([])
  const [roads, setRoads] = useState({
    A: { status: 'idle', data: null },
    B: { status: 'idle', data: null },
    C: { status: 'idle', data: null },
  })
  const [recommendation, setRecommendation] = useState(null)
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [hospitals, setHospitals] = useState(null)
  const [corridor, setCorridor] = useState({ active: false, junctions: [] })
  const [ambulanceProgress, setAmbulanceProgress] = useState(0)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const animationRef = useRef(null)

  const pushFeed = useCallback((text) => {
    feedCounter += 1
    setFeed((prev) => [
      { id: feedCounter, text, time: new Date().toLocaleTimeString('en-IN', { hour12: false }) },
      ...prev,
    ].slice(0, 40))
  }, [])

  // ---------------------------------------------------------------------
  // STEP 1-3: Emergency -> Dispatch -> Patient Pickup (auto-paced)
  // ---------------------------------------------------------------------
  const startEmergency = useCallback(async () => {
    setError(null)
    setPhase(PHASE.EMERGENCY)
    setPriority('LEVEL 1')
    setAmbulanceStatus('EMERGENCY RECEIVED')
    setEta('--:--')
    pushFeed('Emergency request received — Accident / Level 1')

    await sleep(900)
    setPhase(PHASE.DISPATCHED)
    setAmbulanceStatus('DISPATCHED')
    pushFeed(`${ambulanceId} dispatched to patient location`)

    await sleep(1100)
    setPhase(PHASE.PATIENT_PICKUP)
    setAmbulanceStatus('PATIENT PICKUP')
    pushFeed('Patient onboard — proceeding to hospital selection')
  }, [ambulanceId, pushFeed])

  // ---------------------------------------------------------------------
  // STEP 4: AI Traffic Analysis — BMD-45 image -> YOLO -> traffic score
  // ---------------------------------------------------------------------
  const runTrafficAnalysis = useCallback(async () => {
    setError(null)
    setBusy(true)
    setPhase(PHASE.TRAFFIC_ANALYSIS)
    pushFeed('BMD-45 traffic images loaded')
    pushFeed('YOLO traffic analysis started')

    setRoads({
      A: { status: 'analyzing', data: null },
      B: { status: 'analyzing', data: null },
      C: { status: 'analyzing', data: null },
    })

    try {
      const results = {}
      for (const roadId of ROAD_IDS) {
        // sequential on purpose: lets the UI visibly show each road being
        // analyzed one at a time, matching the brief's demo sequence.
        // eslint-disable-next-line no-await-in-loop
        const data = await api.analyzeTraffic(roadId)
        results[roadId] = data
        setRoads((prev) => ({ ...prev, [roadId]: { status: 'done', data } }))
        pushFeed(`Road ${roadId} analyzed — ${data.trafficLevel} traffic (score ${data.trafficScore})`)
        // eslint-disable-next-line no-await-in-loop
        await sleep(250)
      }

      setPhase(PHASE.ROUTE_OPTIMIZATION)
      pushFeed('Weighted route optimization started')

      const roadPayload = ROAD_IDS.map((id) => ({ id, trafficScore: results[id].trafficScore }))
      const routeResult = await api.optimizeRoute(roadPayload)
      setRecommendation(routeResult)
      setSelectedRoute(routeResult.recommendedRoute)
      pushFeed(`Route ${routeResult.recommendedRoute} selected — ${routeResult.reason}`)
      setPhase(PHASE.HOSPITAL_SELECTION)
    } catch (err) {
      setError(err.message || 'Traffic analysis failed')
      pushFeed(`ERROR — ${err.message || 'traffic analysis failed'}`)
    } finally {
      setBusy(false)
    }
  }, [pushFeed])

  // ---------------------------------------------------------------------
  // STEP 6: Hospital Selection
  // ---------------------------------------------------------------------
  const selectBestHospital = useCallback(async () => {
    if (!recommendation || !selectedRoute) return
    setError(null)
    setBusy(true)
    try {
      const chosenRoute = recommendation.routes.find((r) => r.id === selectedRoute)
      const data = await api.getHospitals(chosenRoute?.edgeCost ?? 0, chosenRoute?.trafficScore ?? 0)
      setHospitals(data.hospitals)
      pushFeed('Hospital availability synchronized')
      const best = data.hospitals.find((h) => h.bestMatch)
      if (best) pushFeed(`${best.name} selected — HOSPITAL SELECTED ✓`)

      // Immediately proceed into green corridor planning, per the brief's
      // Step 7 sequence.
      pushFeed('Green corridor planning started')
      const corridorResult = await api.activateGreenCorridor(selectedRoute)
      setCorridor({ active: true, junctions: corridorResult.junctions })
      setPhase(PHASE.GREEN_CORRIDOR)

      for (const junction of corridorResult.junctions) {
        // eslint-disable-next-line no-await-in-loop
        await sleep(350)
        pushFeed(`${junction} signal priority activated`)
      }

      setPhase(PHASE.EN_ROUTE)
      pushFeed(`${ambulanceId} proceeding through green corridor`)
      setAmbulanceStatus('EN ROUTE')
      if (chosenRoute) setEta(`${Math.ceil(chosenRoute.etaMinutes)} MIN`)

      await animateAmbulance()
      pushFeed(`${ambulanceId} approaching selected hospital`)
    } catch (err) {
      setError(err.message || 'Hospital selection failed')
      pushFeed(`ERROR — ${err.message || 'hospital selection failed'}`)
    } finally {
      setBusy(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recommendation, selectedRoute, ambulanceId, pushFeed])

  const animateAmbulance = useCallback(() => {
    return new Promise((resolve) => {
      const durationMs = 2600
      const start = performance.now()
      const step = (now) => {
        const t = Math.min(1, (now - start) / durationMs)
        setAmbulanceProgress(t)
        if (t < 1) {
          animationRef.current = requestAnimationFrame(step)
        } else {
          resolve()
        }
      }
      animationRef.current = requestAnimationFrame(step)
    })
  }, [])

  // ---------------------------------------------------------------------
  // STEP 8: Arrival
  // ---------------------------------------------------------------------
  const completeArrival = useCallback(() => {
    setPhase(PHASE.COMPLETED)
    setAmbulanceStatus('ARRIVED')
    setEta('00:00')
    setCorridor((prev) => ({ ...prev, active: false }))
    pushFeed(`${ambulanceId} arrived at selected hospital`)
    pushFeed('Emergency response completed')
    pushFeed('Green corridor released')
  }, [ambulanceId, pushFeed])

  const reset = useCallback(() => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current)
    setPhase(PHASE.IDLE)
    setPriority(null)
    setAmbulanceStatus('STANDBY')
    setEta('--:--')
    setFeed([])
    setRoads({
      A: { status: 'idle', data: null },
      B: { status: 'idle', data: null },
      C: { status: 'idle', data: null },
    })
    setRecommendation(null)
    setSelectedRoute(null)
    setHospitals(null)
    setCorridor({ active: false, junctions: [] })
    setAmbulanceProgress(0)
    setError(null)
    setBusy(false)
  }, [])

  const activeStepIndex = WORKFLOW_STEPS.findIndex((step) => step.phases.includes(phase))
  const workflowStatus = WORKFLOW_STEPS.map((step, idx) => ({
    ...step,
    state:
      phase === PHASE.IDLE
        ? 'pending'
        : idx < activeStepIndex
        ? 'done'
        : idx === activeStepIndex
        ? 'active'
        : phase === PHASE.COMPLETED
        ? 'done'
        : 'pending',
  }))

  return {
    phase,
    priority,
    ambulanceId,
    ambulanceStatus,
    eta,
    feed,
    roads,
    recommendation,
    selectedRoute,
    hospitals,
    corridor,
    ambulanceProgress,
    error,
    busy,
    workflowStatus,
    actions: {
      startEmergency,
      runTrafficAnalysis,
      selectBestHospital,
      completeArrival,
      reset,
    },
  }
}
