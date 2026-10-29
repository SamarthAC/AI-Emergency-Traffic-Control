import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { ConnectionStatusBanner } from '../system/ConnectionStatusBanner';
import { PickupReplanBanner } from '../mission/PickupReplanBanner';
import { CameraInspectorModal } from '../vision/CameraInspectorModal';
import { useDashboardSocket } from '../../hooks/useDashboardSocket';
import { Info } from 'lucide-react';

export const AppLayout: React.FC = () => {
  // Initialize resilient WebSocket lifecycle and REST hydration once at app root
  useDashboardSocket();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-800">
      {/* 1. Persistent Left Sidebar */}
      <Sidebar />

      {/* 2. Main Workspace (TopBar + Page Content + Footer) */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header */}
        <TopBar />

        {/* Global Connection / Status Banners */}
        <ConnectionStatusBanner />
        <PickupReplanBanner />

        {/* Dynamic Page Routed Content */}
        <main className="flex-1 overflow-y-auto p-5 lg:p-6 bg-[#F8FAFC]">
          <div className="max-w-[1720px] mx-auto w-full">
            <Outlet />
          </div>
        </main>

        {/* Academic Presentation Footer */}
        <footer className="py-2 px-6 bg-white border-t border-slate-200/80 text-center text-xs font-mono text-slate-600 flex items-center justify-center gap-2 shrink-0">
          <Info className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>
            Simulation-based research prototype using SUMO / TraCI. Validated Custom CNN traffic &amp; ambulance detection with dynamic A* rerouting.
          </span>
        </footer>
      </div>

      {/* Shared Camera Inspector Modal */}
      <CameraInspectorModal />
    </div>
  );
};
