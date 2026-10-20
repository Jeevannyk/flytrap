const ADMIN_KEY = 'demo-admin'

async function request(path, options = {}) {
  const res = await fetch('/api' + path, options)
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

const post = (path, headers = {}) => request(path, { method: 'POST', headers })

export const api = {
  scenarios: () => request('/scenarios'),
  run: (scenario, isProtected, agent) =>
    request('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, protected: isProtected, agent }),
    }),
  session: (id) => request(`/sessions/${id}`),
  investigate: (id) => post(`/sessions/${id}/investigate`),
  tamper: (id) => post(`/sessions/${id}/tamper`),
  reset: (id) => post(`/sessions/${id}/reset`, { 'X-Admin-Key': ADMIN_KEY }),
  evaluate: () => request('/evaluate'),
}
