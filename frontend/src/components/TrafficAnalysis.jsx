import TrafficRoadCard from './TrafficRoadCard.jsx'
import { PHASE } from '../state/emergencyState.js'

export default function TrafficAnalysis({ phase, roads, recommendation, busy, actions, aiStatus }) {
  const canRun = phase === PHASE.TRAFFIC_ANALYSIS && !busy
  const notReady = phase === PHASE.IDLE || phase === PHASE.EMERGENCY || phase === PHASE.DISPATCHED

  return (
    <div className="card">
      <div className="card-title">
        <span className="emoji">🧠</span> AI TRAFFIC ANALYSIS
        <span className="input-source-tag" style={{ marginLeft: 'auto' }}>
          INPUT SOURCE: BMD-45 / SIMULATED CCTV
          {aiStatus && (
            <span className={`ai-mode-chip ${aiStatus.aiMode === 'LIVE_YOLO' ? 'live' : 'demo'}`}>
              {aiStatus.aiMode === 'LIVE_YOLO' ? 'LIVE YOLO' : 'DEMO'}
            </span>
          )}
        </span>
      </div>

      {notReady && (
        <div className="empty-hint">
          Complete Dispatch → Patient Pickup to unlock AI Traffic Analysis.
        </div>
      )}

      {!notReady && (
        <>
          <div className="grid-3" style={{ marginBottom: 14 }}>
            {['A', 'B', 'C'].map((roadId) => (
              <TrafficRoadCard
                key={roadId}
                roadId={roadId}
                entry={roads[roadId]}
                isRecommended={recommendation?.recommendedRoute === roadId}
              />
            ))}
          </div>

          {phase === PHASE.TRAFFIC_ANALYSIS && (
            <button className="btn btn-blue" disabled={!canRun} onClick={() => actions.runTrafficAnalysis()}>
              {busy ? 'ANALYZING...' : '▶ RUN AI TRAFFIC ANALYSIS'}
            </button>
          )}
        </>
      )}
    </div>
  )
}
