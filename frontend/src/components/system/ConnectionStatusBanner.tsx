import React from 'react';
import { WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';

export const ConnectionStatusBanner: React.FC = () => {
  const { connectionStatus } = useDashboardStore();

  if (connectionStatus === 'CONNECTED') return null;

  return (
    <div
      className={`px-4 py-2 text-xs font-mono flex items-center justify-between transition-all ${
        connectionStatus === 'OFFLINE'
          ? 'bg-red-950/90 border-b border-red-500/60 text-red-300'
          : 'bg-amber-950/90 border-b border-amber-500/60 text-amber-300'
      }`}
    >
      <div className="flex items-center gap-2">
        {connectionStatus === 'OFFLINE' ? (
          <WifiOff className="w-4 h-4 text-red-400 shrink-0" />
        ) : (
          <RefreshCw className="w-4 h-4 text-amber-400 animate-spin shrink-0" />
        )}
        <span>
          {connectionStatus === 'OFFLINE'
            ? 'Backend Offline — Unable to reach FastAPI server at http://127.0.0.1:8000.'
            : 'Live Feed Reconnecting… Attempting automatic bounded backoff reconnect to ws://127.0.0.1:8000/ws.'}
        </span>
      </div>

      <span className="text-[10px] text-slate-400 hidden sm:inline">
        Automatic state recovery on link re-establishment
      </span>
    </div>
  );
};
