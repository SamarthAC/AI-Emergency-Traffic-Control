import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import * as api from '../services/api.js'

const ROAD_IDS = ['A', 'B', 'C']
const POLL_MS = 300

const VEHICLE_COLORS = {
  car: '#8a93ad',
  two_wheeler: '#ffcf4d',
  bus: '#4da3ff',
  truck: '#c98a4d',
}

const VIEW_W = 900
const VIEW_H = 460
const PAD = 40

function tlsColor(state) {
  if (!state) return 'var(--text-muted)'
  if (state.includes('G')) return 'var(--green)'
  if (state.includes('y')) return 'var(--yellow)'
  return 'var(--red)'
}

export default function SumoSimulationPage() {
  const [searchParams] = useSearchParams()
  const initialRoad = (searchParams.get('road') || 'A').toUpperCase()
  const roadScores = useMemo(() => {
    const scores = {}
    for (const id of ROAD_IDS) {
      const v = searchParams.get(`score${id}`)
      if (v != null) scores[id] = Number(v)
    }
    return scores
  }, [searchParams])

  const [status, setStatus] = useState(null)      // /api/sumo/status
  const [network, setNetwork] = useState(null)     // /api/sumo/network
  const [roadId, setRoadId] = useState(ROAD_IDS.includes(initialRoad) ? initialRoad : 'A')
  const [simState, setSimState] = useState(null)   // /api/sumo/state
  const [error, setError] = useState(null)
  const [starting, setStarting] = useState(false)

  const pollRef = useRef(null)

  useEffect(() => {
    api.getSumoStatus().then(setStatus).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (status?.mode === 'LIVE_SUMO') {
      api.getSumoNetwork().then(setNetwork).catch((e) => setError(e.message))
    }
  }, [status])

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const s = await api.getSumoState()
        setSimState(s)
        if (!s.running) stopPolling()
      } catch (e) {
        setError(e.message)
        stopPolling()
      }
    }, POLL_MS)
  }, [stopPolling])

  useEffect(() => stopPolling, [stopPolling])

  const handleStart = async () => {
    setError(null)
    setStarting(true)
    try {
      await api.startSumoSimulation(roadId, roadScores)
      startPolling()
    } catch (e) {
      setError(e.message)
    } finally {
      setStarting(false)
    }
  }

  const handleStop = async () => {
    try {
      await api.stopSumoSimulation()
    } catch (e) {
      setError(e.message)
    } finally {
      stopPolling()
      setSimState((prev) => (prev ? { ...prev, running: false } : prev))
    }
  }

  // --- world -> SVG coordinate transform -------------------------------
  const transform = useMemo(() => {
    if (!network) return null
    const { xmin, ymin, xmax, ymax } = network.boundary
    const w = Math.max(1, xmax - xmin)
    const h = Math.max(1, ymax - ymin)
    const scale = Math.min((VIEW_W - PAD * 2) / w, (VIEW_H - PAD * 2) / h)
    const toSvg = (x, y) => [
      (x - xmin) * scale + PAD,
      VIEW_H - ((y - ymin) * scale + PAD), // flip Y so "north" reads upward
    ]
    return toSvg
  }, [network])

  const tlsStateById = useMemo(() => {
    const map = {}
    for (const t of simState?.trafficLights || []) map[t.id] = t.state
    return map
  }, [simState])

  const unavailable = status && status.mode !== 'LIVE_SUMO'

  return (
    <div className="app-shell">
      <div className="tool-page-header">
        <Link to="/" className="back-link">← Dashboard</Link>
        <div>
          <div className="header-title">🚦 SUMO SIMULATION</div>
          <div className="header-subtitle">LIVE TRACI-DRIVEN MICROSCOPIC TRAFFIC SIMULATION</div>
        </div>
      </div>

      {!status && <div className="card empty-hint">Checking SUMO availability…</div>}

      {unavailable && (
        <div className="card">
          <div className="card-title"><span className="emoji">⚠</span> SUMO NOT AVAILABLE</div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{status.message}</p>
          <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12.5 }}>
            Install with:<br />
            <code>pip install eclipse-sumo traci sumolib</code><br />
            then restart the backend. No separate system SUMO install is required —
            <code>eclipse-sumo</code> bundles the binaries for Linux/Windows/macOS.
          </p>
        </div>
      )}

      {status?.mode === 'LIVE_SUMO' && (
        <>
          <div className="card">
            <div className="card-title"><span className="emoji">🎛</span> SIMULATION CONTROLS</div>
            <div className="sumo-controls">
              <div className="sumo-road-select">
                {ROAD_IDS.map((id) => (
                  <button
                    key={id}
                    className={`sumo-road-btn ${roadId === id ? 'active' : ''}`}
                    disabled={simState?.running}
                    onClick={() => setRoadId(id)}
                  >
                    Road {id}
                    {roadScores[id] != null && (
                      <span className="sumo-road-score"> · score {roadScores[id]}</span>
                    )}
                  </button>
                ))}
              </div>
              {!simState?.running ? (
                <button className="btn btn-accent" disabled={starting} onClick={handleStart}>
                  {starting ? 'Starting…' : '▶ Start Simulation'}
                </button>
              ) : (
                <button className="btn btn-primary" onClick={handleStop}>■ Stop Simulation</button>
              )}
            </div>
            {error && <div className="error-banner" style={{ marginTop: 12 }}>⚠ {error}</div>}
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-title"><span className="emoji">🗺</span> LIVE NETWORK</div>
              {!network ? (
                <div className="empty-hint">Loading network geometry…</div>
              ) : (
                <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className="sumo-svg">
                  {transform && network.edges.map((edge) => {
                    const points = edge.shape.map(([x, y]) => transform(x, y).join(',')).join(' ')
                    return (
                      <polyline
                        key={edge.id}
                        points={points}
                        fill="none"
                        stroke="var(--border-strong)"
                        strokeWidth={Math.max(2, edge.numLanes * 3)}
                        strokeLinecap="round"
                      />
                    )
                  })}

                  {transform && network.junctions.map((j) => {
                    const [sx, sy] = transform(j.x, j.y)
                    const color = j.hasTLS ? tlsColor(tlsStateById[j.id]) : 'var(--text-muted)'
                    const isHeld = simState?.greenCorridorActive && simState?.ambulance?.nextTLS?.id === j.id
                    return (
                      <g key={j.id}>
                        {isHeld && <circle cx={sx} cy={sy} r={16} fill="none" stroke="var(--green)" strokeWidth={2} opacity={0.6} />}
                        <circle cx={sx} cy={sy} r={j.hasTLS ? 8 : 5} fill={color} />
                        <text x={sx} y={sy - 12} textAnchor="middle" className="sumo-node-label">{j.id}</text>
                      </g>
                    )
                  })}

                  {transform && (simState?.vehicles || []).map((v) => {
                    const [sx, sy] = transform(v.x, v.y)
                    return (
                      <circle key={v.id} cx={sx} cy={sy} r={2.6} fill={VEHICLE_COLORS[v.type] || '#8a93ad'} opacity={0.85} />
                    )
                  })}

                  {transform && simState?.ambulance?.present && (
                    (() => {
                      const [sx, sy] = transform(simState.ambulance.x, simState.ambulance.y)
                      return (
                        <g>
                          <circle cx={sx} cy={sy} r={9} fill="none" stroke="var(--red)" strokeWidth={2} opacity={0.5}>
                            <animate attributeName="r" values="7;13;7" dur="1.2s" repeatCount="indefinite" />
                            <animate attributeName="opacity" values="0.6;0.05;0.6" dur="1.2s" repeatCount="indefinite" />
                          </circle>
                          <circle cx={sx} cy={sy} r={5.5} fill="var(--red)" stroke="#fff" strokeWidth={1} />
                        </g>
                      )
                    })()
                  )}
                </svg>
              )}
              <div className="sumo-legend">
                <span><i className="dot" style={{ background: 'var(--red)' }} /> Ambulance</span>
                <span><i className="dot" style={{ background: VEHICLE_COLORS.car }} /> Car</span>
                <span><i className="dot" style={{ background: VEHICLE_COLORS.two_wheeler }} /> Two-wheeler</span>
                <span><i className="dot" style={{ background: VEHICLE_COLORS.bus }} /> Bus</span>
                <span><i className="dot" style={{ background: VEHICLE_COLORS.truck }} /> Truck</span>
              </div>
            </div>

            <div className="card">
              <div className="card-title"><span className="emoji">🚑</span> AMBULANCE STATUS</div>
              {!simState ? (
                <div className="empty-hint">Start the simulation to see live ambulance telemetry.</div>
              ) : simState.ambulance?.arrived ? (
                <div className="recommendation-banner">
                  <div className="route-name" style={{ color: 'var(--green)' }}>✓ ARRIVED AT HOSPITAL</div>
                </div>
              ) : simState.ambulance?.present ? (
                <div className="sumo-stat-list">
                  <div className="sumo-stat-row"><span>Road</span><b>{simState.roadId}</b></div>
                  <div className="sumo-stat-row"><span>Sim time</span><b>{simState.simTime}s</b></div>
                  <div className="sumo-stat-row"><span>Current edge</span><b>{simState.ambulance.edge}</b></div>
                  <div className="sumo-stat-row"><span>Speed</span><b>{simState.ambulance.speedMps} m/s</b></div>
                  <div className="sumo-stat-row">
                    <span>Route progress</span>
                    <b>{Math.round(simState.ambulance.routeProgress * 100)}%</b>
                  </div>
                  {simState.ambulance.nextTLS && (
                    <div className="sumo-stat-row">
                      <span>Next signal</span>
                      <b>{simState.ambulance.nextTLS.id} — {Math.round(simState.ambulance.nextTLS.distanceM)}m</b>
                    </div>
                  )}
                  <div className={`corridor-active-banner ${simState.greenCorridorActive ? 'active' : 'standby'}`} style={{ marginTop: 10 }}>
                    {simState.greenCorridorActive ? 'GREEN CORRIDOR PREEMPTION ACTIVE' : 'NORMAL SIGNAL TIMING'}
                  </div>
                </div>
              ) : (
                <div className="empty-hint">Ambulance queued to depart…</div>
              )}
              <div className="empty-hint" style={{ marginTop: 14 }}>
                {(simState?.vehicles?.length ?? 0)} background vehicles in simulation.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
