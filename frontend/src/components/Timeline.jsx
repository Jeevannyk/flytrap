function summarize(e) {
  const p = e.payload
  const args = (a) => JSON.stringify(a)
  switch (e.type) {
    case 'tool_call': return `${p.tool}(${args(p.args)})` + (p.untrusted ? '  [untrusted input]' : '')
    case 'decoy_touch': return `touched ${p.decoy} via ${p.tool}(${args(p.args)})`
    case 'containment': return p.actions.join(', ')
    case 'blocked': return `${p.tool} blocked: ${p.reason}`
    case 'policy_block': return `${p.rule}: ${p.args.to}`
    case 'replay_result': return p.candidates.map((c) => c.sentence).join(' | ')
    case 'session_end': return `harm completed: ${p.harm_completed}`
    case 'session_start': return `${p.scenario} (protected: ${p.protected})`
    default: return JSON.stringify(p)
  }
}

export default function Timeline({ detail, scenarios }) {
  if (!detail) {
    return <div className="panel"><strong>No run yet</strong></div>
  }
  const { session, events, chain } = detail
  const title = scenarios.find((s) => s.id === session.scenario)?.title ?? session.scenario
  return (
    <div className="panel">
      <div className="row">
        <strong>{title}</strong>
        <span className={'badge ' + (session.status === 'frozen' ? 'bad' : 'ok')}>{session.status}</span>
        <span className={'badge ' + (chain.ok ? 'ok' : 'bad')}>
          {chain.ok ? `chain verified (${chain.length} events)` : `CHAIN BROKEN at event ${chain.bad_index}`}
        </span>
      </div>
      {events.map((e) => (
        <div key={e.idx} className={'ev ' + e.type}>
          <span>{e.idx}</span>
          <span className="t">{e.type}</span>
          <span className="p">{summarize(e)}</span>
        </div>
      ))}
    </div>
  )
}
