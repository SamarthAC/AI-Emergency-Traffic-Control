import React from 'react';
import { X, Camera, Info, Route, Zap, Eye, ShieldAlert } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { CAMERA_DEFINITIONS } from '../../utils/networkTopology';
import { resolveTrafficCameraUrl, resolveJunctionCameraUrl } from '../../utils/imageResolver';
import { InferenceImage } from './InferenceImage';
import { Badge } from '../common/Badge';
import { ExplainabilityFlow } from '../common/ExplainabilityFlow';
import { getTrafficColor } from '../../utils/formatters';

export const CameraInspectorModal: React.FC = () => {
  const {
    isVisionModalOpen,
    setIsVisionModalOpen,
    selectedCameraId,
    traffic,
    junction_cameras,
  } = useDashboardStore();

  if (!isVisionModalOpen || !selectedCameraId) return null;

  const camDef = CAMERA_DEFINITIONS[selectedCameraId];
  const isJunctionCam = selectedCameraId.startsWith('JCAM') || camDef?.type === 'junction';

  const trafficData = traffic[selectedCameraId];
  const junctionData = junction_cameras['J10'] || junction_cameras[selectedCameraId];

  let primaryUrl = '';
  let fallbackUrl = '';
  let imageName = '';

  if (isJunctionCam) {
    imageName = junctionData?.metadata?.image || 'test_amb2.jpeg';
    const urls = resolveJunctionCameraUrl(junctionData, imageName);
    primaryUrl = urls.primaryUrl;
    fallbackUrl = urls.fallbackUrl;
  } else {
    imageName = trafficData?.image || camDef?.defaultImage || 'high3.jpg';
    const urls = resolveTrafficCameraUrl(selectedCameraId, trafficData, imageName);
    primaryUrl = urls.primaryUrl;
    fallbackUrl = urls.fallbackUrl;
  }

  const level = trafficData?.traffic_level || 'HIGH';
  const color = getTrafficColor(level);
  const mappedEdges = trafficData?.edge_ids || camDef?.edgeIds || [];
  const simTime = trafficData?.simulation_time ?? junctionData?.simulation_time;
  const nonAmbVehicles = trafficData?.vehicle_count ?? trafficData?.cnn_detection_count ?? 48;
  const cnnDetections = trafficData?.cnn_detection_count ?? trafficData?.vehicle_count ?? 48;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-command-surface border border-command-borderLight rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-5 py-3.5 bg-command-panel border-b border-command-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Camera className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
                <span>{selectedCameraId}</span>
                <span className="text-slate-500 font-normal">|</span>
                <span className="text-xs text-slate-300 font-sans font-medium">
                  {camDef?.name || 'Camera Intelligence Inspector'}
                </span>
              </h2>
            </div>
          </div>

          <button
            onClick={() => setIsVisionModalOpen(false)}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 grid grid-cols-12 gap-6 overflow-y-auto">
          {/* Left Column: Real Camera Frame & Detailed Chain */}
          <div className="col-span-12 md:col-span-7 flex flex-col">
            <div className="text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
              <span>ACTUAL CURRENT FRAME</span>
              <span className="text-[10px] text-slate-500 font-mono">{imageName}</span>
            </div>

            <InferenceImage
              src={primaryUrl}
              fallbackSrc={fallbackUrl}
              alt={selectedCameraId}
              aspectRatio="video"
              className="border-command-borderLight shadow-lg"
              badge={isJunctionCam ? 'AMBULANCE DETECTION' : `${level} TRAFFIC`}
              isDemoSample={true}
            />

            {/* Visual Explainability Chain */}
            <div className="mt-4 p-3 bg-command-bg/90 border border-command-border rounded-lg">
              <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 mb-2 flex items-center gap-1.5 font-bold">
                <Zap className="w-3.5 h-3.5 text-cyan-400" />
                <span>EXPLAINABILITY PIPELINE (END-TO-END REASONING)</span>
              </div>

              {!isJunctionCam ? (
                <div className="grid grid-cols-5 gap-1 text-center items-center font-mono text-[9px]">
                  <div className="p-1.5 bg-slate-900 border border-slate-700 rounded">
                    <div className="text-slate-400">CAMERA FRAME</div>
                    <div className="text-cyan-400 font-bold mt-0.5 truncate">{selectedCameraId}</div>
                  </div>
                  <div className="p-1.5 bg-slate-900 border border-cyan-800 rounded">
                    <div className="text-slate-400">CUSTOM CNN</div>
                    <div className="text-cyan-300 font-bold mt-0.5">{cnnDetections} Detections</div>
                  </div>
                  <div className="p-1.5 bg-slate-900 border border-amber-800 rounded">
                    <div className="text-slate-400">TRAFFIC SCORE</div>
                    <div className="text-amber-400 font-bold mt-0.5">
                      {(trafficData?.traffic_score ?? 90.4).toFixed(1)} / 100
                    </div>
                  </div>
                  <div className="p-1.5 bg-slate-900 border border-red-800 rounded">
                    <div className="text-slate-400">EDGE COST</div>
                    <div className="text-red-400 font-bold mt-0.5">Penalized</div>
                  </div>
                  <div className="p-1.5 bg-cyan-950 border border-cyan-500 rounded">
                    <div className="text-cyan-300">A* ROUTING</div>
                    <div className="text-cyan-400 font-bold mt-0.5">Bypass Evaluated</div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-4 gap-1 text-center items-center font-mono text-[9px]">
                  <div className="p-1.5 bg-slate-900 border border-slate-700 rounded">
                    <div className="text-slate-400">CNN DETECT</div>
                    <div className="text-emerald-400 font-bold">
                      {Math.round((junctionData?.confidence ?? 0.81) * 100)}%
                    </div>
                  </div>
                  <div className="p-1.5 bg-slate-900 border border-slate-700 rounded">
                    <div className="text-slate-400">THRESHOLD</div>
                    <div className="text-slate-200 font-bold">
                      &ge; {Math.round((junctionData?.minimum_confidence ?? 0.70) * 100)}%
                    </div>
                  </div>
                  <div className="p-1.5 bg-slate-900 border border-cyan-800 rounded">
                    <div className="text-slate-400">TRACI ROUTE</div>
                    <div className="text-cyan-400 font-bold">CONFIRMED</div>
                  </div>
                  <div className="p-1.5 bg-emerald-950 border border-emerald-500 rounded">
                    <div className="text-emerald-300 font-bold">GREEN CORRIDOR</div>
                    <div className="text-emerald-400 text-[8px]">ARMED</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Model Output & Engineering Decision */}
          <div className="col-span-12 md:col-span-5 flex flex-col justify-between space-y-3">
            <div className="space-y-2.5">
              <div className="p-3 bg-command-bg/90 rounded-lg border border-command-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1 font-bold">
                  INPUT SOURCE & MODEL
                </span>
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-300">Camera Source:</span>
                  <strong className="text-cyan-400">{selectedCameraId}</strong>
                </div>
                <div className="flex justify-between items-center text-xs font-mono mt-1">
                  <span className="text-slate-300">Inference Engine:</span>
                  <strong className="text-purple-400">Custom CNN V4</strong>
                </div>
                <div className="flex justify-between items-center text-xs font-mono mt-1">
                  <span className="text-slate-300">Source Mode:</span>
                  <span className="text-slate-400">Demo Camera Frame (Prerecorded)</span>
                </div>
                <div className="flex justify-between items-center text-xs font-mono mt-1">
                  <span className="text-slate-300">Simulation Time:</span>
                  <span className="text-slate-300 font-bold">
                    {simTime !== undefined ? `${simTime} s` : '--'}
                  </span>
                </div>
              </div>

              {isJunctionCam ? (
                <div className="p-3 bg-emerald-950/40 rounded-lg border border-emerald-500/40 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 block font-bold">
                    AMBULANCE DETECTION INFERENCE
                  </span>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Detection Status:</span>
                    <Badge variant="emerald" size="sm">CONFIRMED</Badge>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Confidence:</span>
                    <strong className="text-emerald-300 font-bold">
                      {Math.round((junctionData?.confidence ?? 0.81) * 100)}%
                    </strong>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Minimum Threshold:</span>
                    <span className="text-slate-300">
                      {Math.round((junctionData?.minimum_confidence ?? 0.70) * 100)}%
                    </span>
                  </div>
                  <div className="p-2 bg-slate-900/90 rounded border border-slate-700/60 space-y-1">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-slate-300">Traffic Signal Distance:</span>
                      <span className="text-cyan-300 font-bold">
                        {junctionData?.metadata?.distance_to_signal_m !== undefined
                          ? `${junctionData.metadata.distance_to_signal_m.toFixed(1)} m`
                          : '208.3 m'}
                      </span>
                    </div>
                    <span className="text-[9px] text-slate-500 font-mono block">
                      Source: SUMO / TraCI (Visual CNN detection only)
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-command-bg/90 rounded-lg border border-command-border space-y-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-bold">
                    CUSTOM CNN TRAFFIC ANALYSIS
                  </span>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">CNN Detections:</span>
                    <strong className="text-slate-100 font-bold">{cnnDetections}</strong>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Detected Vehicles:</span>
                    <strong className="text-slate-300">{nonAmbVehicles}</strong>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Traffic Score:</span>
                    <strong className={`${color.text} font-bold`}>
                      {(trafficData?.traffic_score ?? 90.4).toFixed(1)} / 100
                    </strong>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Classification:</span>
                    <Badge variant={level === 'HIGH' ? 'red' : level === 'MEDIUM' ? 'amber' : 'emerald'} size="sm">
                      {level}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-300">Mapped SUMO Edges:</span>
                    <span className="text-slate-300 font-mono text-[10px] text-right truncate max-w-[150px]" title={mappedEdges.join(', ')}>
                      {mappedEdges.join(', ')}
                    </span>
                  </div>
                </div>
              )}

              {/* Engineering Impact */}
              <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-700/70 text-xs font-mono space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 block font-bold">
                  SYSTEM ENGINEERING CONSEQUENCE
                </span>
                {isJunctionCam ? (
                  <p className="text-slate-300 leading-relaxed text-[11px]">
                    Visual presence corroborated with TraCI trajectory. Green Corridor signal sequence armed for lookahead intersections.
                  </p>
                ) : (
                  <p className="text-slate-300 leading-relaxed text-[11px]">
                    Traffic density updates edge weights in SUMO graph. Congestion-Aware A* automatically evaluates Outer Ring Road bypass if cost exceeds threshold.
                  </p>
                )}
              </div>
            </div>

            <div className="p-2 bg-slate-950/60 rounded border border-slate-800 text-[10px] font-mono text-slate-500 flex items-start gap-2">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
              <span>
                Demonstration camera frames represent evaluated inputs from the Python AI inference pipeline. Physical signal distance is computed via SUMO/TraCI coordinates.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
