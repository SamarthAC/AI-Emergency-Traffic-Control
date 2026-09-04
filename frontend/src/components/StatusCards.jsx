function colorFor(level) {
  if (level === 'LOW') return 'green'
  if (level === 'MEDIUM') return 'yellow'
  if (level === 'HIGH' || level === 'SEVERE') return 'red'
  return 'muted'
}

export default function StatusCards({
  ambulanceId,
  ambulanceStatus,
  priority,
  recommendation,
  selectedRoute,
  corridor,
  eta,
}) {
  const selectedRouteData = recommendation?.routes?.find((r) => r.id === selectedRoute)
  const trafficLevel = selectedRouteData
    ? selectedRouteData.trafficScore <= 30
      ? 'LOW'
      : selectedRouteData.trafficScore <= 60
      ? 'MEDIUM'
      : selectedRouteData.trafficScore <= 100
      ? 'HIGH'
      : 'SEVERE'
    : null

  return (
    <div className="grid-status">
      <div className="stat-card">
        <div className="stat-label">Ambulance</div>
        <div className="stat-value blue">{ambulanceId}</div>
        <div className="status-pill neutral">{ambulanceStatus}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Priority</div>
        <div className={`stat-value ${priority ? 'red' : 'muted'}`}>{priority || '—'}</div>
        <div className="status-pill neutral">{priority ? 'ACCIDENT' : 'AWAITING'}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Traffic</div>
        <div className={`stat-value ${colorFor(trafficLevel)}`}>
          {selectedRouteData ? `${selectedRouteData.trafficScore}` : '—'}
        </div>
        <div className={`status-pill ${trafficLevel ? colorFor(trafficLevel) : 'neutral'}`}>
          {trafficLevel || 'PENDING'}
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Green Corridor</div>
        <div className={`stat-value ${corridor.active ? 'green' : 'muted'}`}>
          {corridor.active ? 'ACTIVE' : 'STANDBY'}
        </div>
        <div className={`status-pill ${corridor.active ? 'green' : 'neutral'}`}>
          {corridor.junctions.length ? `${corridor.junctions.length} JUNCTIONS` : 'IDLE'}
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">ETA</div>
        <div className="stat-value blue">{eta}</div>
        <div className="status-pill neutral">{selectedRoute ? `ROUTE ${selectedRoute}` : '—'}</div>
      </div>
    </div>
  )
}
