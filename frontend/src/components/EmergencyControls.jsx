import { PHASE } from '../state/emergencyState.js'

export default function EmergencyControls({ phase, busy, recommendation, actions }) {
  const canStart = phase === PHASE.IDLE
  const canSelectHospital =
    phase === PHASE.HOSPITAL_SELECTION && !!recommendation && !busy
  const canCompleteArrival = phase === PHASE.EN_ROUTE && !busy
  const isRunning = phase !== PHASE.IDLE && phase !== PHASE.COMPLETED

  return (
    <div className="dash-heading-row">
      <div>
        <div className="dash-heading">Emergency Response Dashboard</div>
        <div className="dash-sub">STATE: {phase}</div>
      </div>
      <div className="controls-row">
        <button
          className="btn btn-primary"
          disabled={!canStart}
          onClick={() => actions.startEmergency()}
        >
          🚨 Start Emergency
        </button>
        <button
          className="btn btn-blue"
          disabled={!canSelectHospital}
          onClick={() => actions.selectBestHospital()}
        >
          🏥 Select Best Hospital
        </button>
        <button
          className="btn btn-accent"
          disabled={!canCompleteArrival}
          onClick={() => actions.completeArrival()}
        >
          ✅ Complete Arrival
        </button>
        {phase === PHASE.COMPLETED && (
          <button className="btn btn-ghost btn-sm" onClick={() => actions.reset()}>
            ↺ Reset Demo
          </button>
        )}
        {isRunning && phase !== PHASE.COMPLETED && (
          <button className="btn btn-ghost btn-sm" onClick={() => actions.reset()}>
            ↺ Reset
          </button>
        )}
      </div>
    </div>
  )
}
