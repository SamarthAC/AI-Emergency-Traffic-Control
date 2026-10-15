import React from 'react';
import { cn } from '../../utils/formatters';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'emerald' | 'amber' | 'red' | 'none';
  header?: React.ReactNode;
  title?: string;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  glow = 'none',
  header,
  title,
  badge,
  icon,
}) => {
  const glowStyles = {
    none: 'border-command-border/80 shadow-lg',
    cyan: 'border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.15)]',
    emerald: 'border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.15)]',
    amber: 'border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.15)]',
    red: 'border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]',
  };

  return (
    <div
      className={cn(
        'bg-command-panel/90 backdrop-blur-md rounded-lg border flex flex-col transition-all overflow-hidden',
        glowStyles[glow],
        className
      )}
    >
      {(header || title) && (
        <div className="px-3.5 py-2.5 bg-command-surface/80 border-b border-command-border/60 flex items-center justify-between gap-2">
          {header ? (
            header
          ) : (
            <>
              <div className="flex items-center gap-2 min-w-0">
                {icon && <span className="text-cyan-400 shrink-0">{icon}</span>}
                {title && (
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 truncate">
                    {title}
                  </h3>
                )}
              </div>
              {badge && <div className="shrink-0">{badge}</div>}
            </>
          )}
        </div>
      )}
      <div className="p-3.5 flex-1 flex flex-col">{children}</div>
    </div>
  );
};
