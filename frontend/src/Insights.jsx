import { useState } from 'react'

// Pearson correlation coefficient between two equal-length numeric arrays.
function correlation(xs, ys) {
  const n = xs.length
  if (n < 2) return null
  const meanX = xs.reduce((a, b) => a + b, 0) / n
  const meanY = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, denX = 0, denY = 0
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - meanX
    const dy = ys[i] - meanY
    num += dx * dy
    denX += dx * dx
    denY += dy * dy
  }
  if (denX === 0 || denY === 0) return null
  return num / Math.sqrt(denX * denY)
}

function trendLabel(r) {
  if (r === null) return { text: 'Not enough variation in the data yet to see a pattern.', tone: 'neutral' }
  if (r >= 0.5) return { text: 'Weeks with higher usage have tended to have higher margins.', tone: 'positive' }
  if (r >= 0.2) return { text: 'Weeks with higher usage have leaned toward higher margins, though the pattern is mild.', tone: 'positive' }
  if (r <= -0.5) return { text: 'Weeks with higher usage have tended to have lower margins.', tone: 'negative' }
  if (r <= -0.2) return { text: 'Weeks with higher usage have leaned toward lower margins, though the pattern is mild.', tone: 'negative' }
  return { text: 'No clear relationship between usage and margin shows up in the data so far.', tone: 'neutral' }
}

export default function Insights() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function fetchInsights() {
    setLoading(true)
    setError('')
    try {
      const [varsRes, weeksRes] = await Promise.all([
        fetch('/api/variables'),
        fetch('/api/weeks'),
      ])
      if (!varsRes.ok || !weeksRes.ok) {
        setError('Could not load data.')
        setLoading(false)
        return
      }
      const variables = await varsRes.json()
      const weeks = await weeksRes.json()

      if (weeks.length < 2) {
        setError('Need at least 2 weeks of data to surface patterns.')
        setLoading(false)
        return
      }

      const margins = weeks.map(w => w.margin)
      const sortedMargins = [...margins].sort((a, b) => a - b)
      const medianMargin = sortedMargins[Math.floor(sortedMargins.length / 2)]
      const hasSplit = weeks.some(w => w.margin > medianMargin) && weeks.some(w => w.margin <= medianMargin)

      const perVariable = variables.map((v, i) => {
        const usage = weeks.map(w => w.units[i])
        const overallMin = Math.min(...usage)
        const overallMax = Math.max(...usage)

        let topRange = null
        if (hasSplit) {
          const topUsage = weeks
            .filter(w => w.margin > medianMargin)
            .map(w => w.units[i])
          if (topUsage.length) {
            topRange = { min: Math.min(...topUsage), max: Math.max(...topUsage) }
          }
        }

        const r = correlation(usage, margins)

        return {
          name: v.name,
          overallMin,
          overallMax,
          topRange,
          trend: trendLabel(r),
        }
      })

      setData({ perVariable, weekCount: weeks.length })
    } catch {
      setError('Something went wrong loading insights.')
    }
    setLoading(false)
  }

  return (
    <section>
      <h2>Insights</h2>
      <p className="insight-intro">
        Historical usage patterns and how they've lined up with margin — for your own read, not a purchase target.
      </p>
      <button onClick={fetchInsights} disabled={loading}>
        {loading ? 'Analyzing…' : 'Generate Insights'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {data && (
        <div className="insight-cards">
          {data.perVariable.map((v, i) => {
            const span = Math.max(v.overallMax - v.overallMin, 1e-9)
            const topLeftPct = v.topRange ? ((v.topRange.min - v.overallMin) / span) * 100 : null
            const topWidthPct = v.topRange ? ((v.topRange.max - v.topRange.min) / span) * 100 : null

            return (
              <div className="insight-card" key={i}>
                <h3>{v.name}</h3>
                <p className={`insight-trend insight-trend-${v.trend.tone}`}>{v.trend.text}</p>

                <div className="insight-bar">
                  <div className="insight-bar-track">
                    {v.topRange && (
                      <div
                        className="insight-bar-highlight"
                        style={{ left: `${topLeftPct}%`, width: `${Math.max(topWidthPct, 2)}%` }}
                      />
                    )}
                  </div>
                  <div className="insight-bar-labels">
                    <span>{v.overallMin}</span>
                    <span>{v.overallMax}</span>
                  </div>
                </div>

                <p className="insight-caption">
                  Full recorded range: {v.overallMin}–{v.overallMax} units/week across {data.weekCount} weeks.
                  {v.topRange && (
                    <> In your higher-margin weeks specifically, usage fell within {v.topRange.min}–{v.topRange.max}.</>
                  )}
                </p>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
