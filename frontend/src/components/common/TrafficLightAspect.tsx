import React from 'react';

export type SignalAspectState = 'RED' | 'YELLOW' | 'GREEN' | 'MUTED' | 'NORMAL';

interface TrafficLightAspectProps {
  state?: SignalAspectState;
  size?: 'xs' | 'sm' | 'md';
  isHalo?: boolean;
}

export const TrafficLightAspect: React.FC<TrafficLightAspectProps> = ({
  state = 'MUTED',
  size = 'sm',
  isHalo = false,
}) => {
  const isRed = state === 'RED';
  const isYellow = state === 'YELLOW';
  const isGreen = state === 'GREEN';

  const dotSize = size === 'xs' ? 'w-2 h-2' : size === 'sm' ? 'w-2.5 h-2.5' : 'w-3 h-3';
  const boxPadding = size === 'xs' ? 'p-1 gap-1' : size === 'sm' ? 'p-1.5 gap-1.5' : 'p-2 gap-2';

  return (
    <div
      className={`inline-flex flex-col items-center justify-center bg-slate-900 rounded-md border border-slate-700/80 shadow-inner ${boxPadding} ${
        isHalo ? 'ring-2 ring-emerald-500/80 shadow-[0_0_12px_rgba(16,185,129,0.35)]' : ''
      }`}
    >
      {/* RED */}
      <div
        className={`rounded-full transition-all duration-300 ${dotSize} ${
          isRed
            ? 'bg-red-500 shadow-[0_0_8px_#ef4444]'
            : 'bg-red-950/60 border border-red-900/40 opacity-40'
        }`}
      />
      {/* YELLOW */}
      <div
        className={`rounded-full transition-all duration-300 ${dotSize} ${
          isYellow
            ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b]'
            : 'bg-amber-950/60 border border-amber-900/40 opacity-40'
        }`}
      />
      {/* GREEN */}
      <div
        className={`rounded-full transition-all duration-300 ${dotSize} ${
          isGreen
            ? 'bg-emerald-400 shadow-[0_0_10px_#10b981] animate-pulse'
            : 'bg-emerald-950/60 border border-emerald-900/40 opacity-40'
        }`}
      />
    </div>
  );
};
