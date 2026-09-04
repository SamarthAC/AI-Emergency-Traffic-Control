export default function ToolNav({ contextParams }) {
  const suffix = contextParams ? `?${contextParams}` : ''

  return (
    <div className="tool-nav">
      <a
        className="tool-nav-card"
        href={`/sumo-simulation${suffix}`}
        target="_blank"
        rel="noreferrer"
      >
        <span className="tool-nav-icon">🚦</span>
        <div>
          <div className="tool-nav-title">SUMO SIMULATION</div>
          <div className="tool-nav-subtitle">Live microscopic traffic sim — opens in a new tab</div>
        </div>
        <span className="tool-nav-arrow">↗</span>
      </a>

      <a
        className="tool-nav-card"
        href={`/routing${suffix}`}
        target="_blank"
        rel="noreferrer"
      >
        <span className="tool-nav-icon">🧭</span>
        <div>
          <div className="tool-nav-title">ROUTING VIEW</div>
          <div className="tool-nav-subtitle">Weighted Dijkstra graph — opens in a new tab</div>
        </div>
        <span className="tool-nav-arrow">↗</span>
      </a>
    </div>
  )
}
