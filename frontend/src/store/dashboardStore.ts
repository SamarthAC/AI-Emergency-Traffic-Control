import { create } from 'zustand';
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
} from '../types/dashboard';
import { sumoToSvg, getJunctionSvgPos, SvgPoint } from '../utils/coordinateTransform';

interface DashboardStore {
  // Data State
  ambulance: AmbulanceState;
  route: RouteData;
  hospital: HospitalSelection;
  traffic: Record<string, TrafficCameraData>;
  signals: Record<string, SignalState>;
  corridor: GreenCorridorStatus;
  junction_cameras: Record<string, JunctionCameraDetection>;
  vehicles: Record<string, Record<string, unknown>>;
  metrics: EmergencyMetrics;
  logs: LogEntry[];

  // Pickup Replan Transition State
  latestPickupReplan: RouteData | null;
  replanBannerDismissed: boolean;

  // Connection & System State
  connectionStatus: ConnectionStatus;
  lastUpdated: string | null;
  hasReceivedInitialState: boolean;

  // Visual & Smooth Position Engine
  ambulanceVisualPos: SvgPoint & { angle: number };
  lastAmbulanceCoord: { x: number; y: number } | null;

  // UI Interactive State
  selectedCameraId: string | null;
  selectedJunctionId: string | null;
  isVisionModalOpen: boolean;
  activeVisionTab: 'traffic' | 'ambulance';
  isPresentationMode: boolean;
  lastVisionEventTime: number | null;

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void;
  setSelectedCameraId: (id: string | null) => void;
  setSelectedJunctionId: (id: string | null) => void;
  setIsVisionModalOpen: (open: boolean) => void;
  setActiveVisionTab: (tab: 'traffic' | 'ambulance') => void;
  setIsPresentationMode: (val: boolean) => void;
  dismissPickupReplan: () => void;
  hydrateState: (snapshot: DashboardStateSnapshot) => void;
  dispatchWsEvent: (event: WebSocketEvent) => void;
  updateAmbulanceVisualPos: (pos: SvgPoint & { angle: number }) => void;
  resetDashboard: () => void;
}

const initialStationPos = getJunctionSvgPos('J01');

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

  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setSelectedCameraId: (id) => set({ selectedCameraId: id }),
  setSelectedJunctionId: (id) => set({ selectedJunctionId: id }),
  setIsVisionModalOpen: (open) => set({ isVisionModalOpen: open }),
  setActiveVisionTab: (tab) => set({ activeVisionTab: tab }),
  setIsPresentationMode: (val) => set({ isPresentationMode: val }),
  updateAmbulanceVisualPos: (pos) => set({ ambulanceVisualPos: pos }),
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
      lastUpdated: new Date().toISOString(),
    });
  },

  hydrateState: (snapshot) => {
    if (!snapshot) return;

    let visualPos = get().ambulanceVisualPos;
    let lastCoord = get().lastAmbulanceCoord;

    if (snapshot.ambulance && typeof snapshot.ambulance.x === 'number' && typeof snapshot.ambulance.y === 'number') {
      const targetSvg = sumoToSvg(snapshot.ambulance.x, snapshot.ambulance.y);
      let angle = visualPos.angle;
      if (lastCoord) {
        const dx = targetSvg.x - lastCoord.x;
        const dy = targetSvg.y - lastCoord.y;
        if (Math.hypot(dx, dy) > 0.5) {
          angle = (Math.atan2(dy, dx) * 180) / Math.PI;
        }
      }
      visualPos = { ...targetSvg, angle };
      lastCoord = targetSvg;
    }

    const routeData = snapshot.route || {};
    let pickupReplan = get().latestPickupReplan;
    if (routeData.route_stage === 'PICKUP_REPLAN' || routeData.replan_type === 'PICKUP_TRANSITION') {
      pickupReplan = routeData;
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
      lastUpdated: new Date().toISOString(),
    });
  },

  // Central Single Event Dispatcher
  dispatchWsEvent: (event) => {
    if (!event || !event.type) return;
    const now = new Date().toISOString();

    switch (event.type) {
      case 'STATE_SNAPSHOT': {
        get().hydrateState(event.data);
        break;
      }

      case 'AMBULANCE_STATUS': {
        const currentAmb = get().ambulance;
        const currentRoute = get().route;
        const newAmb = { ...currentAmb, ...event.data };

        const updatedRoute = { ...currentRoute };
        const statusUpper = String(event.data.status || '').toUpperCase();
        const pickupReached = Boolean(event.data.pickup_reached);

        if (pickupReached || statusUpper === 'EN_ROUTE_TO_HOSPITAL' || statusUpper === 'PICKUP_REACHED') {
          updatedRoute.pickup_reached = true;
          updatedRoute.route_stage = 'POST_PICKUP';
        }

        if (statusUpper === 'ARRIVED') {
          updatedRoute.pickup_reached = true;
          updatedRoute.route_stage = 'ARRIVED';
        }

        set({
          ambulance: newAmb,
          route: updatedRoute,
          lastUpdated: now,
        });
        break;
      }

      case 'AI_ROUTE': {
        const routeData = event.data;
        const isPickupReplan =
          routeData.route_stage === 'PICKUP_REPLAN' ||
          routeData.replan_type === 'PICKUP_TRANSITION';

        set((state) => ({
          route: routeData,
          latestPickupReplan: isPickupReplan ? routeData : state.latestPickupReplan,
          replanBannerDismissed: isPickupReplan ? false : state.replanBannerDismissed,
          lastUpdated: now,
        }));
        break;
      }

      case 'HOSPITAL_SELECTION': {
        set({
          hospital: event.data,
          lastUpdated: now,
        });
        break;
      }

      case 'TRAFFIC_OVERVIEW': {
        const data = event.data;
        const key = data.camera_id || (data.edge_ids && data.edge_ids.join(',')) || 'traffic_default';
        set((state) => ({
          traffic: {
            ...state.traffic,
            [key]: {
              ...(state.traffic[key] || {}),
              ...data,
            },
          },
          lastUpdated: now,
        }));
        break;
      }

      case 'SIGNAL_UPDATE': {
        const data = event.data;
        if (data && data.junction_id) {
          set((state) => ({
            signals: {
              ...state.signals,
              [String(data.junction_id)]: data,
            },
            lastUpdated: now,
          }));
        }
        break;
      }

      case 'GREEN_CORRIDOR_STATUS': {
        set((state) => ({
          corridor: {
            ...state.corridor,
            ...event.data,
          },
          lastUpdated: now,
        }));
        break;
      }

      case 'JUNCTION_CAMERA_DETECTION': {
        const data = event.data;
        const key = data.junction_id || data.camera_id;
        if (key) {
          set((state) => ({
            junction_cameras: {
              ...state.junction_cameras,
              [String(key)]: data,
            },
            lastVisionEventTime: Date.now(),
            lastUpdated: now,
          }));
        }
        break;
      }

      case 'VEHICLE_UPDATE': {
        const data = event.data;
        const vehicleId = data.vehicle_id as string;
        if (!vehicleId) return;

        set((state) => {
          const newVehicles = {
            ...state.vehicles,
            [vehicleId]: data,
          };

          if (vehicleId === 'AI_AMB_001') {
            const currentAmb = state.ambulance;
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
              simulation_time: data.simulation_time as number,
            };

            let visualPos = state.ambulanceVisualPos;
            let lastCoord = state.lastAmbulanceCoord;

            if (typeof data.x === 'number' && typeof data.y === 'number') {
              const targetSvg = sumoToSvg(data.x, data.y);
              let angle = visualPos.angle;
              if (lastCoord) {
                const dx = targetSvg.x - lastCoord.x;
                const dy = targetSvg.y - lastCoord.y;
                if (Math.hypot(dx, dy) > 0.5) {
                  angle = (Math.atan2(dy, dx) * 180) / Math.PI;
                }
              }
              visualPos = { ...targetSvg, angle };
              lastCoord = targetSvg;
            }

            return {
              vehicles: newVehicles,
              ambulance: updatedAmb,
              ambulanceVisualPos: visualPos,
              lastAmbulanceCoord: lastCoord,
              lastUpdated: now,
            };
          }

          return {
            vehicles: newVehicles,
            lastUpdated: now,
          };
        });
        break;
      }

      case 'EMERGENCY_METRICS': {
        set({
          metrics: event.data,
          lastUpdated: now,
        });
        break;
      }

      case 'LOG': {
        set((state) => ({
          logs: [...state.logs.slice(-199), event.data],
          lastUpdated: now,
        }));
        break;
      }

      default:
        console.warn('Unhandled WebSocket event type:', (event as { type: string }).type);
    }
  },
}));
