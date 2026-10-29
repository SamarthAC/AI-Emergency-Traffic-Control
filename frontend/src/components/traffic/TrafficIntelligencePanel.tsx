import React, { useState } from 'react';
import { Video, ExternalLink, Clock, Route, Upload, ShieldAlert, Sparkles, AlertCircle } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CAMERA_DEFINITIONS } from '../../utils/networkTopology';
import { getTrafficColor } from '../../utils/formatters';
import { resolveTrafficCameraUrl } from '../../utils/imageResolver';
import { InferenceImage } from '../vision/InferenceImage';
import { CameraUploadModal } from './CameraUploadModal';

export const TrafficIntelligencePanel: React.FC = () => {
  const { traffic, setSelectedCameraId, setIsVisionModalOpen, uploadStatus } = useDashboardStore();

  const [uploadModalCameraId, setUploadModalCameraId] = useState<string | null>(null);

  const trafficCams = Object.values(CAMERA_DEFINITIONS).filter((c) => c.type === 'traffic');

  return (
    <>
      <Card
        title="Live Traffic Cameras (Custom CNN Inference)"
        icon={<Video className="w-4 h-4 text-cyan-400" />}
        badge={
          <Badge variant="cyan" size="sm">
            5 LOGICAL CAMERAS
          </Badge>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {trafficCams.map((cam) => {
            const liveData = traffic[cam.id];
            const hasData = Boolean(liveData);
            const detections = liveData?.cnn_detection_count ?? liveData?.vehicle_count;
            const nonAmbVehicles = liveData?.vehicle_count ?? detections;
            const score = liveData?.traffic_score;
            const level = liveData?.traffic_level || (score !== undefined ? (score > 75 ? 'HIGH' : score > 45 ? 'MEDIUM' : 'LOW') : 'DEFAULT');
            const color = getTrafficColor(level);
            const mappedEdges = liveData?.edge_ids || cam.edgeIds;
            const simTime = liveData?.simulation_time;
            const ambDetected = liveData?.ambulance_detected;
            const status = uploadStatus[cam.id] || 'IDLE';

            const { primaryUrl, fallbackUrl } = resolveTrafficCameraUrl(cam.id, liveData, cam.defaultImage);

            return (
              <div
                key={cam.id}
                className="p-2.5 bg-command-surface/95 hover:bg-slate-800/90 border border-command-border hover:border-cyan-500/50 rounded-lg transition-all flex flex-col justify-between group shadow-md"
              >
                <div>
                  {/* Header with Camera ID and Traffic Level Badge */}
                  <div className="flex items-center justify-between mb-1.5 gap-1">
                    <span className="text-[11px] font-mono font-bold text-slate-200 truncate group-hover:text-cyan-300">
                      {cam.id}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold shrink-0 ${color.bg} ${color.text} border ${color.border}`}
                    >
                      {level}
                    </span>
                  </div>

                  {/* Actual Current Camera Frame */}
                  <div
                    className="mb-2 cursor-pointer"
                    onClick={() => {
                      setSelectedCameraId(cam.id);
                      setIsVisionModalOpen(true);
                    }}
                  >
                    <InferenceImage
                      src={primaryUrl}
                      fallbackSrc={fallbackUrl}
                      alt={cam.name}
                      aspectRatio="video"
                      badge={liveData?.image || cam.defaultImage}
                    />
                  </div>

                  {/* Upload Status Alert if active */}
                  {status === 'WAITING_CNN' && (
                    <div className="mb-2 px-2 py-1 rounded bg-amber-950/70 border border-amber-500/50 text-[10px] font-mono text-amber-300 animate-pulse">
                      WAITING FOR CNN...
                    </div>
                  )}
                  {status === 'CNN_COMPLETE' && (
                    <div className="mb-2 px-2 py-1 rounded bg-emerald-950/70 border border-emerald-500/50 text-[10px] font-mono text-emerald-300">
                      CNN UPDATED
                    </div>
                  )}

                  {/* Detailed Telemetry (Section 13) */}
                  <div className="space-y-1 text-[11px] font-mono">
                    <div className="flex justify-between text-slate-400">
                      <span>Traffic Score:</span>
                      <strong className={color.text}>
                        {score !== undefined ? `${score.toFixed(1)} / 100` : '-- / 100'}
                      </strong>
                    </div>

                    <div className="flex justify-between text-slate-400">
                      <span>Non-Amb Vehicles:</span>
                      <strong className="text-slate-200">
                        {nonAmbVehicles !== undefined ? nonAmbVehicles : '--'}
                      </strong>
                    </div>

                    <div className="flex justify-between text-slate-400">
                      <span>CNN Detections:</span>
                      <strong className="text-slate-300">
                        {detections !== undefined ? detections : '--'}
                      </strong>
                    </div>

                    <div className="flex justify-between text-slate-400">
                      <span>Ambulance Seen:</span>
                      <strong className={ambDetected ? 'text-red-400 font-bold' : 'text-slate-400'}>
                        {ambDetected !== undefined ? (ambDetected ? 'YES' : 'NO') : '--'}
                      </strong>
                    </div>

                    <div className="flex justify-between text-slate-400">
                      <span>Sim Time:</span>
                      <span className="text-slate-300">{simTime !== undefined ? `${simTime}s` : '--'}</span>
                    </div>
                  </div>
                </div>

                {/* Mapped Edges & Upload Action (Section 15) */}
                <div className="mt-2.5 pt-2 border-t border-command-border/60 space-y-1.5">
                  <div className="text-[9px] font-mono text-slate-500 truncate" title={mappedEdges.join(', ')}>
                    Edges: <span className="text-slate-400">{mappedEdges.slice(0, 2).join(', ')}{mappedEdges.length > 2 ? '...' : ''}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setUploadModalCameraId(cam.id)}
                      title="Upload a new camera frame to replace this CCTV input"
                      className="flex-1 py-1 px-2 rounded bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-500/50 hover:border-cyan-400 text-[10px] font-mono text-cyan-300 font-semibold flex items-center justify-center gap-1 transition-all shadow-sm"
                    >
                      <Upload className="w-3 h-3 text-cyan-400" />
                      <span>CHANGE FRAME</span>
                    </button>

                    <button
                      onClick={() => {
                        setSelectedCameraId(cam.id);
                        setIsVisionModalOpen(true);
                      }}
                      title="Inspect camera inference pipeline"
                      className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-cyan-300 border border-slate-700 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Dynamic Image Upload Modal */}
      <CameraUploadModal
        cameraId={uploadModalCameraId}
        isOpen={Boolean(uploadModalCameraId)}
        onClose={() => setUploadModalCameraId(null)}
      />
    </>
  );
};
