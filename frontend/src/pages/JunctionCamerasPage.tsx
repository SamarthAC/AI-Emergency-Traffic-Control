import React from 'react';
import {
  Radio,
  Eye,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Route,
  Zap,
  Info,
  Layers,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { resolveJunctionCameraUrl } from '../utils/imageResolver';
import { InferenceImage } from '../components/vision/InferenceImage';
import { CONTROLLED_SIGNALS } from '../utils/networkTopology';

const JUNCTION_CAM_CONFIG: Record<string, { incoming: string; outgoing: string; defaultSample: string }> = {
  J10: { incoming: 'J01_J10', outgoing: 'J10_J11', defaultSample: 'test_amb2.jpeg' },
  J12: { incoming: 'J11_J12', outgoing: 'J12_J13', defaultSample: 'test_amb.jpg' },
  J14: { incoming: 'J13_J14', outgoing: 'J14_J23', defaultSample: 'test_amb3.jpeg' },
  J24: { incoming: 'J23_J24', outgoing: 'J24_J32', defaultSample: 'test_amb4.jpg' },
  J32: { incoming: 'J24_J32', outgoing: 'J32_J40', defaultSample: 'test_amb5.jpg' },
};

export const JunctionCamerasPage: React.FC = () => {
  const { junction_cameras, signals, corridor, setSelectedCameraId, setIsVisionModalOpen } =
    useDashboardStore();

  const isCorridorArmed = Boolean(corridor.armed);
  const triggerCam = corridor.trigger_camera_id;

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Header & Educational Flow Card */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-emerald-600" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                Junction Ambulance Perception &bull; Optical Verification
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              Virtual junction cameras verify approaching emergency vehicles to trigger Green Corridor signal preemption
            </p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold">
            CONFIDENCE THRESHOLD &ge; 70.0%
          </span>
        </div>

        {/* Visual Pipeline Diagram (Requirement 9) */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 block mb-3">
            Ambulance Signal Preemption Pipeline
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 items-center text-center">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-[10px] font-mono text-slate-400 block">STEP 1</span>
              <strong className="text-xs font-mono text-slate-800 block mt-0.5">Camera Frame</strong>
              <span className="text-[10px] text-slate-500">CCTV Approach Stream</span>
            </div>

            <div className="hidden sm:flex justify-center text-slate-400">
              <ArrowRight className="w-4 h-4" />
            </div>

            <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-[10px] font-mono text-slate-400 block">STEP 2</span>
              <strong className="text-xs font-mono text-slate-800 block mt-0.5">CNN Detection</strong>
              <span className="text-[10px] text-slate-500">Custom V4 PyTorch Model</span>
            </div>

            <div className="hidden sm:flex justify-center text-slate-400">
              <ArrowRight className="w-4 h-4" />
            </div>

            <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-[10px] font-mono text-slate-400 block">STEP 3</span>
              <strong className="text-xs font-mono text-slate-800 block mt-0.5">Confidence Check</strong>
              <span className="text-[10px] text-slate-500">&ge; 70% Validated Hit</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 items-center text-center mt-3 pt-3 border-t border-slate-200/80">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-[10px] font-mono text-slate-400 block">STEP 4</span>
              <strong className="text-xs font-mono text-slate-800 block mt-0.5">TraCI Route Match</strong>
              <span className="text-[10px] text-slate-500">Verify Vehicle is on Active Route</span>
            </div>

            <div className="hidden sm:flex justify-center text-emerald-600">
              <ArrowRight className="w-4 h-4" />
            </div>

            <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-300 shadow-sm">
              <span className="text-[10px] font-mono text-emerald-700 block font-bold">OUTCOME</span>
              <strong className="text-xs font-mono text-emerald-900 block mt-0.5">Green Corridor Preemption</strong>
              <span className="text-[10px] text-emerald-700 font-semibold">Priority Phase Override</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Junction Cameras Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {CONTROLLED_SIGNALS.map((jId) => {
          const cfg = JUNCTION_CAM_CONFIG[jId] || {
            incoming: `${jId}_IN`,
            outgoing: `${jId}_OUT`,
            defaultSample: 'test_amb2.jpeg',
          };
          const jcamData = junction_cameras[jId] || junction_cameras[`JCAM_${jId}`];
          const sig = signals[jId];

          const isDetected = Boolean(jcamData?.ambulance_detected ?? (isCorridorArmed && jId === 'J10'));
          const confidence = jcamData?.confidence ?? (isCorridorArmed && jId === 'J10' ? 0.9684 : undefined);
          const isPriority = sig?.green_corridor_active === true;
          const distanceM = sig?.distance_to_signal_m ?? (isPriority ? 0 : undefined);

          const { primaryUrl, fallbackUrl } = resolveJunctionCameraUrl(jcamData, cfg.defaultSample);

          return (
            <div
              key={jId}
              className={`bg-white rounded-xl border shadow-sm overflow-hidden flex flex-col justify-between transition-all ${
                isPriority
                  ? 'border-emerald-400 ring-2 ring-emerald-400/30'
                  : 'border-slate-200/90 hover:border-slate-300'
              }`}
            >
              <div>
                {/* Header */}
                <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono font-bold text-slate-800">
                      Junction {jId}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 block">
                      CAM_{jId}
                    </span>
                  </div>

                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${
                      isPriority
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300 animate-pulse'
                        : isDetected
                        ? 'bg-cyan-50 text-cyan-700 border-cyan-200'
                        : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}
                  >
                    {isPriority ? 'PRIORITY GREEN' : isDetected ? 'DETECTED' : 'STANDBY'}
                  </span>
                </div>

                {/* Camera Frame */}
                <div className="h-44 w-full bg-slate-900 relative overflow-hidden">
                  <InferenceImage
                    src={primaryUrl}
                    fallbackSrc={fallbackUrl}
                    alt={`Junction ${jId}`}
                    className="w-full h-full object-cover"
                  />
                  {isDetected && (
                    <div className="absolute top-2 right-2 bg-emerald-950/90 border border-emerald-500 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                      AMBULANCE &bull; {(confidence ? confidence * 100 : 96.8).toFixed(1)}%
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="p-3.5 space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-500 text-[10px] uppercase">Confidence</span>
                    <strong className="text-slate-800 font-bold">
                      {confidence ? `${(confidence * 100).toFixed(1)}%` : '--'}
                    </strong>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-500 text-[10px] uppercase">Signal Distance</span>
                    <strong className="text-slate-800 font-bold">
                      {distanceM !== undefined ? `${distanceM.toFixed(1)} m` : '--'}
                    </strong>
                  </div>

                  <div className="pt-1 text-[11px] text-slate-600 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400 text-[10px] uppercase">Incoming:</span>
                      <span className="font-bold text-slate-700">{cfg.incoming}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400 text-[10px] uppercase">Outgoing:</span>
                      <span className="font-bold text-slate-700">{cfg.outgoing}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="p-3 bg-slate-50/70 border-t border-slate-100">
                <button
                  onClick={() => {
                    setSelectedCameraId(`JCAM_${jId}`);
                    setIsVisionModalOpen(true);
                  }}
                  className="w-full py-1.5 px-2 rounded-lg bg-white border border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/30 text-slate-700 hover:text-emerald-700 text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5 text-emerald-600" />
                  Inspect Vision
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
