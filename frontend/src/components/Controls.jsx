export default function Controls({
  scenarios, scenario, setScenario, isProtected, setIsProtected, agent, setAgent, busy, hasRun,
  onRun, onInvestigate, onTamper, onReset, onEvaluate,
}) {
  const current = scenarios.find((s) => s.id === scenario)
  const idle = !busy
  return (
    <section className="panel">
      <label htmlFor="scenario">Scenario</label>
      <select id="scenario" value={scenario} onChange={(e) => setScenario(e.target.value)}>
        {scenarios.map((s) => (
          <option key={s.id} value={s.id}>{s.title}</option>
        ))}
      </select>
      {current && <div className="hint">{current.expectation}</div>}
      <label htmlFor="agent">Agent</label>
      <select id="agent" value={agent} onChange={(e) => setAgent(e.target.value)}>
        <option value="sim">Simulated (reproducible)</option>
        <option value="llm">Live LLM (Gemini)</option>
      </select>
      {agent === 'llm' && (
        <div className="hint">Real model calls. Results can vary, and the model may refuse the injection.</div>
      )}
      <label className="check">
        <input type="checkbox" checked={isProtected} onChange={(e) => setIsProtected(e.target.checked)} />
        FLYTRAP protection on
      </label>
      <button className="primary" onClick={onRun} disabled={!idle}>{busy ? 'Working…' : 'Run agent'}</button>

      <h2>After a run</h2>
      <button onClick={onInvestigate} disabled={!hasRun || !idle}>Investigate (replay)</button>
      <button onClick={onTamper} disabled={!hasRun || !idle}>Tamper with a record (demo)</button>
      <button onClick={onReset} disabled={!hasRun || !idle}>Authorized reset</button>

      <h2>Measured results</h2>
      <button onClick={onEvaluate} disabled={!idle}>Run evaluation</button>
      <div className="hint">
        Agent is a deterministic simulation of a prompt-injectable agent. Baseline is a keyword filter, not an LLM judge.
      </div>
    </section>
  )
}
