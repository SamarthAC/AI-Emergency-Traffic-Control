export default function HospitalRecommendation({ hospitals }) {
  return (
    <div className="card">
      <div className="card-title"><span className="emoji">🏥</span> AI HOSPITAL RECOMMENDATION</div>

      {!hospitals && (
        <div className="empty-hint">Hospital recommendations appear after route selection.</div>
      )}

      {hospitals && hospitals.map((h) => (
        <div key={h.id} className={`hospital-card ${h.bestMatch ? 'best' : ''}`}>
          <div className="hospital-card-header">
            <span className="hospital-name">{h.name}</span>
            {h.bestMatch && <span className="best-match-tag">BEST MATCH</span>}
          </div>
          <div className="hospital-metric-row"><span>Distance</span><span>{h.distanceKm} km</span></div>
          <div className="hospital-metric-row"><span>Traffic on route</span><span>{h.trafficPercent}%</span></div>
          <div className="hospital-metric-row"><span>Beds available</span><span>{h.beds}</span></div>
          <div className="hospital-metric-row"><span>ICU capacity</span><span>{h.icu}</span></div>
          <div className="hospital-metric-row"><span>Doctors on duty</span><span>{h.doctors}</span></div>
        </div>
      ))}
    </div>
  )
}
