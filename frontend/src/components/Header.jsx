export default function Header({ aiStatus }) {
  const mode = aiStatus?.aiMode || 'DEMO'
  return (
    <header className="header">
      <div className="header-left">
        <div className="header-badge">🚑</div>
        <div>
          <div className="header-title">AMBULANCE AI</div>
          <div className="header-subtitle">EMERGENCY RESPONSE &amp; HOSPITAL COORDINATION</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span className={`ai-mode-chip ${mode === 'LIVE_YOLO' ? 'live' : 'demo'}`}>
          {mode === 'LIVE_YOLO' ? '● LIVE YOLO' : '○ DEMO MODE'}
        </span>
        <div className="system-status">
          <span className="pulse-dot" />
          ALL SYSTEMS OPERATIONAL
        </div>
      </div>
    </header>
  )
}
