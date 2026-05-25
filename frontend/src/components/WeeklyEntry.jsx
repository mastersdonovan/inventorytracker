import { useState, useEffect } from 'react'

export default function WeeklyEntry() {
  const [variables, setVariables] = useState([])
  const [weeks, setWeeks] = useState([])
  const [units, setUnits] = useState([])
  const [margin, setMargin] = useState('')
  const [editIndex, setEditIndex] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchVariables()
    fetchWeeks()
  }, [])

  async function fetchVariables() {
    const res = await fetch('/api/variables')
    const vars = await res.json()
    setVariables(vars)
    setUnits(vars.map(() => ''))
  }

  async function fetchWeeks() {
    const res = await fetch('/api/weeks')
    setWeeks(await res.json())
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const parsedUnits = units.map(Number)
    const method = editIndex !== null ? 'PUT' : 'POST'
    const url = editIndex !== null ? `/api/weeks/${editIndex}` : '/api/weeks'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ units: parsedUnits, margin: parseFloat(margin) }),
    })
    if (!res.ok) { setError((await res.json()).error); return }
    setUnits(variables.map(() => ''))
    setMargin('')
    setEditIndex(null)
    fetchWeeks()
  }

  function handleEdit(i) {
    setEditIndex(i)
    setUnits(weeks[i].units.map(String))
    setMargin(String(weeks[i].margin))
    setError('')
  }

  function handleCancel() {
    setEditIndex(null)
    setUnits(variables.map(() => ''))
    setMargin('')
    setError('')
  }

  async function handleRemove(i) {
    await fetch(`/api/weeks/${i}`, { method: 'DELETE' })
    fetchWeeks()
  }

  return (
    <section>
      <h2>Weekly Entry</h2>
      <form onSubmit={handleSubmit}>
        {variables.map((v, i) => (
          <input
            key={i}
            type="number"
            placeholder={`${v.name} (units)`}
            value={units[i] ?? ''}
            onChange={e => {
              const next = [...units]
              next[i] = e.target.value
              setUnits(next)
            }}
            required
          />
        ))}
        <input
          type="number"
          placeholder="Margin ($)"
          value={margin}
          onChange={e => setMargin(e.target.value)}
          step="0.01"
          required
        />
        <button type="submit">{editIndex !== null ? 'Update Week' : 'Add Week'}</button>
        {editIndex !== null && <button type="button" onClick={handleCancel}>Cancel</button>}
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Week</th>
            {variables.map((v, i) => <th key={i}>{v.name}</th>)}
            <th>Margin</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {weeks.map((w, i) => (
            <tr key={i}>
              <td>Wk {i + 1}</td>
              {w.units.map((u, j) => <td key={j}>{u}</td>)}
              <td>${w.margin.toFixed(2)}</td>
              <td>
                <button onClick={() => handleEdit(i)}>Edit</button>
                <button onClick={() => handleRemove(i)}>Remove</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
