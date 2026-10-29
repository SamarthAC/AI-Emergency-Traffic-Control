export type ConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'OFFLINE';

export type TrafficLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export type MissionStage =
  | 'IDLE'
  | 'DISPATCHED'
  | 'EN_ROUTE_TO_PICKUP'
  | 'PICKUP_REACHED'
  | 'POST_PICKUP'
  | 'EN_ROUTE_TO_HOSPITAL'
  | 'ARRIVED';

export interface AmbulanceState {
  id?: string;
  status?: string;
  pickup?: string;
  destination?: string;
  destination_name?: string;
  edge_id?: string;
  lane_id?: string;
  route_index?: number;
  route_length?: number;
  speed_kmh?: number;
  x?: number;
  y?: number;
  simulation_time?: number;
  pickup_reached?: boolean;
}

export interface RouteData {
  ambulance_id?: string;
  pickup?: string;
  pickup_reached?: boolean;
  destination?: string;
  route_stage?: 'DISPATCH' | 'PRE_PICKUP' | 'PICKUP_REPLAN' | 'POST_PICKUP' | 'ARRIVED' | string;
  replan_type?: 'INITIAL' | 'DYNAMIC_CONGESTION' | 'PICKUP_TRANSITION' | string;
  route?: string[];
  rerouted?: boolean;
  reroute_from_edge?: string;
  reroute_from_junction?: string;
  previous_post_pickup_route?: string[];
  new_post_pickup_route?: string[];
  old_remaining_cost_s?: number;
  new_remaining_cost_s?: number;
  improvement_percent?: number;
  simulation_time?: number;
  station_to_pickup?: {
    junction_path: string[];
    edge_path: string[];
    distance_m: number;
    base_travel_time_s: number;
    dynamic_cost_s: number;
  };
  pickup_to_hospital?: {
    junction_path: string[];
    edge_path: string[];
    distance_m: number;
    base_travel_time_s: number;
    dynamic_cost_s: number;
  };
}

export interface HospitalCandidate {
  hospital_id: string;
  name: string;
  junction_id: string;
  beds_available: number;
  doctors_available: number;
  dynamic_cost_s: number;
  distance_m: number;
  eligible?: boolean;
  reasons?: string[];
}

export interface HospitalSelection {
  pickup?: string;
  selected_hospital?: HospitalCandidate;
  candidates?: HospitalCandidate[];
  selection_reason?: string;
  simulation_time?: number;
}

export interface TrafficCameraData {
  camera_id: string;
  image?: string;
  image_url?: string;
  image_version?: string | number;
  edge_ids?: string[];
  vehicle_count?: number;
  cnn_detection_count?: number;
  ambulance_detected?: boolean;
  traffic_score?: number;
  traffic_level?: TrafficLevel | string;
  source_mode?: string;
  phase?: string;
  simulation_time?: number;
  timestamp?: string;
}

export type CorridorSignalState = 
  | 'NORMAL' 
  | 'UPCOMING' 
  | 'PRIORITY' 
  | 'ACTIVE' 
  | 'PASSED' 
  | 'RESTORED';

export interface SignalState {
  junction_id: string;
  state?: string;
  green_corridor_active?: boolean;
  corridor_armed?: boolean;
  ambulance_id?: string;
  incoming_edge?: string;
  outgoing_edge?: string;
  incoming_route_index?: number;
  distance_to_signal_m?: number;
  controlled_links?: number[];
  selected_phase?: number;
  phase_state?: string;
  hold_seconds?: number;
  simulation_time?: number;
  restored_program?: string;
  restored_phase?: number;
  // Derived corridor signal state for visualization
  corridor_signal_state?: CorridorSignalState;
}

export type DemoMode = 'WITH_CORRIDOR' | 'WITHOUT_CORRIDOR';

export interface GreenCorridorStatus {
  armed?: boolean;
  ambulance_id?: string;
  trigger_camera_id?: string;
  trigger_junction_id?: string;
  confidence?: number;
  lookahead_signals?: number;
  lookahead_distance_m?: number;
  simulation_time?: number;
  route_updated?: boolean;
  route?: string[];
}

export interface JunctionCameraDetection {
  camera_id: string;
  junction_id?: string;
  ambulance_detected?: boolean;
  confidence?: number;
  minimum_confidence?: number;
  simulation_time?: number;
  metadata?: {
    source_mode?: string;
    image?: string;
    image_url?: string;
    distance_to_signal_m?: number;
    incoming_edge?: string;
    outgoing_edge?: string;
    ambulance_count?: number;
    ambulance_candidate_count?: number;
  };
}

export interface EmergencyMetrics {
  ambulance_id?: string;
  pickup?: string;
  destination?: string;
  destination_name?: string;
  dispatch_time_s?: number;
  pickup_time_s?: number;
  arrival_time_s?: number;
  dispatch_to_pickup_s?: number;
  pickup_to_hospital_s?: number;
  total_emergency_travel_s?: number;
  dynamic_reroutes?: number;
  pickup_stage_replans?: number;
  confirmed_full_stops?: number;
  intersection_stops?: number;
  longest_stationary_s?: number;
  minimum_moving_speed_kmh?: number;
  signals_preempted?: number;
  saved_at?: string;
}

export interface LogEntry {
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'DEBUG' | string;
  message: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface ImageManifest {
  traffic_images?: Record<string, string>;
  junction_images?: Record<string, string>;
  available_cameras?: string[];
  [key: string]: unknown;
}

export interface DashboardStateSnapshot {
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
  meta?: {
    last_event_type?: string | null;
    updated_at?: string | null;
  };
}

export type WebSocketEvent =
  | { type: 'STATE_SNAPSHOT'; data: DashboardStateSnapshot }
  | { type: 'VEHICLE_UPDATE'; data: Record<string, unknown> }
  | { type: 'SIGNAL_UPDATE'; data: SignalState }
  | { type: 'AMBULANCE_STATUS'; data: AmbulanceState }
  | { type: 'AI_ROUTE'; data: RouteData }
  | { type: 'TRAFFIC_OVERVIEW'; data: TrafficCameraData }
  | { type: 'LOG'; data: LogEntry }
  | { type: 'HOSPITAL_SELECTION'; data: HospitalSelection }
  | { type: 'JUNCTION_CAMERA_DETECTION'; data: JunctionCameraDetection }
  | { type: 'GREEN_CORRIDOR_STATUS'; data: GreenCorridorStatus }
  | { type: 'EMERGENCY_METRICS'; data: EmergencyMetrics };

export interface SumoJunctionNode {
  id: string;
  x: number;
  y: number;
  label?: string;
  isControlledSignal?: boolean;
  type?: 'station' | 'pickup' | 'hospital' | 'regular';
}

export interface SumoEdgeDefinition {
  id: string;
  from: string;
  to: string;
  length_m?: number;
}

export interface CameraDefinition {
  id: string;
  name: string;
  type: 'traffic' | 'junction';
  junctionId?: string;
  edgeIds: string[];
  defaultImage: string;
}
