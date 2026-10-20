const yn = (b) => (b ? 'yes' : 'no')

export default function EvalTable({ evaluation }) {
  return (
    <div className="panel">
      <strong>Measured results</strong>
      <table>
        <thead>
          <tr>
            <th>Scenario</th><th>Harm unprotected</th><th>FLYTRAP detected (by)</th>
            <th>Harm with FLYTRAP</th><th>Keyword filter flags page</th>
          </tr>
        </thead>
        <tbody>
          {evaluation.rows.map((r) => (
            <tr key={r.scenario}>
              <td>{r.title}</td>
              <td>{yn(r.harm_unprotected)}</td>
              <td>{yn(r.flytrap_detected)} ({r.detected_by})</td>
              <td>{yn(r.harm_protected)}</td>
              <td>{yn(r.keyword_filter_flags_page)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="hint">False alarms on clean runs: {evaluation.false_alarms} / {evaluation.clean_runs}</div>
    </div>
  )
}
