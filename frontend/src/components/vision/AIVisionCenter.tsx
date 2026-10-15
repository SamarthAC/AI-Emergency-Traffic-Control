import React from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { InferenceImage } from './InferenceImage';
import {
  resolveTrafficCameraUrl,
  resolveJunctionCameraUrl,
  AMBULANCE_SAMPLE_GALLERY,
} from '../../utils/imageResolver';
import { CAMERA_DEFINITIONS } from '../../utils/networkTopology';
import { Badge } from '../common/Badge';
import { ExplainabilityFlow } from '../common/ExplainabilityFlow';
import { getTrafficColor } from '../../utils/formatters';

export const AIVisionCenter: React.FC = () => {
  const {
    activeVisionTab,
    setActiveVisionTab,
    traffic,
    junction_cameras,
    setSelectedCameraId,
    setIsVisionModalOpen,
  } = useDashboardStore();

  const jcamJ10 = junction_cameras['J10'] || junction_cameras['JCAM_J10'];
  const { primaryUrl: resolvedJcamUrl, fallbackUrl: fallbackJcamUrl } = resolveJunctionCameraUrl(
    jcamJ10,
    'test_amb2.jpeg'
  );

  const trafficCams = Object.values(CAMERA_DEFINITIONS).filter((c) => c.type === 'traffic');

  return (
    <div className="flex flex-col h-full bg-command-panel/90 border border-command-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-command-surface border-b border-command-border/80">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
            AI Vision Intelligence
          </span>
        </div>

        <div className="flex items-center p-0.5 bg-slate-900 rounded border border-slate-700/60">
          <button
            onClick={() => setActiveVisionTab('traffic')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeVisionTab === 'traffic'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            TRAFFIC ANALYSIS
          </button>
          <button
            onClick={() => setActiveVisionTab('ambulance')}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
              activeVisionTab === 'ambulance'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            AMBULANCE DETECTION
          </button>
        </div>
      </div>

      <div className="p-3.5 flex-1 overflow-y-auto space-y-3">
        {activeVisionTab === 'traffic' ? (
          <>
            <div className="grid grid-cols-2 gap-2.5">
              {trafficCams.slice(0, 4).map((cam) => {
                const liveData = traffic[cam.id];
                const count = liveData?.cnn_detection_count ?? liveData?.vehicle_count ?? 48;
                const score = liveData?.traffic_score ?? 65.0;
                const level = liveData?.traffic_level || 'MEDIUM';
                const color = getTrafficColor(level);

                const { primaryUrl, fallbackUrl } = resolveTrafficCameraUrl(
                  cam.id,
                  liveData,
                  cam.defaultImage
                );

                return (
                  <div
                    key={cam.id}
                    onClick={() => {
                      setSelectedCameraId(cam.id);
                      setIsVisionModalOpen(true);
                    }}
                    className="group bg-command-surface/80 border border-command-border hover:border-cyan-500/50 rounded-lg p-2.5 cursor-pointer transition-all flex flex-col shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-mono font-semibold text-slate-300 truncate">
                        {cam.id}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold ${color.bg} ${color.text} border ${color.border}`}
                      >
                        {level}
                      </span>
                    </div>

                    <InferenceImage
                      src={primaryUrl}
                      fallbackSrc={fallbackUrl}
                      alt={cam.name}
                      badge={liveData?.image || cam.defaultImage}
                      aspectRatio="video"
                    />

                    <div className="mt-2 grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400">
                      <div>
                        <span>CNN Detections:</span>{' '}
                        <strong className="text-slate-200">{count}</strong>
                      </div>
                      <div className="text-right">
                        <span>Density:</span>{' '}
                        <strong className={color.text}>{score.toFixed(1)}</strong>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <ExplainabilityFlow
              type="traffic"
              data={{
                camera: 'CAM_HOSPITAL_DIRECT_2',
                detections: traffic['CAM_HOSPITAL_DIRECT_2']?.cnn_detection_count ?? 48,
                score: traffic['CAM_HOSPITAL_DIRECT_2']?.traffic_score ?? 90.4,
                level: traffic['CAM_HOSPITAL_DIRECT_2']?.traffic_level || 'HIGH',
              }}
            />
          </>
        ) : (
          <>
            <div className="bg-command-surface/90 border border-emerald-500/40 rounded-lg p-3 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono font-bold text-emerald-300">
                    JCAM_J10 JUNCTION CAMERA CONFIRMATION
                  </span>
                </div>
                <Badge variant="emerald" size="sm" pulse>
                  AMBULANCE CONFIRMED
                </Badge>
              </div>

              <div className="grid grid-cols-12 gap-3 items-center">
                <div className="col-span-6">
                  <InferenceImage
                    src={resolvedJcamUrl}
                    fallbackSrc={fallbackJcamUrl}
                    alt="JCAM J10 Ambulance Detection"
                    badge="JCAM_J10"
                    isDemoSample={true}
                    aspectRatio="video"
                    onClick={() => {
                      setSelectedCameraId('JCAM_J10');
                      setIsVisionModalOpen(true);
                    }}
                  />
                </div>

                <div className="col-span-6 space-y-2 text-xs font-mono">
                  <div className="flex justify-between p-1.5 bg-slate-900/90 rounded border border-slate-700/60">
                    <span className="text-slate-400">CNN Confidence:</span>
                    <strong className="text-emerald-400 font-bold">
                      {Math.round((jcamJ10?.confidence ?? 0.81) * 100)}%
                    </strong>
                  </div>
                  <div className="flex justify-between p-1.5 bg-slate-900/90 rounded border border-slate-700/60">
                    <span className="text-slate-400">Detection Threshold:</span>
                    <strong className="text-slate-200">
                      {Math.round((jcamJ10?.minimum_confidence ?? 0.70) * 100)}%
                    </strong>
                  </div>
                  <div className="flex justify-between p-1.5 bg-slate-900/90 rounded border border-slate-700/60">
                    <span className="text-slate-400">Distance to Signal:</span>
                    <strong className="text-cyan-400">
                      {jcamJ10?.metadata?.distance_to_signal_m
                        ? `${jcamJ10.metadata.distance_to_signal_m.toFixed(1)} m`
                        : '219.03 m'}
                    </strong>
                  </div>
                  <div className="flex justify-between p-1.5 bg-slate-900/90 rounded border border-slate-700/60">
                    <span className="text-slate-400">Vector:</span>
                    <span className="text-slate-300 font-bold">J01_J10 &rarr; J10_J11</span>
                  </div>
                </div>
              </div>
            </div>

            <ExplainabilityFlow
              type="ambulance"
              data={{
                confidence: jcamJ10?.confidence ?? 0.81,
                threshold: jcamJ10?.minimum_confidence ?? 0.70,
              }}
            />

            <div className="pt-2">
              <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center justify-between">
                <span>PROJECT EVALUATION SAMPLES (CNN TEST SUITE)</span>
                <span className="text-[10px] text-slate-500">6 Test Frames</span>
              </div>
              <div className="grid grid-cols-6 gap-2">
                {AMBULANCE_SAMPLE_GALLERY.map((sample) => (
                  <div
                    key={sample.id}
                    onClick={() => {
                      setSelectedCameraId('JCAM_J10');
                      setIsVisionModalOpen(true);
                    }}
                    className="cursor-pointer group"
                    title={sample.label}
                  >
                    <InferenceImage
                      src={sample.url}
                      fallbackSrc={sample.fallback}
                      alt={sample.label}
                      aspectRatio="square"
                      isDemoSample={true}
                      className="border-slate-700/70 group-hover:border-cyan-400"
                    />
                    <div className="text-[9px] font-mono text-slate-400 truncate mt-1 text-center">
                      {sample.id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
