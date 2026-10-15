import { useEffect, useRef, useCallback } from 'react';
import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi } from '../api/dashboardApi';
import { WebSocketEvent } from '../types/dashboard';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws';
const MIN_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 15000;
const BACKOFF_MULTIPLIER = 1.5;

export function useDashboardSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const backoffMsRef = useRef<number>(MIN_BACKOFF_MS);
  const isUnmountingRef = useRef<boolean>(false);

  const {
    setConnectionStatus,
    hydrateState,
    dispatchWsEvent,
    connectionStatus,
  } = useDashboardStore();

  const fetchLatestStateSnapshot = useCallback(async () => {
    try {
      const state = await dashboardApi.getState();
      hydrateState(state);
    } catch (err) {
      console.warn('Failed to fetch state snapshot on initial/reconnect load:', err);
    }
  }, [hydrateState]);

  const connect = useCallback(() => {
    if (isUnmountingRef.current) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    setConnectionStatus('CONNECTING');

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = async () => {
        if (isUnmountingRef.current) return;
        setConnectionStatus('CONNECTED');
        backoffMsRef.current = MIN_BACKOFF_MS; // reset backoff on success
        // Re-hydrate state upon successful connection / reconnection
        await fetchLatestStateSnapshot();
      };

      ws.onmessage = (event: MessageEvent) => {
        if (isUnmountingRef.current) return;
        try {
          const parsed = JSON.parse(event.data) as WebSocketEvent;
          dispatchWsEvent(parsed);
        } catch (err) {
          console.error('Failed to parse WebSocket message JSON:', err, event.data);
        }
      };

      ws.onclose = () => {
        if (isUnmountingRef.current) return;
        setConnectionStatus('RECONNECTING');
        scheduleReconnect();
      };

      ws.onerror = (err) => {
        if (isUnmountingRef.current) return;
        console.warn('WebSocket connection error:', err);
        ws.close();
      };
    } catch (err) {
      console.warn('WebSocket creation failed:', err);
      setConnectionStatus('RECONNECTING');
      scheduleReconnect();
    }
  }, [setConnectionStatus, fetchLatestStateSnapshot, dispatchWsEvent]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
    }

    const nextBackoff = Math.min(backoffMsRef.current * BACKOFF_MULTIPLIER, MAX_BACKOFF_MS);
    const delay = backoffMsRef.current;
    backoffMsRef.current = nextBackoff;

    reconnectTimeoutRef.current = window.setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);

  useEffect(() => {
    isUnmountingRef.current = false;
    // Step 1: Immediately fetch initial state
    fetchLatestStateSnapshot();
    // Step 2: Establish resilient WebSocket
    connect();

    return () => {
      isUnmountingRef.current = true;
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchLatestStateSnapshot, connect]);

  return {
    connectionStatus,
    reconnect: connect,
    refetchState: fetchLatestStateSnapshot,
  };
}
