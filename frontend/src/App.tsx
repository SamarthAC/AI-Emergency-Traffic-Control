import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { LiveSimulationPage } from './pages/LiveSimulationPage';
import { TrafficCamerasPage } from './pages/TrafficCamerasPage';
import { JunctionCamerasPage } from './pages/JunctionCamerasPage';
import { HospitalSelectionPage } from './pages/HospitalSelectionPage';
import { GreenCorridorPage } from './pages/GreenCorridorPage';
import { MetricsPage } from './pages/MetricsPage';
import { LogsPage } from './pages/LogsPage';
import { SystemPage } from './pages/SystemPage';

export function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/overview" element={<Navigate to="/" replace />} />
          <Route path="/simulation" element={<LiveSimulationPage />} />
          <Route path="/cameras" element={<TrafficCamerasPage />} />
          <Route path="/junction-cameras" element={<JunctionCamerasPage />} />
          <Route path="/hospitals" element={<HospitalSelectionPage />} />
          <Route path="/green-corridor" element={<GreenCorridorPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/system" element={<SystemPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
