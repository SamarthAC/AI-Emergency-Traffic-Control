export default function WorkflowSteps({ steps }) {
  return (
    <div className="card">
      <div className="workflow-bar">
        {steps.map((step, idx) => (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: idx === steps.length - 1 ? 'none' : 1 }}>
            <div className={`workflow-step ${step.state}`}>
              <div className="workflow-step-circle">
                {step.state === 'done' ? '✓' : idx + 1}
              </div>
              <span className="workflow-step-label">{step.label}</span>
            </div>
            {idx < steps.length - 1 && <div className="workflow-connector" />}
          </div>
        ))}
      </div>
    </div>
  )
}
