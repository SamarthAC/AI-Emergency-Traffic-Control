import { Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage.jsx'
import SumoSimulationPage from './pages/SumoSimulationPage.jsx'
import RoutingPage from './pages/RoutingPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/sumo-simulation" element={<SumoSimulationPage />} />
      <Route path="/routing" element={<RoutingPage />} />
    </Routes>
  )
}
