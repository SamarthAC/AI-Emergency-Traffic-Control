import { useEffect, useRef } from 'react'

const ROAD_PATHS = {
  A: 'M 150 150 Q 320 60 420 60 Q 520 60 620 150',
  B: 'M 150 150 L 620 150',
  C: 'M 150 150 Q 320 240 420 240 Q 520 240 620 150',
}

const ROAD_JUNCTION_POS = {
  A: [{ id: 'J1', x: 150, y: 150 }, { id: 'J2', x: 420, y: 60 }, { id: 'HOSPITAL', x: 620, y: 150 }],
  B: [{ id: 'J1', x: 150, y: 150 }, { id: 'J2', x: 330, y: 150 }, { id: 'J3', x: 500, y: 150 }, { id: 'HOSPITAL', x: 620, y: 150 }],
  C: [{ id: 'J1', x: 150, y: 150 }, { id: 'J4', x: 420, y: 240 }, { id: 'HOSPITAL', x: 620, y: 150 }],
}

function trafficColor(score) {
  if (score == null) return 'var(--border-strong)'
  if (score <= 30) return 'var(--green)'
  if (score <= 60) return 'var(--yellow)'
  if (score <= 100) return 'var(--red)'
  return 'var(--critical-red)'
}

export default function AmbulanceRoute({ roads, recommendation, selectedRoute, corridor, ambulanceProgress, phase }) {
  const pathRefs = { A: useRef(null), B: useRef(null), C: useRef(null) }
  const ambRef = useRef(null)

  useEffect(() => {
    if (!selectedRoute) return
    const pathEl = pathRefs[selectedRoute]?.current
    const ambEl = ambRef.current
    if (!pathEl || !ambEl) return
    const total = pathEl.getTotalLength()
    const point = pathEl.getPointAtLength(total * ambulanceProgress)
    ambEl.setAttribute('transform', `translate(${point.x}, ${point.y})`)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ambulanceProgress, selectedRoute, phase])

  const showAmbulance = selectedRoute && (phase === 'EN_ROUTE' || phase === 'ARRIVAL' || phase === 'COMPLETED')
  const staticAmbProgress = phase === 'COMPLETED' ? 1 : ambulanceProgress

  return (
    <div className="route-map-wrap">
      <svg viewBox="0 0 700 300" width="100%" style={{ display: 'block' }}>
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Patient + Hospital anchor labels */}
        <text x="40" y="145" fill="var(--text-secondary)" fontSize="11" fontFamily="IBM Plex Mono, monospace">PATIENT</text>
        <circle cx="150" cy="150" r="7" fill="var(--accent-blue)" />
        <text x="600" y="180" fill="var(--text-secondary)" fontSize="11" fontFamily="IBM Plex Mono, monospace" textAnchor="middle">🏥 HOSPITAL</text>

        {['A', 'B', 'C'].map((roadId) => {
          const data = roads[roadId]?.data
          const isSelected = selectedRoute === roadId
          const isRecommended = recommendation?.recommendedRoute === roadId
          const color = isSelected ? 'var(--green)' : trafficColor(data?.trafficScore)
          return (
            <g key={roadId}>
              <path
                ref={pathRefs[roadId]}
                d={ROAD_PATHS[roadId]}
                fill="none"
                stroke={color}
                strokeWidth={isSelected ? 6 : 3}
                strokeLinecap="round"
                opacity={isSelected ? 1 : 0.55}
                filter={isSelected ? 'url(#glow)' : undefined}
                style={{ transition: 'stroke 0.5s ease, stroke-width 0.3s ease' }}
              />
              <text
                x={roadId === 'B' ? 380 : 380}
                y={roadId === 'A' ? 45 : roadId === 'C' ? 262 : 140}
                fill={isSelected ? 'var(--green)' : 'var(--text-muted)'}
                fontSize="11"
                fontFamily="IBM Plex Mono, monospace"
                textAnchor="middle"
                fontWeight={isSelected ? 700 : 400}
              >
                ROAD {roadId}{isRecommended ? ' ★' : ''}
              </text>
              {ROAD_JUNCTION_POS[roadId]
                .filter((j) => j.id !== 'HOSPITAL' && j.id !== 'J1')
                .map((j) => {
                  const isGreenJ = corridor.active && isSelected && corridor.junctions.includes(j.id)
                  return (
                    <g key={j.id}>
                      <circle
                        cx={j.x}
                        cy={j.y}
                        r={6}
                        fill={isGreenJ ? 'var(--green)' : 'var(--bg-panel)'}
                        stroke={isGreenJ ? 'var(--green)' : 'var(--border-strong)'}
                        strokeWidth="1.5"
                      />
                      <text x={j.x} y={j.y - 12} fill="var(--text-muted)" fontSize="9" textAnchor="middle" fontFamily="IBM Plex Mono, monospace">
                        {j.id}
                      </text>
                    </g>
                  )
                })}
            </g>
          )
        })}

        <circle cx="620" cy="150" r="9" fill="var(--bg-panel)" stroke="var(--accent-blue)" strokeWidth="2" />

        {showAmbulance && (
          <g ref={ambRef} style={{ transition: 'transform 0.05s linear' }}>
            <text x="0" y="6" fontSize="20" textAnchor="middle">🚑</text>
          </g>
        )}
      </svg>
    </div>
  )
}
