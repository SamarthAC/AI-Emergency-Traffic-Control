import { useEffect, useMemo, useState } from 'react'
import Header from '../components/Header.jsx'
import EmergencyControls from '../components/EmergencyControls.jsx'
import StatusCards from '../components/StatusCards.jsx'
import AmbulanceRoute from '../components/AmbulanceRoute.jsx'
import TrafficAnalysis from '../components/TrafficAnalysis.jsx'
import AIRecommendation from '../components/AIRecommendation.jsx'
import HospitalRecommendation from '../components/HospitalRecommendation.jsx'
import GreenCorridor from '../components/GreenCorridor.jsx'
import HospitalStatus from '../components/HospitalStatus.jsx'
import LiveSystemFeed from '../components/LiveSystemFeed.jsx'
import WorkflowSteps from '../components/WorkflowSteps.jsx'
import ToolNav from '../components/ToolNav.jsx'
import { useEmergencyState } from '../state/emergencyState.js'
import * as api from '../services/api.js'

export default function DashboardPage() {
  const state = useEmergencyState()
  const [aiStatus, setAiStatus] = useState(null)

  useEffect(() => {
    api.getSystemStatus().then(setAiStatus).catch(() => setAiStatus(null))
  }, [])

  // Carries the current road/traffic-score context into the SUMO
  // Simulation and Routing pages via URL params, so opening them in a new
  // tab still reflects whatever the dashboard has already analyzed.
  const toolContextParams = useMemo(() => {
    const params = new URLSearchParams()
    if (state.selectedRoute) params.set('road', state.selectedRoute)
    for (const roadId of ['A', 'B', 'C']) {
      const score = state.roads[roadId]?.data?.trafficScore
      if (score != null) params.set(`score${roadId}`, score)
    }
    return params.toString()
  }, [state.selectedRoute, state.roads])

  return (
    <div className="app-shell">
      <Header aiStatus={aiStatus} />

      <ToolNav contextParams={toolContextParams} />

      <div className="card">
        <EmergencyControls
          phase={state.phase}
          busy={state.busy}
          recommendation={state.recommendation}
          actions={state.actions}
        />
      </div>

      {state.error && <div className="error-banner">⚠ {state.error}</div>}

      <StatusCards
        ambulanceId={state.ambulanceId}
        ambulanceStatus={state.ambulanceStatus}
        priority={state.priority}
        recommendation={state.recommendation}
        selectedRoute={state.selectedRoute}
        corridor={state.corridor}
        eta={state.eta}
      />

      <div className="grid-2">
        <div className="card">
          <div className="card-title"><span className="emoji">🚑</span> AMBULANCE ROUTE</div>
          <AmbulanceRoute
            roads={state.roads}
            recommendation={state.recommendation}
            selectedRoute={state.selectedRoute}
            corridor={state.corridor}
            ambulanceProgress={state.ambulanceProgress}
            phase={state.phase}
          />
        </div>
        <HospitalRecommendation hospitals={state.hospitals} />
      </div>

      <TrafficAnalysis
        phase={state.phase}
        roads={state.roads}
        recommendation={state.recommendation}
        busy={state.busy}
        actions={state.actions}
        aiStatus={aiStatus}
      />

      <AIRecommendation recommendation={state.recommendation} />

      <div className="grid-bottom">
        <GreenCorridor corridor={state.corridor} selectedRoute={state.selectedRoute} />
        <HospitalStatus hospitals={state.hospitals} />
        <LiveSystemFeed feed={state.feed} />
      </div>

      <WorkflowSteps steps={state.workflowStatus} />

      <div className="prototype-footer">
        <span><b>Traffic perception:</b> BMD-45 Bengaluru CCTV imagery (simulated / prerecorded)</span>
        <span><b>AI:</b> YOLO vehicle detection</span>
        <span><b>Routing:</b> Traffic-weighted Dijkstra</span>
        <span><b>CCTV:</b> Simulated input — not a live city feed</span>
      </div>
    </div>
  )
}
