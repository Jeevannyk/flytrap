export default function Controls({
  scenarios, scenario, setScenario, isProtected, setIsProtected, hasRun,
  onRun, onInvestigate, onTamper, onReset, onEvaluate,
}) {
  const current = scenarios.find((s) => s.id === scenario)
  return (
    <section className="panel">
      <label htmlFor="scenario">Scenario</label>
      <select id="scenario" value={scenario} onChange={(e) => setScenario(e.target.value)}>
        {scenarios.map((s) => (
          <option key={s.id} value={s.id}>{s.title}</option>
        ))}
      </select>
      {current && <div className="hint">{current.expectation}</div>}
      <label className="check">
        <input type="checkbox" checked={isProtected} onChange={(e) => setIsProtected(e.target.checked)} />
        FLYTRAP protection on
      </label>
      <button className="primary" onClick={onRun}>Run agent</button>

      <h2>After a run</h2>
      <button onClick={onInvestigate} disabled={!hasRun}>Investigate (replay)</button>
      <button onClick={onTamper} disabled={!hasRun}>Tamper with a record (demo)</button>
      <button onClick={onReset} disabled={!hasRun}>Authorized reset</button>

      <h2>Measured results</h2>
      <button onClick={onEvaluate}>Run evaluation</button>
      <div className="hint">
        Agent is a deterministic simulation of a prompt-injectable agent. Baseline is a keyword filter, not an LLM judge.
      </div>
    </section>
  )
}
