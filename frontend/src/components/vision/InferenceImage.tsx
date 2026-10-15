import React, { useState, useEffect, useRef } from 'react';
import { ImageOff, ZoomIn } from 'lucide-react';
import { cn } from '../../utils/formatters';

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
  confidence?: number;
}

interface InferenceImageProps {
  src: string | null;
  fallbackSrc?: string | null;
  alt: string;
  detections?: BoundingBox[];
  className?: string;
  aspectRatio?: 'video' | 'square' | 'wide' | 'auto';
  onClick?: () => void;
  badge?: string;
  isDemoSample?: boolean;
}

export const InferenceImage: React.FC<InferenceImageProps> = ({
  src,
  fallbackSrc,
  alt,
  detections = [],
  className,
  aspectRatio = 'video',
  onClick,
  badge,
  isDemoSample = false,
}) => {
  const [displayedSrc, setDisplayedSrc] = useState<string | null>(src);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const currentLoadingSrc = useRef<string | null>(null);

  useEffect(() => {
    if (!src) {
      setHasError(true);
      setIsLoading(false);
      return;
    }

    currentLoadingSrc.current = src;

    // Preload newly versioned image before swapping to reduce flicker
    const img = new Image();
    img.src = src;

    img.onload = () => {
      if (currentLoadingSrc.current === src) {
        setDisplayedSrc(src);
        setHasError(false);
        setIsLoading(false);
      }
    };

    img.onerror = () => {
      // Try fallbackSrc if available
      if (fallbackSrc && fallbackSrc !== src) {
        const fallbackImg = new Image();
        fallbackImg.src = fallbackSrc;
        fallbackImg.onload = () => {
          if (currentLoadingSrc.current === src) {
            setDisplayedSrc(fallbackSrc);
            setHasError(false);
            setIsLoading(false);
          }
        };
        fallbackImg.onerror = () => {
          if (currentLoadingSrc.current === src) {
            setHasError(true);
            setIsLoading(false);
          }
        };
      } else {
        if (currentLoadingSrc.current === src) {
          setHasError(true);
          setIsLoading(false);
        }
      }
    };
  }, [src, fallbackSrc]);

  const aspectStyles = {
    video: 'aspect-video',
    square: 'aspect-square',
    wide: 'aspect-[21/9]',
    auto: 'h-auto',
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative bg-slate-950 rounded border border-command-border/80 overflow-hidden group select-none',
        aspectStyles[aspectRatio],
        onClick && 'cursor-pointer hover:border-cyan-500/60 transition-colors',
        className
      )}
    >
      {/* Corner UI Accents */}
      <div className="absolute top-1 left-1 w-2 h-2 border-t border-l border-cyan-400/60 z-10 pointer-events-none" />
      <div className="absolute top-1 right-1 w-2 h-2 border-t border-r border-cyan-400/60 z-10 pointer-events-none" />
      <div className="absolute bottom-1 left-1 w-2 h-2 border-b border-l border-cyan-400/60 z-10 pointer-events-none" />
      <div className="absolute bottom-1 right-1 w-2 h-2 border-b border-r border-cyan-400/60 z-10 pointer-events-none" />

      {/* Badges */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-1.5 pointer-events-none">
        {badge && (
          <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-sm border border-slate-700/80 text-[10px] font-mono text-cyan-400 font-semibold shadow-sm">
            {badge}
          </span>
        )}
        {isDemoSample && (
          <span className="px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-600/60 text-[9px] font-mono text-amber-300 shadow-sm">
            Demo Camera Frame
          </span>
        )}
      </div>

      {onClick && (
        <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-black/70 p-1 rounded text-cyan-400">
          <ZoomIn className="w-3.5 h-3.5" />
        </div>
      )}

      {displayedSrc && !hasError ? (
        <>
          <img
            src={displayedSrc}
            alt={alt}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />

          {/* SVG Overlay for Real Bounding Boxes (ONLY if backend supplied coordinates) */}
          {detections.length > 0 && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-10" viewBox="0 0 100 100">
              {detections.map((box, i) => (
                <g key={i}>
                  <rect
                    x={box.x}
                    y={box.y}
                    width={box.width}
                    height={box.height}
                    fill="none"
                    stroke="#00F0FF"
                    strokeWidth="1.5"
                    strokeDasharray="2 1"
                  />
                  {box.label && (
                    <text
                      x={box.x}
                      y={Math.max(4, box.y - 2)}
                      fill="#00F0FF"
                      fontSize="3.5"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {box.label} {box.confidence ? `${Math.round(box.confidence * 100)}%` : ''}
                    </text>
                  )}
                </g>
              ))}
            </svg>
          )}

          {isLoading && !displayedSrc && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
              <div className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
            </div>
          )}
        </>
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950/90 text-slate-500 p-4 text-center">
          <ImageOff className="w-8 h-8 mb-2 opacity-50 text-slate-400" />
          <span className="text-xs font-mono">Camera image unavailable</span>
          <span className="text-[10px] text-slate-600 font-mono mt-0.5">{alt}</span>
        </div>
      )}
    </div>
  );
};
