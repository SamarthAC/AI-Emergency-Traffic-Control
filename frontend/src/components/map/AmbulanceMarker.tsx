import React from 'react';
import { formatSpeed } from '../../utils/formatters';

interface AmbulanceMarkerProps {
  x: number;
  y: number;
  angle?: number;
  speedKmh?: number;
  id?: string;
}

export const AmbulanceMarker: React.FC<AmbulanceMarkerProps> = ({
  x,
  y,
  angle = 0,
  speedKmh = 0,
  id = 'AI_AMB_001',
}) => {
  return (
    <g
      transform={`translate(${x}, ${y})`}
      className="transition-transform duration-300 ease-out pointer-events-none"
    >
      {/* Outer Pulse Siren Waves */}
      <circle
        r="28"
        className="fill-cyan-500/10 stroke-cyan-400/40 animate-ping-slow"
        strokeWidth="1"
      />
      <circle
        r="18"
        className="fill-emergency-red/20 stroke-emergency-red/80 animate-pulse"
        strokeWidth="1.5"
      />

      {/* Rotating Vehicle Icon */}
      <g transform={`rotate(${angle})`}>
        {/* Ambulance Body */}
        <rect
          x="-14"
          y="-8"
          width="28"
          height="16"
          rx="3"
          fill="#FFFFFF"
          stroke="#0F172A"
          strokeWidth="1.5"
        />
        {/* Windshield */}
        <rect x="5" y="-6" width="6" height="12" rx="1" fill="#38BDF8" opacity="0.9" />
        {/* Rear Cross / Red Mark */}
        <rect x="-10" y="-3" width="6" height="6" fill="#EF4444" />
        {/* Side emergency stripes */}
        <line x1="-12" y1="-7" x2="4" y2="-7" stroke="#EF4444" strokeWidth="1.5" />
        <line x1="-12" y1="7" x2="4" y2="7" stroke="#EF4444" strokeWidth="1.5" />
        {/* Emergency Beacon Lights */}
        <circle cx="-1" cy="-4" r="2.5" fill="#EF4444" className="animate-pulse" />
        <circle cx="-1" cy="4" r="2.5" fill="#00F0FF" className="animate-pulse" />
      </g>

      {/* Speed & ID Tag Above Vehicle */}
      <g transform="translate(0, -26)">
        <rect
          x="-35"
          y="-12"
          width="70"
          height="16"
          rx="3"
          fill="#0B0F19"
          stroke="#00F0FF"
          strokeWidth="1"
          opacity="0.95"
        />
        <text
          x="0"
          y="0"
          textAnchor="middle"
          fill="#00F0FF"
          fontSize="9"
          fontFamily="monospace"
          fontWeight="bold"
        >
          {formatSpeed(speedKmh)}
        </text>
      </g>
    </g>
  );
};
