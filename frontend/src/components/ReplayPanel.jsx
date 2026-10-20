// Split text into plain and highlighted parts for each candidate sentence.
function highlight(text, sentences) {
  const parts = []
  let rest = text
  for (const s of sentences) {
    const i = rest.indexOf(s)
    if (i === -1) continue
    parts.push(rest.slice(0, i), <mark key={parts.length}>{s}</mark>)
    rest = rest.slice(i + s.length)
  }
  parts.push(rest)
  return parts
}

export default function ReplayPanel({ replay, events }) {
  if (replay.status !== 'ok') {
    return <div className="panel"><strong>Investigation:</strong> {replay.status}</div>
  }
  const sources = {}
  for (const e of events) {
    if (e.payload.untrusted) sources[e.payload.args.url] = e.payload.text
  }
  return (
    <div className="panel">
      <strong>Likely triggering input</strong> <span className="badge warn">{replay.method}</span>
      {Object.entries(sources).map(([url, text]) => (
        <div key={url}>
          <div className="hint">{url}</div>
          <div className="evidence">
            {highlight(text, replay.candidates.filter((c) => c.source === url).map((c) => c.sentence))}
          </div>
        </div>
      ))}
      <div className="hint">{replay.note}</div>
    </div>
  )
}
