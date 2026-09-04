function levelFor(score) {
  if (score <= 30) return { label: 'LOW', color: 'var(--green)', pill: 'green', emoji: '🟢' }
  if (score <= 60) return { label: 'MEDIUM', color: 'var(--yellow)', pill: 'yellow', emoji: '🟡' }
  if (score <= 100) return { label: 'HIGH', color: 'var(--red)', pill: 'red', emoji: '🔴' }
  return { label: 'SEVERE', color: 'var(--critical-red)', pill: 'critical_red', emoji: '🔴' }
}

export default function AIRecommendation({ recommendation }) {
  if (!recommendation) {
    return (
      <div className="card">
        <div className="card-title"><span className="emoji">🤖</span> AI ROUTE RECOMMENDATION</div>
        <div className="empty-hint">Run AI Traffic Analysis to generate a route recommendation.</div>
      </div>
    )
  }

  const maxScore = Math.max(...recommendation.routes.map((r) => r.trafficScore), 1)
  const best = recommendation.routes.find((r) => r.id === recommendation.recommendedRoute)
  const bestLevel = best ? levelFor(best.trafficScore) : null

  return (
    <div className="card">
      <div className="card-title"><span className="emoji">🤖</span> AI ROUTE RECOMMENDATION</div>

      {[...recommendation.routes]
        .sort((a, b) => a.id.localeCompare(b.id))
        .map((route) => {
          const level = levelFor(route.trafficScore)
          const isRecommended = route.id === recommendation.recommendedRoute
          return (
            <div key={route.id} className={`route-compare-row ${isRecommended ? 'recommended' : ''}`}>
              <span style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, width: 60 }}>
                Route {route.id}
              </span>
              <span style={{ width: 26 }}>{level.emoji}</span>
              <div className="route-compare-bar-track">
                <div
                  className="route-compare-bar-fill"
                  style={{
                    width: `${(route.trafficScore / maxScore) * 100}%`,
                    background: level.color,
                  }}
                />
              </div>
              <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 12.5, width: 34, textAlign: 'right' }}>
                {route.trafficScore}
              </span>
              {isRecommended && <span className="recommended-tag">RECOMMENDED</span>}
            </div>
          )
        })}

      {best && (
        <div className="recommendation-banner">
          <div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 10.5, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              RECOMMENDED ROUTE
            </div>
            <div className="route-name">🚑 ROAD {best.id}</div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 11.5, color: 'var(--text-secondary)', marginTop: 4 }}>
              Traffic: {bestLevel.label} &nbsp;·&nbsp; Score: {best.trafficScore} &nbsp;·&nbsp; Est. delay: {best.etaMinutes} min
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, color: 'var(--text-muted)' }}>REASON</div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--text-secondary)', maxWidth: 260 }}>
              {recommendation.reason}
            </div>
            <div style={{ marginTop: 6, color: 'var(--green)', fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, fontSize: 12 }}>
              ROUTE SELECTED ✓
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
