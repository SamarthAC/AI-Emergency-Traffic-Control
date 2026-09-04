// Thin wrapper around the FastAPI backend. All calls go through Vite's
// /api proxy (see vite.config.js) which forwards to http://localhost:8000.

const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch (_) {
      /* ignore parse errors */
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function getSystemStatus() {
  const res = await fetch(`${BASE}/status`)
  return handle(res)
}

export async function analyzeTraffic(roadId) {
  const res = await fetch(`${BASE}/analyze-traffic?road_id=${roadId}`, {
    method: 'POST',
  })
  return handle(res)
}

export async function optimizeRoute(roads) {
  const res = await fetch(`${BASE}/optimize-route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roads }),
  })
  return handle(res)
}

export async function activateGreenCorridor(route) {
  const res = await fetch(`${BASE}/activate-green-corridor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ route }),
  })
  return handle(res)
}

export async function getHospitals(routeCost = 0, routeTrafficScore = 0) {
  const res = await fetch(
    `${BASE}/hospitals?route_cost=${routeCost}&route_traffic_score=${routeTrafficScore}`
  )
  return handle(res)
}

// ---------------------------------------------------------------------
// SUMO Simulation page
// ---------------------------------------------------------------------

export async function getSumoStatus() {
  const res = await fetch(`${BASE}/sumo/status`)
  return handle(res)
}

export async function getSumoNetwork() {
  const res = await fetch(`${BASE}/sumo/network`)
  return handle(res)
}

export async function startSumoSimulation(roadId, roadTrafficScores) {
  const res = await fetch(`${BASE}/sumo/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roadId, roadTrafficScores }),
  })
  return handle(res)
}

export async function stopSumoSimulation() {
  const res = await fetch(`${BASE}/sumo/stop`, { method: 'POST' })
  return handle(res)
}

export async function getSumoState() {
  const res = await fetch(`${BASE}/sumo/state`)
  return handle(res)
}
