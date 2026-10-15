import React from 'react';
import { cn } from '../../utils/formatters';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'cyan' | 'emerald' | 'amber' | 'red' | 'slate' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'slate',
  size = 'md',
  className,
  pulse = false,
}) => {
  const variantStyles = {
    cyan: 'bg-cyan-950/60 border-cyan-500/40 text-cyan-400 shadow-cyan-950/20',
    emerald: 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400 shadow-emerald-950/20',
    amber: 'bg-amber-950/60 border-amber-500/40 text-amber-400 shadow-amber-950/20',
    red: 'bg-red-950/60 border-red-500/40 text-red-400 shadow-red-950/20',
    slate: 'bg-slate-800/80 border-slate-700/60 text-slate-300',
    purple: 'bg-purple-950/60 border-purple-500/40 text-purple-400 shadow-purple-950/20',
  };

  const sizeStyles = {
    sm: 'px-1.5 py-0.5 text-[10px] font-mono tracking-wider',
    md: 'px-2.5 py-1 text-xs font-mono font-medium tracking-wide',
    lg: 'px-3 py-1.5 text-sm font-semibold tracking-wide',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded border uppercase tracking-wider transition-all',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span
            className={cn(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              variant === 'cyan' && 'bg-cyan-400',
              variant === 'emerald' && 'bg-emerald-400',
              variant === 'amber' && 'bg-amber-400',
              variant === 'red' && 'bg-red-400',
              variant === 'slate' && 'bg-slate-400',
              variant === 'purple' && 'bg-purple-400'
            )}
          />
          <span
            className={cn(
              'relative inline-flex rounded-full h-2 w-2',
              variant === 'cyan' && 'bg-cyan-500',
              variant === 'emerald' && 'bg-emerald-500',
              variant === 'amber' && 'bg-amber-500',
              variant === 'red' && 'bg-red-500',
              variant === 'slate' && 'bg-slate-500',
              variant === 'purple' && 'bg-purple-500'
            )}
          />
        </span>
      )}
      {children}
    </span>
  );
};
