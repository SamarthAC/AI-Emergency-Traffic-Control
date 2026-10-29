import React, { useState } from 'react';
import {
  Camera,
  Upload,
  Eye,
  CheckCircle2,
  Clock,
  Route,
  Activity,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { CAMERA_DEFINITIONS } from '../utils/networkTopology';
import { getTrafficColor } from '../utils/formatters';
import { resolveTrafficCameraUrl } from '../utils/imageResolver';
import { InferenceImage } from '../components/vision/InferenceImage';
import { CameraUploadModal } from '../components/traffic/CameraUploadModal';

export const TrafficCamerasPage: React.FC = () => {
  const {
    traffic,
    setSelectedCameraId,
    setIsVisionModalOpen,
    uploadStatus,
    ambulance,
  } = useDashboardStore();

  const [uploadModalCameraId, setUploadModalCameraId] = useState<string | null>(null);

  const trafficCams = Object.values(CAMERA_DEFINITIONS).filter((c) => c.type === 'traffic');

  // Compute summary stats
  const activeCount = trafficCams.length;
  const directCameras = trafficCams.filter((c) => c.id.includes('DIRECT'));
  const orrCameras = trafficCams.filter((c) => c.id.includes('ORR'));

  const getCorridorStatus = (cams: typeof trafficCams) => {
    let hasHigh = false;
    let hasMed = false;
    for (const c of cams) {
      const data = traffic[c.id];
      const level = data?.traffic_level || (data?.traffic_score && data.traffic_score > 75 ? 'HIGH' : 'LOW');
      if (level === 'HIGH') hasHigh = true;
      if (level === 'MEDIUM') hasMed = true;
    }
    if (hasHigh) return { label: 'HEAVY CONGESTION', color: 'text-red-600 bg-red-50 border-red-200' };
    if (hasMed) return { label: 'MODERATE FLOW', color: 'text-amber-600 bg-amber-50 border-amber-200' };
    return { label: 'OPTIMAL FLOW', color: 'text-emerald-600 bg-emerald-50 border-emerald-200' };
  };

  const directStatus = getCorridorStatus(directCameras);
  const orrStatus = getCorridorStatus(orrCameras);

  const latestSimTime = ambulance.simulation_time ?? 0;

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Header & Summary Row */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-indigo-600" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                Traffic Intelligence &bull; Live CCTV Ingestion
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              Custom PyTorch V4 CNN traffic density analysis across 5 strategic arterial corridors
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold">
              {activeCount} LOGICAL CCTV FEEDS ACTIVE
            </span>
          </div>
        </div>

        {/* Summary Metrics Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">Active Feeds</span>
            <strong className="text-sm font-mono text-slate-800">19 Cameras Online</strong>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">Direct Corridor</span>
            <span className={`inline-block text-xs font-mono font-bold px-1.5 py-0.5 rounded border mt-0.5 ${directStatus.color}`}>
              {directStatus.label}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">ORR Bypass Corridor</span>
            <span className={`inline-block text-xs font-mono font-bold px-1.5 py-0.5 rounded border mt-0.5 ${orrStatus.color}`}>
              {orrStatus.label}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">Last Sync / Frame Time</span>
            <strong className="text-sm font-mono text-slate-800">{latestSimTime.toFixed(1)}s sim-time</strong>
          </div>
        </div>
      </div>

      {/* 2. 5-Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {trafficCams.map((cam) => {
          const liveData = traffic[cam.id];
          const hasData = Boolean(liveData);
          const detections = liveData?.cnn_detection_count ?? liveData?.vehicle_count;
          const score = liveData?.traffic_score;
          const level =
            liveData?.traffic_level ||
            (score !== undefined ? (score > 75 ? 'HIGH' : score > 45 ? 'MEDIUM' : 'LOW') : 'DEFAULT');
          const color = getTrafficColor(level);
          const mappedEdges = liveData?.edge_ids || cam.edgeIds;
          const status = uploadStatus[cam.id] || 'IDLE';

          const { primaryUrl, fallbackUrl } = resolveTrafficCameraUrl(
            cam.id,
            liveData,
            cam.defaultImage
          );

          return (
            <div
              key={cam.id}
              className="bg-white rounded-xl border border-slate-200/90 shadow-sm overflow-hidden flex flex-col justify-between hover:border-indigo-400 transition-all group"
            >
              <div>
                {/* Card Header */}
                <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-800 truncate">
                    {cam.id}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${color.bg} ${color.text} ${color.border}`}
                  >
                    {level}
                  </span>
                </div>

                {/* Camera Image Feed */}
                <div className="h-44 w-full bg-slate-900 relative overflow-hidden">
                  <InferenceImage
                    src={primaryUrl}
                    fallbackSrc={fallbackUrl}
                    alt={cam.id}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />

                  {/* Upload State Pipeline Badge Overlay */}
                  {status !== 'IDLE' && (
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-3 text-center">
                      <span className="text-xs font-mono font-bold text-cyan-400 animate-pulse mb-1">
                        {status === 'UPLOADING' && 'Uploading...'}
                        {status === 'WAITING_CNN' && 'Waiting for CNN...'}
                        {status === 'CNN_COMPLETE' && 'CNN Analysis Complete'}
                        {status === 'ROUTE_UPDATED' && 'Route Updated'}
                      </span>
                      <span className="text-[10px] font-mono text-slate-300">
                        Edge Cost Refreshing
                      </span>
                    </div>
                  )}
                </div>

                {/* Camera Details */}
                <div className="p-3.5 space-y-2.5">
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                    <div className="p-2 rounded bg-slate-50 border border-slate-100">
                      <span className="text-[10px] text-slate-500 block uppercase">Traffic Score</span>
                      <strong className="text-slate-800 font-bold text-sm">
                        {score !== undefined ? score : '--'}
                      </strong>
                    </div>
                    <div className="p-2 rounded bg-slate-50 border border-slate-100">
                      <span className="text-[10px] text-slate-500 block uppercase">Vehicles</span>
                      <strong className="text-slate-800 font-bold text-sm">
                        {detections !== undefined ? detections : '--'}
                      </strong>
                    </div>
                  </div>

                  <div className="text-[11px] font-mono text-slate-600">
                    <span className="text-slate-400 text-[10px] uppercase block">Mapped SUMO Edges:</span>
                    <span className="truncate block font-bold text-slate-700">
                      {mappedEdges.join(', ')}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-3 bg-slate-50/70 border-t border-slate-100 flex items-center gap-2">
                <button
                  onClick={() => setUploadModalCameraId(cam.id)}
                  className="flex-1 py-1.5 px-2 rounded-lg bg-white border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/40 text-slate-700 hover:text-indigo-700 text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all shadow-sm"
                >
                  <Upload className="w-3.5 h-3.5 text-indigo-500" />
                  Change Frame
                </button>
                <button
                  onClick={() => {
                    setSelectedCameraId(cam.id);
                    setIsVisionModalOpen(true);
                  }}
                  className="py-1.5 px-2 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-slate-600 text-xs font-mono flex items-center justify-center transition-all shadow-sm"
                  title="Inspect Camera Inference"
                >
                  <Eye className="w-3.5 h-3.5 text-slate-500" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Modal (if triggered) */}
      {uploadModalCameraId && (
        <CameraUploadModal
          cameraId={uploadModalCameraId}
          isOpen={Boolean(uploadModalCameraId)}
          onClose={() => setUploadModalCameraId(null)}
        />
      )}
    </div>
  );
};
