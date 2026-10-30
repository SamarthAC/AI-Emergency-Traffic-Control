import { create } from 'zustand'
import {
  AmbulanceState,
  RouteData,
  HospitalSelection,
  TrafficCameraData,
  SignalState,
  GreenCorridorStatus,
  JunctionCameraDetection,
  EmergencyMetrics,
  LogEntry,
  DashboardStateSnapshot,
  WebSocketEvent,
  ConnectionStatus,
  CorridorSignalState
} from '../types/dashboard'
import {
  sumoToSvg,
  getJunctionSvgPos,
  SvgPoint
} from '../utils/coordinateTransform'

interface DashboardStore {
  // Data State
  ambulance: AmbulanceState
  route: RouteData
  hospital: HospitalSelection
  traffic: Record<string, TrafficCameraData>
  signals: Record<string, SignalState>
  corridor: GreenCorridorStatus
  junction_cameras: Record<string, JunctionCameraDetection>
  vehicles: Record<string, Record<string, unknown>>
  metrics: EmergencyMetrics
  logs: LogEntry[]

  // Pickup Replan Transition State
  latestPickupReplan: RouteData | null
  replanBannerDismissed: boolean

  // Connection & System State
  connectionStatus: ConnectionStatus
  lastUpdated: string | null
  hasReceivedInitialState: boolean

  // Visual & Smooth Position Engine
  ambulanceVisualPos: SvgPoint & { angle: number }
  lastAmbulanceCoord: { x: number; y: number } | null

  // UI Interactive State
  selectedCameraId: string | null
  selectedJunctionId: string | null
  isVisionModalOpen: boolean
  activeVisionTab: 'traffic' | 'ambulance'
  isPresentationMode: boolean
  lastVisionEventTime: number | null

  // Demo Mode & Comparison
  demoMode: 'WITH_CORRIDOR' | 'WITHOUT_CORRIDOR'
  baselineRun: EmergencyMetrics | null
  corridorRun: EmergencyMetrics | null
  preemptedJunctions: Set<string>
  uploadStatus: Record<
    string,
    'IDLE' | 'UPLOADING' | 'WAITING_CNN' | 'CNN_COMPLETE' | 'ROUTE_UPDATED'
  >
  cameraProcessingState: Record<
    string,
    | 'IDLE'
    | 'UPLOADING'
    | 'FRAME_UPDATED'
    | 'WAITING_CNN'
    | 'CNN_PROCESSING'
    | 'ANALYSIS_COMPLETE'
  >

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void
  setSelectedCameraId: (id: string | null) => void
  setSelectedJunctionId: (id: string | null) => void
  setIsVisionModalOpen: (open: boolean) => void
  setActiveVisionTab: (tab: 'traffic' | 'ambulance') => void
  setIsPresentationMode: (val: boolean) => void
  setDemoMode: (mode: 'WITH_CORRIDOR' | 'WITHOUT_CORRIDOR') => void
  saveAsBaselineRun: () => void
  saveAsCorridorRun: () => void
  clearComparisonRuns: () => void
  clearLogs: () => void
  setCameraUploadStatus: (
    cameraId: string,
    status:
      | 'IDLE'
      | 'UPLOADING'
      | 'WAITING_CNN'
      | 'CNN_COMPLETE'
      | 'ROUTE_UPDATED'
  ) => void
  setCameraProcessingState: (
    cameraId: string,
    state:
      | 'IDLE'
      | 'UPLOADING'
      | 'FRAME_UPDATED'
      | 'WAITING_CNN'
      | 'CNN_PROCESSING'
      | 'ANALYSIS_COMPLETE'
  ) => void
  dismissPickupReplan: () => void
  hydrateState: (snapshot: DashboardStateSnapshot) => void
  dispatchWsEvent: (event: WebSocketEvent) => void
  updateAmbulanceVisualPos: (pos: SvgPoint & { angle: number }) => void
  resetDashboard: () => void
  // Derived signal state computation
  computeCorridorSignalStates: () => void
}

const initialStationPos = getJunctionSvgPos('J01')

function getStoredRun (key: string): EmergencyMetrics | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function storeRun (key: string, run: EmergencyMetrics | null) {
  try {
    if (run) {
      localStorage.setItem(key, JSON.stringify(run))
    } else {
      localStorage.removeItem(key)
    }
  } catch (err) {
    console.error('LocalStorage write failed:', err)
  }
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  // Data
  ambulance: {},
  route: {},
  hospital: {},
  traffic: {},
  signals: {},
  corridor: {},
  junction_cameras: {},
  vehicles: {},
  metrics: {},
  logs: [],

  // Pickup Replan
  latestPickupReplan: null,
  replanBannerDismissed: false,

  // Connection
  connectionStatus: 'CONNECTING',
  lastUpdated: null,
  hasReceivedInitialState: false,

  // Ambulance Visuals
  ambulanceVisualPos: { ...initialStationPos, angle: 90 },
  lastAmbulanceCoord: null,

  // UI State
  selectedCameraId: 'CAM_HOSPITAL_DIRECT_2',
  selectedJunctionId: null,
  isVisionModalOpen: false,
  activeVisionTab: 'traffic',
  isPresentationMode: false,
  lastVisionEventTime: null,

  // Demo Mode & Persistent Comparison Runs
  demoMode: 'WITH_CORRIDOR',
  baselineRun: getStoredRun('smart_ambulance_baseline_run'),
  corridorRun: getStoredRun('smart_ambulance_corridor_run'),
  preemptedJunctions: new Set<string>(),
  uploadStatus: {},
  cameraProcessingState: {},

  setConnectionStatus: status => set({ connectionStatus: status }),
  setSelectedCameraId: id => set({ selectedCameraId: id }),
  setSelectedJunctionId: id => set({ selectedJunctionId: id }),
  setIsVisionModalOpen: open => set({ isVisionModalOpen: open }),
  setActiveVisionTab: tab => set({ activeVisionTab: tab }),
  setIsPresentationMode: val => set({ isPresentationMode: val }),
  setDemoMode: mode => set({ demoMode: mode }),

  saveAsBaselineRun: () => {
    const { metrics, ambulance, preemptedJunctions } = get()
    const runToSave: EmergencyMetrics = {
      ...metrics,
      signals_preempted: preemptedJunctions.size,
      saved_at: new Date().toLocaleTimeString(),
      ambulance_id: ambulance.id || 'AI_AMB_001'
    }
    storeRun('smart_ambulance_baseline_run', runToSave)
    set({ baselineRun: runToSave })
  },

  saveAsCorridorRun: () => {
    const { metrics, ambulance, preemptedJunctions } = get()
    const runToSave: EmergencyMetrics = {
      ...metrics,
      signals_preempted: preemptedJunctions.size,
      saved_at: new Date().toLocaleTimeString(),
      ambulance_id: ambulance.id || 'AI_AMB_001'
    }
    storeRun('smart_ambulance_corridor_run', runToSave)
    set({ corridorRun: runToSave })
  },

  clearComparisonRuns: () => {
    storeRun('smart_ambulance_baseline_run', null)
    storeRun('smart_ambulance_corridor_run', null)
    set({ baselineRun: null, corridorRun: null })
  },

  clearLogs: () => {
    set({ logs: [] })
  },

  setCameraUploadStatus: (cameraId, status) => {
    set(state => ({
      uploadStatus: {
        ...state.uploadStatus,
        [cameraId]: status
      }
    }))
  },

  setCameraProcessingState: (cameraId, state) => {
    set(st => ({
      cameraProcessingState: {
        ...st.cameraProcessingState,
        [cameraId]: state
      }
    }))
  },

  updateAmbulanceVisualPos: pos => set({ ambulanceVisualPos: pos }),
  dismissPickupReplan: () => set({ replanBannerDismissed: true }),

  resetDashboard: () => {
    set({
      ambulance: {},
      route: {},
      hospital: {},
      traffic: {},
      signals: {},
      corridor: {},
      junction_cameras: {},
      vehicles: {},
      metrics: {},
      logs: [],
      latestPickupReplan: null,
      replanBannerDismissed: false,
      hasReceivedInitialState: false,
      lastAmbulanceCoord: null,
      ambulanceVisualPos: { ...initialStationPos, angle: 90 },
      preemptedJunctions: new Set<string>(),
      uploadStatus: {},
      cameraProcessingState: {},
      lastUpdated: new Date().toISOString()
    })
  },

  hydrateState: snapshot => {
    if (!snapshot) return

    let visualPos = get().ambulanceVisualPos
    let lastCoord = get().lastAmbulanceCoord

    if (
      snapshot.ambulance &&
      typeof snapshot.ambulance.x === 'number' &&
      typeof snapshot.ambulance.y === 'number'
    ) {
      const targetSvg = sumoToSvg(snapshot.ambulance.x, snapshot.ambulance.y)
      let angle = visualPos.angle
      if (lastCoord) {
        const dx = targetSvg.x - lastCoord.x
        const dy = targetSvg.y - lastCoord.y
        if (Math.hypot(dx, dy) > 0.5) {
          angle = (Math.atan2(dy, dx) * 180) / Math.PI
        }
      }
      visualPos = { ...targetSvg, angle }
      lastCoord = targetSvg
    }

    const routeData = snapshot.route || {}
    let pickupReplan = get().latestPickupReplan
    if (
      routeData.route_stage === 'PICKUP_REPLAN' ||
      routeData.replan_type === 'PICKUP_TRANSITION'
    ) {
      pickupReplan = routeData
    }

    set({
      ambulance: snapshot.ambulance || {},
      route: routeData,
      hospital: snapshot.hospital || {},
      traffic: snapshot.traffic || {},
      signals: snapshot.signals || {},
      corridor: snapshot.corridor || {},
      junction_cameras: snapshot.junction_cameras || {},
      vehicles: snapshot.vehicles || {},
      metrics: snapshot.metrics || {},
      logs: snapshot.logs || [],
      latestPickupReplan: pickupReplan,
      ambulanceVisualPos: visualPos,
      lastAmbulanceCoord: lastCoord,
      hasReceivedInitialState: true,
      lastUpdated: new Date().toISOString()
    })
  },

  // Central Single Event Dispatcher
  dispatchWsEvent: event => {
    if (!event || !event.type) return
    const now = new Date().toISOString()

    switch (event.type) {
      case 'STATE_SNAPSHOT': {
        get().hydrateState(event.data)
        break
      }

      case 'AMBULANCE_STATUS': {
        const currentAmb = get().ambulance
        const currentRoute = get().route
        const newAmb = { ...currentAmb, ...event.data }

        const updatedRoute = { ...currentRoute }
        const statusUpper = String(event.data.status || '').toUpperCase()
        const pickupReached = Boolean(event.data.pickup_reached)

        if (
          pickupReached ||
          statusUpper === 'EN_ROUTE_TO_HOSPITAL' ||
          statusUpper === 'PICKUP_REACHED'
        ) {
          updatedRoute.pickup_reached = true
          updatedRoute.route_stage = 'POST_PICKUP'
        }

        if (statusUpper === 'ARRIVED') {
          updatedRoute.pickup_reached = true
          updatedRoute.route_stage = 'ARRIVED'
        }

        set({
          ambulance: newAmb,
          route: updatedRoute,
          lastUpdated: now
        })
        break
      }

      case 'AI_ROUTE': {
        const routeData = event.data
        const isPickupReplan =
          routeData.route_stage === 'PICKUP_REPLAN' ||
          routeData.replan_type === 'PICKUP_TRANSITION'

        set(state => {
          // If a camera was in CNN_COMPLETE and route changed, transition to ROUTE_UPDATED
          const updatedUploadStatus = { ...state.uploadStatus }
          if (routeData.rerouted || isPickupReplan) {
            for (const camId of Object.keys(updatedUploadStatus)) {
              if (updatedUploadStatus[camId] === 'CNN_COMPLETE') {
                updatedUploadStatus[camId] = 'ROUTE_UPDATED'
              }
            }
          }

          return {
            route: routeData,
            latestPickupReplan: isPickupReplan
              ? routeData
              : state.latestPickupReplan,
            replanBannerDismissed: isPickupReplan
              ? false
              : state.replanBannerDismissed,
            uploadStatus: updatedUploadStatus,
            lastUpdated: now
          }
        })

        // Recompute corridor signal states after route change
        setTimeout(() => get().computeCorridorSignalStates(), 0)
        break
      }

      case 'HOSPITAL_SELECTION': {
        set({
          hospital: event.data,
          lastUpdated: now
        })
        break
      }

      case 'TRAFFIC_OVERVIEW': {
        const data = event.data

        const cameraId = data.camera_id

        if (!cameraId) {
          console.warn('TRAFFIC_OVERVIEW received without camera_id:', data)
          break
        }

        set(state => {
          const updatedUpload = { ...state.uploadStatus }

          if (updatedUpload[cameraId] === 'WAITING_CNN') {
            updatedUpload[cameraId] = 'CNN_COMPLETE'
          }

          return {
            traffic: {
              ...state.traffic,
              [cameraId]: {
                ...(state.traffic[cameraId] || {}),
                ...data
              }
            },
            uploadStatus: updatedUpload,
            lastUpdated: now
          }
        })

        break
      }

      case 'SIGNAL_UPDATE': {
        const data = event.data
        if (data && data.junction_id) {
          const jId = String(data.junction_id)
          const isGreen = Boolean(data.green_corridor_active)

          set(state => {
            const nextPreempted = new Set(state.preemptedJunctions)
            if (isGreen) {
              nextPreempted.add(jId)
            }

            return {
              signals: {
                ...state.signals,
                [jId]: {
                  ...data,
                  green_corridor_active: isGreen,
                  state:
                    data.state || (isGreen ? 'GREEN_CORRIDOR_ACTIVE' : 'NORMAL')
                }
              },
              preemptedJunctions: nextPreempted,
              lastUpdated: now
            }
          })

          // Recompute corridor signal states after signal update
          setTimeout(() => get().computeCorridorSignalStates(), 0)
        }
        break
      }

      case 'GREEN_CORRIDOR_STATUS': {
        set(state => ({
          corridor: {
            ...state.corridor,
            ...event.data
          },
          lastUpdated: now
        }))

        // Recompute corridor signal states after corridor status update
        setTimeout(() => get().computeCorridorSignalStates(), 0)
        break
      }

      case 'JUNCTION_CAMERA_DETECTION': {
        const data = event.data
        const key = data.junction_id || data.camera_id
        if (key) {
          set(state => ({
            junction_cameras: {
              ...state.junction_cameras,
              [String(key)]: data
            },
            lastVisionEventTime: Date.now(),
            lastUpdated: now
          }))
        }
        break
      }

      case 'VEHICLE_UPDATE': {
        const data = event.data
        const vehicleId = data.vehicle_id as string
        if (!vehicleId) return

        set(state => {
          const newVehicles = {
            ...state.vehicles,
            [vehicleId]: data
          }

          if (vehicleId === 'AI_AMB_001') {
            const currentAmb = state.ambulance
            const updatedAmb = {
              ...currentAmb,
              id: vehicleId,
              edge_id: data.edge_id as string,
              lane_id: data.lane_id as string,
              route_index: data.route_index as number,
              route_length: data.route_length as number,
              speed_kmh: data.speed_kmh as number,
              x: data.x as number,
              y: data.y as number,
              simulation_time: data.simulation_time as number
            }

            let visualPos = state.ambulanceVisualPos
            let lastCoord = state.lastAmbulanceCoord

            if (typeof data.x === 'number' && typeof data.y === 'number') {
              const targetSvg = sumoToSvg(data.x, data.y)
              let angle = visualPos.angle
              if (lastCoord) {
                const dx = targetSvg.x - lastCoord.x
                const dy = targetSvg.y - lastCoord.y
                if (Math.hypot(dx, dy) > 0.5) {
                  angle = (Math.atan2(dy, dx) * 180) / Math.PI
                }
              }
              visualPos = { ...targetSvg, angle }
              lastCoord = targetSvg
            }

            return {
              vehicles: newVehicles,
              ambulance: updatedAmb,
              ambulanceVisualPos: visualPos,
              lastAmbulanceCoord: lastCoord,
              lastUpdated: now
            }
          }

          return {
            vehicles: newVehicles,
            lastUpdated: now
          }
        })

        // Recompute corridor signal states when ambulance moves
        if (vehicleId === 'AI_AMB_001') {
          setTimeout(() => get().computeCorridorSignalStates(), 0)
        }
        break
      }

      case 'EMERGENCY_METRICS': {
        const metricsData = event.data
        const preemptedCount =
          metricsData.signals_preempted ?? get().preemptedJunctions.size
        set({
          metrics: {
            ...metricsData,
            signals_preempted: preemptedCount
          },
          lastUpdated: now
        })
        break
      }

      case 'LOG': {
        set(state => ({
          logs: [...state.logs.slice(-199), event.data],
          lastUpdated: now
        }))
        break
      }

      default:
        console.warn(
          'Unhandled WebSocket event type:',
          (event as { type: string }).type
        )
    }
  },

  // Derive corridor signal states for visualization
  computeCorridorSignalStates: () => {
    const { signals, corridor, ambulance, route } = get()
    if (!corridor.armed) {
      // Reset all signals to NORMAL when corridor not armed
      set(state => {
        const updatedSignals = { ...state.signals }
        let changed = false
        for (const jId of Object.keys(updatedSignals)) {
          if (
            updatedSignals[jId].corridor_signal_state &&
            updatedSignals[jId].corridor_signal_state !== 'NORMAL'
          ) {
            updatedSignals[jId] = {
              ...updatedSignals[jId],
              corridor_signal_state: 'NORMAL'
            }
            changed = true
          }
        }
        if (changed) {
          return { signals: updatedSignals }
        }
        return {}
      })
      return
    }

    // Get the route signal sequence from the active route
    const routeEdges = route?.route || []
    if (routeEdges.length < 2) return

    // Build the signal sequence for the current route
    const signalSequence: Array<{
      junctionId: string
      routeIndex: number
      distance: number
    }> = []

    // We need to know which junctions on the route have signals
    // This is derived from the route edges and the edge_nodes mapping
    // For now, we'll use the signals that have green_corridor_active or are in the lookahead

    const lookaheadSignals = corridor.lookahead_signals || 2
    const lookaheadDistance = corridor.lookahead_distance_m || 900

    // Get currently active signal (where green_corridor_active is true)
    const activeJunctionId = Object.keys(signals).find(
      jId => signals[jId]?.green_corridor_active === true
    )

    // Get all route signals in order
    const routeSignalJunctions = Object.entries(signals)
      .filter(([_, sig]) => sig.incoming_edge && sig.outgoing_edge)
      .map(([jId, sig]) => ({
        junctionId: jId,
        routeIndex: sig.incoming_route_index ?? 0,
        distance: sig.distance_to_signal_m ?? Infinity
      }))
      .sort((a, b) => a.routeIndex - b.routeIndex)

    if (routeSignalJunctions.length === 0) return

    // Find the ambulance's current route index
    const currentRouteIndex = ambulance.route_index ?? 0

    // Derive states for each signal
    set(state => {
      const updatedSignals = { ...state.signals }
      let changed = false

      for (let i = 0; i < routeSignalJunctions.length; i++) {
        const { junctionId, routeIndex, distance } = routeSignalJunctions[i]
        const sig = updatedSignals[junctionId]
        if (!sig) continue

        let newState: CorridorSignalState = 'NORMAL'

        if (junctionId === activeJunctionId) {
          newState = 'ACTIVE'
        } else if (routeIndex < currentRouteIndex) {
          // Signal already passed
          newState = 'PASSED'
        } else if (
          routeIndex === currentRouteIndex &&
          junctionId !== activeJunctionId
        ) {
          // Next signal the ambulance is approaching
          newState = 'PRIORITY'
        } else if (i < lookaheadSignals && distance <= lookaheadDistance) {
          // Within lookahead window
          newState = 'UPCOMING'
        } else if (
          sig.green_corridor_active === false &&
          state.preemptedJunctions.has(junctionId)
        ) {
          // Was preempted but now restored
          newState = 'RESTORED'
        }

        if (sig.corridor_signal_state !== newState) {
          updatedSignals[junctionId] = {
            ...sig,
            corridor_signal_state: newState
          }
          changed = true
        }
      }

      if (changed) {
        return { signals: updatedSignals }
      }
      return {}
    })
  }
}))
