import React from 'react';
import { CameraDefinition } from '../../types/dashboard';
import { getTrafficColor } from '../../utils/formatters';

interface TrafficCameraMarkerProps {
  camera: CameraDefinition;
  x: number;
  y: number;
  trafficLevel?: string;
  trafficScore?: number;
  isSelected?: boolean;
  isJunctionCamActive?: boolean;
  onClick: () => void;
}

export const TrafficCameraMarker: React.FC<TrafficCameraMarkerProps> = ({
  camera,
  x,
  y,
  trafficLevel = 'LOW',
  trafficScore = 0,
  isSelected = false,
  isJunctionCamActive = false,
  onClick,
}) => {
  const color = getTrafficColor(trafficLevel);
  const isJunctionCam = camera.type === 'junction' || camera.id.startsWith('JCAM');

  return (
    <g
      transform={`translate(${x}, ${y})`}
      onClick={onClick}
      className="cursor-pointer group select-none"
    >
      {/* Field of view cone indicator */}
      <path
        d="M 0 0 L -18 -26 L 18 -26 Z"
        fill={isJunctionCam ? 'rgba(16, 185, 129, 0.15)' : color.hex}
        opacity={isSelected ? 0.35 : 0.15}
        className="transition-opacity group-hover:opacity-40"
      />

      {/* Outer Pulse if active detection or selected */}
      {(isSelected || isJunctionCamActive) && (
        <circle
          r="16"
          className={
            isJunctionCam
              ? 'stroke-emerald-400 fill-emerald-500/20 animate-ping-slow'
              : 'stroke-cyan-400 fill-cyan-500/20 animate-ping-slow'
          }
          strokeWidth="1.5"
        />
      )}

      {/* Main Camera Housing */}
      <circle
        r="11"
        fill="#0E1524"
        stroke={isSelected ? '#00F0FF' : isJunctionCam ? '#10B981' : color.hex}
        strokeWidth={isSelected ? '2.5' : '1.5'}
        className="transition-all group-hover:scale-110"
      />

      {/* Inner Lens */}
      <circle
        r="4.5"
        fill={isJunctionCam ? '#10B981' : color.hex}
        className={isJunctionCamActive ? 'animate-pulse' : ''}
      />

      {/* Label Badge on Hover or Selection */}
      <g
        transform="translate(0, -32)"
        className={`transition-opacity duration-200 ${
          isSelected ? 'opacity-100' : 'opacity-80 group-hover:opacity-100'
        }`}
      >
        <rect
          x="-38"
          y="-11"
          width="76"
          height="15"
          rx="3"
          fill="#0B0F19"
          stroke={isSelected ? '#00F0FF' : color.hex}
          strokeWidth="1"
          opacity="0.95"
        />
        <text
          x="0"
          y="0"
          textAnchor="middle"
          fill={isSelected ? '#00F0FF' : '#E2E8F0'}
          fontSize="8"
          fontFamily="monospace"
          fontWeight="bold"
        >
          {camera.id}
        </text>
      </g>
    </g>
  );
};
