import { useEffect, useState } from 'react'
import { api } from './api'
import Controls from './components/Controls'
import Timeline from './components/Timeline'
import ReplayPanel from './components/ReplayPanel'
import EvalTable from './components/EvalTable'

const responseSteps = [
  {
    number: '01',
    title: 'Detect the touch',
    text: 'Session-specific decoys turn an unexpected tool, file, or key access into a high-confidence signal.',
    tone: 'green',
  },
  {
    number: '02',
    title: 'Contain the agent',
    text: 'The gateway freezes the session, revokes its capability token, and blocks subsequent tool calls.',
    tone: 'red',
  },
  {
    number: '03',
    title: 'Trace the trigger',
    text: 'Replay tests untrusted input one sentence at a time and highlights likely triggering text.',
    tone: 'blue',
  },
]

const systemBoundary = [
  'Session-scoped decoy generation',
  'Gateway enforcement and tool-call blocking',
  'Egress allowlist for external recipients',
  'Tamper-evident, hash-chained event log',
]

const simulatedBoundary = [
  'The demo agent and company data',
  'Credential revocation (gateway token)',
  'Evaluation baseline (keyword filter)',
  'Replay runs against the simulated agent',
]

export default function App() {
  const [scenarios, setScenarios] = useState([])
  const [scenario, setScenario] = useState('clean')
  const [isProtected, setIsProtected] = useState(true)
  const [agent, setAgent] = useState('sim')
  const [busy, setBusy] = useState(false)
  const [detail, setDetail] = useState(null)
  const [replay, setReplay] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.scenarios().then(setScenarios).catch((e) => setError(e.message))
  }, [])

  const act = (fn) => async () => {
    setError(null)
    setBusy(true)
    try {
      await fn()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const sessionId = detail?.session.id
  const handlers = {
    onRun: act(async () => {
      setReplay(null)
      setDetail(await api.run(scenario, isProtected, agent))
    }),
    onInvestigate: act(async () => {
      const result = await api.investigate(sessionId)
      setDetail(await api.session(sessionId))
      setReplay(result)
    }),
    onTamper: act(async () => setDetail(await api.tamper(sessionId))),
    onReset: act(async () => setDetail(await api.reset(sessionId))),
    onEvaluate: act(async () => setEvaluation(await api.evaluate())),
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Flytrap home">
          <span className="brand-mark">F</span>
          <span>FLYTRAP</span>
        </a>
        <span className="topbar-caption">AI AGENT SECURITY</span>
        <div className="system-status"><span className="status-dot" /> DEMO ENVIRONMENT</div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="eyebrow"><span className="eyebrow-line" /> BEHAVIORAL DEFENSE FOR AI AGENTS</div>
          <h1>Decoy tripwires that catch <span>hijacked AI</span></h1>
          <p className="hero-copy">
            Catch suspicious actions at the tool boundary. Contain the agent, investigate the trigger,
            and keep a verifiable record of what happened.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#demo">Launch live demo <span aria-hidden="true">↘</span></a>
            <a className="button button-quiet" href="#how-it-works">See how it works <span aria-hidden="true">↓</span></a>
          </div>
          <div className="hero-footnote"><span className="status-dot" /> SIMULATED ENVIRONMENT <span className="footnote-divider">/</span> NO REAL DATA OR TOOLS
          </div>
        </section>

        <section className="content-section demo-section" id="demo">
          <div className="section-heading">
            <div>
              <div className="eyebrow">01 / HANDS-ON DEMO</div>
              <h2>Run the agent. Watch the boundary.</h2>
              <p>Choose a scenario, run it with or without protection, then inspect the evidence.</p>
            </div>
            <span className="section-chip"><span className="status-dot" /> LIVE CONTROLS</span>
          </div>
          {error && <div className="panel error" role="alert"><strong>Request failed</strong><span>{error}</span></div>}
          <Controls
            scenarios={scenarios}
            scenario={scenario}
            setScenario={setScenario}
            isProtected={isProtected}
            setIsProtected={setIsProtected}
            agent={agent}
            setAgent={setAgent}
            busy={busy}
            hasRun={Boolean(detail)}
            {...handlers}
          />
          <div className="demo-output">
            <div className="output-heading">
              <div>
                <div className="eyebrow">SESSION OBSERVABILITY</div>
                <h3>Event timeline</h3>
              </div>
              {detail && <span className="section-chip">{detail.events.length} EVENTS</span>}
            </div>
            <Timeline detail={detail} scenarios={scenarios} />
            {replay && <ReplayPanel replay={replay} events={detail.events} />}
          </div>
        </section>

        <section className="content-section" id="how-it-works">
          <div className="section-heading">
            <div>
              <div className="eyebrow">02 / RESPONSE PIPELINE</div>
              <h2>From suspicious action to useful evidence.</h2>
              <p>Flytrap responds to what an agent does, rather than trying to classify every piece of text it reads.</p>
            </div>
          </div>
          <div className="response-grid">
            {responseSteps.map((step) => (
              <article className={`info-card tone-${step.tone}`} key={step.number}>
                <span className="step-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="content-section metrics-section" id="results">
          <div className="section-heading">
            <div>
              <div className="eyebrow">03 / MEASURED RESULTS</div>
              <h2>Signals, not promises.</h2>
              <p>Reproducible results from the included scenarios. One known miss is shown explicitly.</p>
            </div>
            <a className="text-link" href="#demo">Run the evaluation ↑</a>
          </div>
          <div className="metric-grid">
            <article className="metric-card"><span className="metric-value">3<span>/4</span></span><span className="metric-label">attack patterns detected</span><small>Decoy tripwire or egress allowlist</small></article>
            <article className="metric-card"><span className="metric-value">0<span>/20</span></span><span className="metric-label">false alarms on clean runs</span><small>Measured with the deterministic demo agent</small></article>
            <article className="metric-card"><span className="metric-value metric-text">SHA-256</span><span className="metric-label">tamper-evident event chain</span><small>Detects edits to logged events</small></article>
            <article className="metric-card metric-miss"><span className="metric-value">01</span><span className="metric-label">known miss</span><small>Internal email swap uses only legitimate tools</small></article>
          </div>
          <div className="evaluation-wrap">
            {evaluation
              ? <EvalTable evaluation={evaluation} />
              : <div className="evaluation-placeholder"><span className="status-dot" /> Run evaluation from the demo controls to load the full scenario-by-scenario comparison.</div>}
          </div>
        </section>

        <section className="content-section" id="boundary">
          <div className="section-heading">
            <div>
              <div className="eyebrow">04 / SYSTEM BOUNDARY</div>
              <h2>What is enforced—and what is simulated.</h2>
              <p>The demo is transparent about the boundary between working security logic and simulated infrastructure.</p>
            </div>
          </div>
          <div className="boundary-grid">
            <article className="boundary-card">
              <div className="card-kicker"><span className="status-dot" /> ENFORCED IN THE DEMO</div>
              <ul>{systemBoundary.map((item) => <li key={item}>{item}</li>)}</ul>
            </article>
            <article className="boundary-card muted-card">
              <div className="card-kicker"><span className="status-dot muted-dot" /> SIMULATED COMPONENTS</div>
              <ul>{simulatedBoundary.map((item) => <li key={item}>{item}</li>)}</ul>
            </article>
          </div>
        </section>

        <section className="content-section architecture-section" id="architecture">
          <div className="section-heading">
            <div>
              <div className="eyebrow">05 / ARCHITECTURE</div>
              <h2>A narrow boundary. A complete trail.</h2>
            </div>
            <span className="architecture-note">Every tool call passes through the gateway.</span>
          </div>
          <div className="architecture-flow" aria-label="Agent to gateway to tools, with the gateway writing to the audit log">
            <div className="flow-node"><span className="flow-index">01</span><strong>Agent</strong><small>Plans and requests actions</small></div>
            <span className="flow-arrow" aria-hidden="true">→</span>
            <div className="flow-node flow-gateway"><span className="flow-index">02</span><strong>Flytrap gateway</strong><small>Token check · tripwire · egress policy</small></div>
            <span className="flow-arrow" aria-hidden="true">→</span>
            <div className="flow-node"><span className="flow-index">03</span><strong>Tools</strong><small>Simulated company environment</small></div>
          </div>
          <div className="audit-branch"><span className="branch-line" /><span className="audit-node"><span className="status-dot" /> SHA-256 HASH-CHAINED AUDIT LOG</span></div>
          <div className="closing-note"><span className="closing-mark">✳</span><p>A decoy touch is a high-confidence warning signal—not proof of intent. Replay provides candidate inputs, not certainty.</p></div>
        </section>
      </main>

      <nav className="bottom-nav" aria-label="Page sections">
        <a href="#demo"><span>01</span>Demo</a>
        <a href="#how-it-works"><span>02</span>Response</a>
        <a href="#results"><span>03</span>Results</a>
        <a href="#architecture"><span>04</span>Architecture</a>
      </nav>
    </div>
  )
}
