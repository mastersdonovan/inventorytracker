import { useState, useEffect } from 'react'

export default function Variables() {
  const [variables, setVariables] = useState([])
  const [name, setName] = useState('')
  const [unitCost, setUnitCost] = useState('')
  const [editIndex, setEditIndex] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { fetchVariables() }, [])

  async function fetchVariables() {
    const res = await fetch('/api/variables')
    setVariables(await res.json())
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const method = editIndex !== null ? 'PUT' : 'POST'
    const url = editIndex !== null ? `/api/variables/${editIndex}` : '/api/variables'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, unit_cost: parseFloat(unitCost) }),
    })
    if (!res.ok) { setError((await res.json()).error); return }
    setName('')
    setUnitCost('')
    setEditIndex(null)
    fetchVariables()
  }

  function handleEdit(i) {
    setEditIndex(i)
    setName(variables[i].name)
    setUnitCost(String(variables[i].unit_cost))
    setError('')
  }

  function handleCancel() {
    setEditIndex(null)
    setName('')
    setUnitCost('')
    setError('')
  }

  async function handleRemove(index) {
    await fetch(`/api/variables/${index}`, { method: 'DELETE' })
    fetchVariables()
  }

  return (
    <section>
      <h2>Variables</h2>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
        <input
          type="number"
          placeholder="Unit cost"
          value={unitCost}
          onChange={e => setUnitCost(e.target.value)}
          step="0.01"
          required
        />
        <button type="submit">{editIndex !== null ? 'Update Variable' : 'Add Variable'}</button>
        {editIndex !== null && <button type="button" onClick={handleCancel}>Cancel</button>}
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table>
        <thead>
          <tr><th>Name</th><th>Unit Cost</th><th></th></tr>
        </thead>
        <tbody>
          {variables.map((v, i) => (
            <tr key={i}>
              <td>{v.name}</td>
              <td>${v.unit_cost.toFixed(2)}</td>
              <td>
                <button onClick={() => handleEdit(i)}>Edit</button>
                <button type="button" onClick={() => handleRemove(i)}>Remove</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
