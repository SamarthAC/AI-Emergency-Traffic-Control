import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import * as api from '../services/api.js'

const ROAD_IDS = ['A', 'B', 'C']
const VIEW_W = 900
const VIEW_H = 420
const LEFT_X = 90
const RIGHT_X = 810
const MID_Y = 210

// One lane offset per road so the three paths fan out and reconverge at
// J1 / HOSPITAL, purely from the junction list the API returns — no
// hardcoded topology assumptions.
const LANE_OFFSET = { A: 0, B: -130, C: 130 }
const ROAD_COLOR = { A: 'var(--accent-blue)', B: 'var(--purple)', C: '#4dd0e1' }

function layoutRoute(junctions, roadId) {
  const n = junctions.length
  const offset = LANE_OFFSET[roadId] ?? 0
  return junctions.map((id, i) => {
    const t = n > 1 ? i / (n - 1) : 0
    const x = LEFT_X + (RIGHT_X - LEFT_X) * t
    const y = MID_Y + offset * Math.sin(Math.PI * t)
    return { id, x, y }
  })
}

export default function RoutingPage() {
  const [searchParams] = useSearchParams()
  const initialScores = useMemo(() => {
    const scores = {}
    for (const id of ROAD_IDS) {
      const v = searchParams.get(`score${id}`)
      scores[id] = v != null ? Number(v) : 20
    }
    return scores
  }, [searchParams])

  const [scores, setScores] = useState(initialScores)
  const [recommendation, setRecommendation] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    const roads = ROAD_IDS.map((id) => ({ id, trafficScore: scores[id] }))
    api.optimizeRoute(roads)
      .then((data) => { if (!cancelled) setRecommendation(data) })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scores.A, scores.B, scores.C])

  const layouts = useMemo(() => {
    if (!recommendation) return {}
    const map = {}
    for (const route of recommendation.routes) {
      map[route.id] = layoutRoute(route.junctions, route.id)
    }
    return map
  }, [recommendation])

  return (
    <div className="app-shell">
      <div className="tool-page-header">
        <Link to="/" className="back-link">← Dashboard</Link>
        <div>
          <div className="header-title">🧭 ROUTING VIEW</div>
          <div className="header-subtitle">LIVE WEIGHTED DIJKSTRA ROUTE GRAPH</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title"><span className="emoji">🎚</span> TRAFFIC SCORE INPUTS</div>
        <div className="routing-sliders">
          {ROAD_IDS.map((id) => (
            <div key={id} className="routing-slider-row">
              <span className="routing-slider-label" style={{ color: ROAD_COLOR[id] }}>Road {id}</span>
              <input
                type="range"
                min={0}
                max={150}
                value={scores[id]}
                onChange={(e) => setScores((prev) => ({ ...prev, [id]: Number(e.target.value) }))}
              />
              <span className="routing-slider-value">{scores[id]}</span>
            </div>
          ))}
        </div>
        <div className="empty-hint" style={{ marginTop: 8 }}>
          Drag a slider to see the recommended route recompute live via /api/optimize-route.
        </div>
      </div>

      {error && <div className="error-banner">⚠ {error}</div>}

      <div className="card">
        <div className="card-title"><span className="emoji">🗺</span> ROUTE GRAPH</div>
        {loading && !recommendation ? (
          <div className="empty-hint">Loading…</div>
        ) : recommendation && (
          <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className="sumo-svg">
            {ROAD_IDS.map((id) => {
              const points = layouts[id]
              if (!points) return null
              const isBest = recommendation.recommendedRoute === id
              const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
              return (
                <path
                  key={id}
                  d={d}
                  fill="none"
                  stroke={isBest ? 'var(--green)' : ROAD_COLOR[id]}
                  strokeWidth={isBest ? 6 : 3}
                  opacity={isBest ? 1 : 0.55}
                  strokeLinecap="round"
                />
              )
            })}

            {ROAD_IDS.map((id) => (layouts[id] || []).map((p, i) => (
              <g key={`${id}-${p.id}-${i}`}>
                <circle cx={p.x} cy={p.y} r={p.id === 'J1' || p.id === 'HOSPITAL' ? 10 : 7}
                  fill={recommendation.recommendedRoute === id ? 'var(--green)' : ROAD_COLOR[id]} />
                <text x={p.x} y={p.y - 16} textAnchor="middle" className="sumo-node-label">{p.id}</text>
              </g>
            )))}

            {ROAD_IDS.map((id) => {
              const route = recommendation.routes.find((r) => r.id === id)
              const points = layouts[id]
              if (!route || !points || points.length < 2) return null
              const mid = points[Math.floor(points.length / 2)]
              return (
                <text
                  key={`label-${id}`}
                  x={mid.x}
                  y={mid.y + (LANE_OFFSET[id] < 0 ? -30 : LANE_OFFSET[id] > 0 ? 42 : 30)}
                  textAnchor="middle"
                  className="routing-edge-label"
                  fill={recommendation.recommendedRoute === id ? 'var(--green)' : ROAD_COLOR[id]}
                >
                  Road {id} · cost {route.edgeCost} · {route.etaMinutes} min
                </text>
              )
            })}
          </svg>
        )}
      </div>

      {recommendation && (
        <div className="card">
          <div className="card-title"><span className="emoji">📊</span> ROUTE COMPARISON</div>
          <table className="routing-table">
            <thead>
              <tr>
                <th>Road</th>
                <th>Traffic score</th>
                <th>Edge cost</th>
                <th>Distance</th>
                <th>ETA</th>
                <th>Junctions</th>
              </tr>
            </thead>
            <tbody>
              {[...recommendation.routes].sort((a, b) => a.id.localeCompare(b.id)).map((r) => (
                <tr key={r.id} className={r.id === recommendation.recommendedRoute ? 'best-row' : ''}>
                  <td style={{ color: ROAD_COLOR[r.id] }}>Road {r.id}</td>
                  <td>{r.trafficScore}</td>
                  <td>{r.edgeCost}</td>
                  <td>{r.distanceKm} km</td>
                  <td>{r.etaMinutes} min</td>
                  <td>{r.junctions.join(' → ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="recommendation-banner" style={{ marginTop: 14 }}>
            <div>
              <div className="route-name">🚑 ROAD {recommendation.recommendedRoute}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
                {recommendation.reason}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
