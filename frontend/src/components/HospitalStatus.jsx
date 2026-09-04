export default function HospitalStatus({ hospitals }) {
  const best = hospitals?.find((h) => h.bestMatch)

  return (
    <div className="card">
      <div className="card-title"><span className="emoji">📋</span> HOSPITAL STATUS</div>
      {!best && <div className="empty-hint">No hospital selected yet.</div>}
      {best && (
        <>
          <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, fontSize: 14, marginBottom: 10 }}>
            {best.name}
          </div>
          <div className="hospital-metric-row"><span>Beds</span><span>{best.beds}</span></div>
          <div className="hospital-metric-row"><span>ICU</span><span>{best.icu}</span></div>
          <div className="hospital-metric-row"><span>Doctors</span><span>{best.doctors}</span></div>
          <div className="hospital-metric-row"><span>Distance</span><span>{best.distanceKm} km</span></div>
        </>
      )}
    </div>
  )
}
