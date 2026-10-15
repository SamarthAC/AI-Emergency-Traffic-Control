import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(seconds?: number | null): string {
  if (seconds === undefined || seconds === null) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function formatDistance(meters?: number | null): string {
  if (meters === undefined || meters === null) return '-- m';
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(2)} km`;
  }
  return `${meters.toFixed(0)} m`;
}

export function formatSpeed(speedKmh?: number | null): string {
  if (speedKmh === undefined || speedKmh === null) return '-- km/h';
  return `${speedKmh.toFixed(1)} km/h`;
}

export function getTrafficColor(level?: string | null) {
  switch (level?.toUpperCase()) {
    case 'LOW':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/30',
        dot: 'bg-emerald-400',
        hex: '#10B981',
      };
    case 'MEDIUM':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/30',
        dot: 'bg-amber-400',
        hex: '#F59E0B',
      };
    case 'HIGH':
      return {
        bg: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/30',
        dot: 'bg-red-400',
        hex: '#EF4444',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/30',
        dot: 'bg-slate-400',
        hex: '#64748B',
      };
  }
}
