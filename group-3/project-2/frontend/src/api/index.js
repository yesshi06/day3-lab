const BASE = '/api/v1/valuation'

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const json = await res.json()
  if (!res.ok) throw json.error || { code: 'UNKNOWN', message: res.statusText }
  return json.data
}

export const api = {
  // Page 1
  getCompanies: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/companies${qs ? '?' + qs : ''}`)
  },
  getStatistics: () => request('/statistics'),

  // Page 2
  getCompany: (id) => request(`/companies/${encodeURIComponent(id)}`),
  getFinancials: (id) => request(`/companies/${encodeURIComponent(id)}/financials`),

  // Page 3
  recommendComparables: (id) =>
    request(`/companies/${encodeURIComponent(id)}/comparables/recommend`, { method: 'POST' }),
  searchCandidates: (id, params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/companies/${encodeURIComponent(id)}/comparables/candidates${qs ? '?' + qs : ''}`)
  },
  confirmComparables: (id, comparableIds) =>
    request(`/companies/${encodeURIComponent(id)}/comparables`, {
      method: 'PUT',
      body: JSON.stringify({ comparable_ids: comparableIds }),
    }),
  getComparables: (id) => request(`/companies/${encodeURIComponent(id)}/comparables`),

  // Page 4
  runValuation: (id, params = {}) =>
    request(`/companies/${encodeURIComponent(id)}/valuations/run`, {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  getValuationMethods: (id) => request(`/companies/${encodeURIComponent(id)}/valuations/methods`),

  // Page 5
  getValuationSummary: (id) => request(`/companies/${encodeURIComponent(id)}/valuations/summary`),
}
