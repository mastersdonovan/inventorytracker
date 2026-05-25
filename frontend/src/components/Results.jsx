import { useState } from 'react'

export default function Results() {
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function fetchResults() {
    setLoading(true)
    setError('')
    const res = await fetch('/api/results')
    if (!res.ok) {
      setError((await res.json()).error)
      setLoading(false)
      return
    }
    setResults(await res.json())
    setLoading(false)
  }

  const totalWeeklyCost = results
    ? results.variables.reduce((sum, v) => sum + v.weekly * v.unit_cost, 0)
    : 0

  return (
    <section>
      <h2>Results</h2>
      <button onClick={fetchResults} disabled={loading}>
        {loading ? 'Calculating…' : 'Calculate Optimal Purchase'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {results && (
        <table>
          <thead>
            <tr>
              <th>Variable</th>
              <th>Daily (units)</th>
              <th>Weekly (units)</th>
              <th>Monthly (units)</th>
              <th>Unit Cost</th>
              <th>Est. Weekly Cost</th>
            </tr>
          </thead>
          <tbody>
            {results.variables.map((v, i) => (
              <tr key={i}>
                <td>{v.name}</td>
                <td>{v.daily}</td>
                <td>{v.weekly}</td>
                <td>{v.monthly}</td>
                <td>${v.unit_cost.toFixed(2)}</td>
                <td>${(v.weekly * v.unit_cost).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={5}><strong>Total Est. Weekly Cost</strong></td>
              <td><strong>${totalWeeklyCost.toFixed(2)}</strong></td>
            </tr>
          </tfoot>
        </table>
      )}
    </section>
  )
}
