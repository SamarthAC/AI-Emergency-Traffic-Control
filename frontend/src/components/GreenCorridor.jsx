export default function GreenCorridor({ corridor, selectedRoute }) {
  return (
    <div className="card">
      <div className="card-title"><span className="emoji">🟢</span> GREEN CORRIDOR</div>

      <div className={`corridor-active-banner ${corridor.active ? 'active' : 'standby'}`}>
        {corridor.active ? `ACTIVE — ROUTE ${selectedRoute}` : 'STANDBY'}
      </div>

      {corridor.junctions.length === 0 && (
        <div className="empty-hint">Junctions will appear once a route is selected.</div>
      )}

      {corridor.junctions.map((j) => (
        <div className="junction-row" key={j}>
          <span>{j}</span>
          <span style={{ color: corridor.active ? 'var(--green)' : 'var(--text-muted)' }}>
            {corridor.active ? '🟢 GREEN' : '🔴 RED'}
          </span>
        </div>
      ))}
    </div>
  )
}
