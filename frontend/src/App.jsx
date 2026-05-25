import { useState } from 'react'
import Variables from './components/Variables'
import WeeklyEntry from './components/WeeklyEntry'
import Results from './components/Results'
import './App.css'

const TABS = ['Variables', 'Weekly Entry', 'Results']

export default function App() {
  const [tab, setTab] = useState('Variables')

  return (
    <div className="app">
      <header>
        <h1>Inventory Tracker</h1>
        <nav>
          {TABS.map(t => (
            <button
              key={t}
              className={tab === t ? 'active' : ''}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {tab === 'Variables'    && <Variables />}
        {tab === 'Weekly Entry' && <WeeklyEntry />}
        {tab === 'Results'      && <Results />}
      </main>
    </div>
  )
}
