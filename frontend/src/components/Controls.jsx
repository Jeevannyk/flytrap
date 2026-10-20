export default function Controls({
  scenarios, scenario, setScenario, isProtected, setIsProtected, agent, setAgent, busy, hasRun,
  onRun, onInvestigate, onTamper, onReset, onEvaluate,
}) {
  const current = scenarios.find((s) => s.id === scenario)
  const idle = !busy
  return (
    <section className="panel controls-panel" aria-label="Demo controls">
      <div className="controls-topline">
        <div>
          <div className="eyebrow">CONFIGURE A SESSION</div>
          <h3>Choose your test conditions</h3>
        </div>
        <span className="control-state"><span className="status-dot" /> {isProtected ? 'PROTECTION ENABLED' : 'UNPROTECTED RUN'}</span>
      </div>
      <div className="controls-grid">
        <div className="control-field">
          <label htmlFor="scenario">Scenario</label>
          <select id="scenario" value={scenario} onChange={(e) => setScenario(e.target.value)}>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>{s.title}</option>
            ))}
          </select>
          {current && <div className="hint">{current.expectation}</div>}
        </div>
        <div className="control-field">
          <label htmlFor="agent">Agent runtime</label>
          <select id="agent" value={agent} onChange={(e) => setAgent(e.target.value)}>
            <option value="sim">Simulated · reproducible</option>
            <option value="llm">Live LLM · Gemini</option>
          </select>
          {agent === 'llm' && (
            <div className="hint">Live model calls can vary, and the model may refuse the injection.</div>
          )}
        </div>
        <label className="check protection-toggle">
          <input type="checkbox" checked={isProtected} onChange={(e) => setIsProtected(e.target.checked)} />
          <span className="toggle-copy"><strong>Flytrap protection</strong><small>Gateway tripwires and containment</small></span>
        </label>
        <div className="run-action">
          <button className="primary" onClick={onRun} disabled={!idle}>{busy ? 'Running session…' : 'Run agent'} <span aria-hidden="true">↗</span></button>
          <span className="hint">Uses fake company data and simulated tools.</span>
        </div>
      </div>
      <div className="control-divider" />
      <div className="control-footer">
        <div className="secondary-actions">
          <span className="control-caption">SESSION ACTIONS</span>
          <button className="button button-small" onClick={onInvestigate} disabled={!hasRun || !idle}>Investigate replay</button>
          <button className="button button-small" onClick={onTamper} disabled={!hasRun || !idle}>Demo tamper detection</button>
          <button className="button button-small" onClick={onReset} disabled={!hasRun || !idle}>Authorized reset</button>
        </div>
        <div className="evaluation-action">
          <span className="control-caption">BENCHMARK</span>
          <button className="button button-small button-outline" onClick={onEvaluate} disabled={!idle}>Run evaluation <span aria-hidden="true">↗</span></button>
        </div>
      </div>
      <p className="control-disclaimer">The agent is a deterministic simulation by default. The baseline is a keyword filter, not an LLM judge.</p>
    </section>
  )
}
