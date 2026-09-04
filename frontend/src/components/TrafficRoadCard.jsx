import { useState } from 'react'

const CLASS_LABELS = {
  car: 'Cars',
  two_wheeler: 'Two-wheelers',
  auto: 'Autos',
  bus: 'Buses',
  truck: 'Trucks',
}

const LEVEL_EMOJI = { LOW: '🟢', MEDIUM: '🟡', HIGH: '🔴', SEVERE: '🔴' }

export default function TrafficRoadCard({ roadId, entry, isRecommended }) {
  const [view, setView] = useState('annotated')
  const { status, data } = entry

  return (
    <div className={`road-card ${isRecommended ? 'recommended' : ''}`}>
      <div className="road-card-header">
        <span className="road-card-title">ROAD {roadId}</span>
        {isRecommended && <span className="recommended-tag">RECOMMENDED</span>}
      </div>

      {status === 'idle' && (
        <div className="road-empty-state">
          BMD-45 image queued.
          <br />
          Awaiting AI traffic analysis.
        </div>
      )}

      {status === 'analyzing' && (
        <div className="road-empty-state">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <div className="spinner" />
            YOLO analyzing Road {roadId}...
          </div>
        </div>
      )}

      {status === 'done' && data && (
        <>
          <div className="road-image-wrap">
            <img src={view === 'annotated' ? data.annotatedImage : data.originalImage} alt={`Road ${roadId}`} />
            <span className="detection-badge">
              {data.mode === 'LIVE_YOLO' ? '● LIVE YOLO' : '○ DEMO'}
            </span>
            <div className="image-toggle">
              <button className={view === 'original' ? 'active' : ''} onClick={() => setView('original')}>
                ORIGINAL
              </button>
              <button className={view === 'annotated' ? 'active' : ''} onClick={() => setView('annotated')}>
                AI DETECTION
              </button>
            </div>
          </div>

          <div className="class-breakdown">
            {Object.entries(data.vehicleCounts).map(([cls, count]) => (
              <div className="class-breakdown-row" key={cls}>
                <span>{CLASS_LABELS[cls] || cls}</span>
                <b>{count}</b>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 14, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11.5, color: 'var(--text-secondary)' }}>
            <span>🚗 Vehicles: <b style={{ color: 'var(--text-primary)' }}>{data.totalVehicles}</b></span>
            <span>🚶 Peds: <b style={{ color: 'var(--text-primary)' }}>{data.pedestrians ?? 'N/A'}</b></span>
            <span>🚧 Obstacles: <b style={{ color: 'var(--text-primary)' }}>{data.obstacles ?? 'N/A'}</b></span>
          </div>

          <div className="traffic-score-row">
            <div>
              <div className="stat-label" style={{ marginBottom: 2 }}>Traffic Score</div>
              <div className="traffic-score-value">{data.trafficScore}</div>
            </div>
            <span className={`status-pill ${data.colorState}`}>
              {LEVEL_EMOJI[data.trafficLevel]} {data.trafficLevel}
            </span>
          </div>
        </>
      )}
    </div>
  )
}
