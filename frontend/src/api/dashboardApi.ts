import { DashboardStateSnapshot, ImageManifest } from '../types/dashboard';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const dashboardApi = {
  async getHealth(): Promise<{ status: string; connected_clients: number }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  async getState(): Promise<DashboardStateSnapshot> {
    const res = await fetch(`${API_BASE_URL}/api/state`);
    if (!res.ok) throw new Error(`Failed to fetch state snapshot: ${res.statusText}`);
    return res.json();
  },

  async getAmbulance() {
    const res = await fetch(`${API_BASE_URL}/api/ambulance`);
    if (!res.ok) throw new Error(`Failed to fetch ambulance: ${res.statusText}`);
    return res.json();
  },

  async getRoute() {
    const res = await fetch(`${API_BASE_URL}/api/route`);
    if (!res.ok) throw new Error(`Failed to fetch route: ${res.statusText}`);
    return res.json();
  },

  async getHospital() {
    const res = await fetch(`${API_BASE_URL}/api/hospital`);
    if (!res.ok) throw new Error(`Failed to fetch hospital: ${res.statusText}`);
    return res.json();
  },

  async getTraffic() {
    const res = await fetch(`${API_BASE_URL}/api/traffic`);
    if (!res.ok) throw new Error(`Failed to fetch traffic: ${res.statusText}`);
    return res.json();
  },

  async getSignals() {
    const res = await fetch(`${API_BASE_URL}/api/signals`);
    if (!res.ok) throw new Error(`Failed to fetch signals: ${res.statusText}`);
    return res.json();
  },

  async getCorridor() {
    const res = await fetch(`${API_BASE_URL}/api/corridor`);
    if (!res.ok) throw new Error(`Failed to fetch corridor: ${res.statusText}`);
    return res.json();
  },

  async getJunctionCameras() {
    const res = await fetch(`${API_BASE_URL}/api/junction-cameras`);
    if (!res.ok) throw new Error(`Failed to fetch junction cameras: ${res.statusText}`);
    return res.json();
  },

  async getMetrics() {
    const res = await fetch(`${API_BASE_URL}/api/metrics`);
    if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.statusText}`);
    return res.json();
  },

  async getLogs() {
    const res = await fetch(`${API_BASE_URL}/api/logs`);
    if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`);
    return res.json();
  },

  async getImageManifest(): Promise<ImageManifest> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/images/manifest`);
      if (!res.ok) return {};
      return res.json();
    } catch {
      return {};
    }
  },

  async reset(): Promise<{ reset: boolean }> {
    const res = await fetch(`${API_BASE_URL}/api/reset`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to reset: ${res.statusText}`);
    return res.json();
  },
};
