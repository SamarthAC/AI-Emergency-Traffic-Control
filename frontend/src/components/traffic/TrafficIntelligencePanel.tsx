import React from 'react';
import { Video, ExternalLink, Clock, Route } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CAMERA_DEFINITIONS } from '../../utils/networkTopology';
import { getTrafficColor } from '../../utils/formatters';
import { resolveTrafficCameraUrl } from '../../utils/imageResolver';
import { InferenceImage } from '../vision/InferenceImage';

export const TrafficIntelligencePanel: React.FC = () => {
  const { traffic, setSelectedCameraId, setIsVisionModalOpen } = useDashboardStore();

  const trafficCams = Object.values(CAMERA_DEFINITIONS).filter((c) => c.type === 'traffic');

  return (
    <Card
      title="Traffic Intelligence (Custom CNN)"
      icon={<Video className="w-4 h-4" />}
      badge={
        <Badge variant="cyan" size="sm">
          5 CAMERAS ACTIVE
        </Badge>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {trafficCams.map((cam) => {
          const liveData = traffic[cam.id];
          const detections = liveData?.cnn_detection_count ?? liveData?.vehicle_count ?? 35;
          const nonAmbVehicles = liveData?.vehicle_count ?? detections;
          const score = liveData?.traffic_score ?? 50;
          const level = liveData?.traffic_level || (score > 75 ? 'HIGH' : score > 45 ? 'MEDIUM' : 'LOW');
          const color = getTrafficColor(level);
          const mappedEdges = liveData?.edge_ids || cam.edgeIds;
          const simTime = liveData?.simulation_time;

          const { primaryUrl, fallbackUrl } = resolveTrafficCameraUrl(cam.id, liveData, cam.defaultImage);

          return (
            <div
              key={cam.id}
              onClick={() => {
                setSelectedCameraId(cam.id);
                setIsVisionModalOpen(true);
              }}
              className="p-2.5 bg-command-surface/95 hover:bg-slate-800/90 border border-command-border hover:border-cyan-500/50 rounded-lg cursor-pointer transition-all flex flex-col justify-between group shadow-md"
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
                <div className="mb-2">
                  <InferenceImage
                    src={primaryUrl}
                    fallbackSrc={fallbackUrl}
                    alt={cam.name}
                    aspectRatio="video"
                    badge={liveData?.image || cam.defaultImage}
                  />
                </div>

                {/* Detailed Telemetry */}
                <div className="space-y-1 text-[11px] font-mono">
                  <div className="flex justify-between text-slate-400">
                    <span>CNN Detections:</span>
                    <strong className="text-slate-100">{detections}</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Detected Vehicles:</span>
                    <strong className="text-slate-300">{nonAmbVehicles}</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Traffic Score:</span>
                    <strong className={color.text}>{score.toFixed(1)} / 100</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Sim Time:</span>
                    <span className="text-slate-300">{simTime !== undefined ? `${simTime}s` : '--'}</span>
                  </div>
                </div>
              </div>

              {/* Mapped SUMO Edges & Inspect Action */}
              <div className="mt-2 pt-1.5 border-t border-command-border/60">
                <div className="text-[9px] font-mono text-slate-500 truncate mb-1" title={mappedEdges.join(', ')}>
                  Edges: <span className="text-slate-400">{mappedEdges.slice(0, 2).join(', ')}{mappedEdges.length > 2 ? '...' : ''}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-cyan-400 group-hover:text-cyan-300">
                  <span>Inspect Pipeline</span>
                  <ExternalLink className="w-3 h-3 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
