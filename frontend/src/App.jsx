import { useEffect, useState } from 'react'
import { api } from './api'
import Controls from './components/Controls'
import Timeline from './components/Timeline'
import ReplayPanel from './components/ReplayPanel'
import EvalTable from './components/EvalTable'

export default function App() {
  const [scenarios, setScenarios] = useState([])
  const [scenario, setScenario] = useState('clean')
  const [isProtected, setIsProtected] = useState(true)
  const [detail, setDetail] = useState(null)
  const [replay, setReplay] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.scenarios().then(setScenarios).catch((e) => setError(e.message))
  }, [])

  const act = (fn) => async () => {
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e.message)
    }
  }

  const sessionId = detail?.session.id

  const handlers = {
    onRun: act(async () => {
      setReplay(null)
      setDetail(await api.run(scenario, isProtected))
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
    <>
      <header>
        <h1>FLYTRAP</h1>
        <span>Plant the bait. Catch the action. Stop the agent. Find the likely cause. Preserve the evidence.</span>
      </header>
      <main>
        <Controls
          scenarios={scenarios}
          scenario={scenario}
          setScenario={setScenario}
          isProtected={isProtected}
          setIsProtected={setIsProtected}
          hasRun={Boolean(detail)}
          {...handlers}
        />
        <section>
          {error && <div className="panel error">{error}</div>}
          <Timeline detail={detail} scenarios={scenarios} />
          {replay && <ReplayPanel replay={replay} events={detail.events} />}
          {evaluation && <EvalTable evaluation={evaluation} />}
        </section>
      </main>
    </>
  )
}
