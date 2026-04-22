import React, { useState } from 'react'
import { predictRisk } from '../api'
import ShapChart from '../components/ShapChart'
import MetricCard from '../components/MetricCard'

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
]
const CATEGORIES = ['flood', 'wildfire', 'drought', 'hurricane']

function fmt(n) {
  if (!n) return '—'
  return n >= 1e9 ? `$${(n / 1e9).toFixed(1)}B` : `$${(n / 1e6).toFixed(0)}M`
}

function RegionCard({ label, result, loading }) {
  if (loading) return <div style={styles.card}><div style={styles.loading}>Predicting...</div></div>
  if (!result)  return <div style={styles.card}><div style={styles.empty}>Select a region above</div></div>

  const tierColor = result.risk_tier === 'High' ? '#A32D2D' : result.risk_tier === 'Medium' ? '#854D0E' : '#3B6D11'

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.cardState}>{result.state}</span>
        <span style={{ ...styles.cardTier, color: tierColor, background: tierColor + '18' }}>
          {result.risk_tier}
        </span>
      </div>
      <div style={styles.metricsGrid}>
        <MetricCard label="Risk score"  value={`${result.risk_score}%`}      tier={result.risk_tier} />
        <MetricCard label="Exposure"    value={fmt(result.estimated_damage_usd)} />
        <MetricCard label="Trend"       value={result.forecast_next_year} />
        <MetricCard label="Probability" value={`${(result.high_risk_probability * 100).toFixed(1)}%`} />
      </div>
      <div style={styles.range}>
        Damage range: <b>{fmt(result.damage_range_low)}</b> – <b>{fmt(result.damage_range_high)}</b>
      </div>
      <ShapChart data={result.shap_features ?? []} />
    </div>
  )
}

export default function Compare() {
  const [stateA, setStateA] = useState('TX')
  const [stateB, setStateB] = useState('FL')
  const [category, setCategory] = useState('flood')
  const [year, setYear] = useState(2024)
  const [resultA, setResultA] = useState(null)
  const [resultB, setResultB] = useState(null)
  const [loadingA, setLoadingA] = useState(false)
  const [loadingB, setLoadingB] = useState(false)

  const compare = async () => {
    setLoadingA(true); setLoadingB(true)
    setResultA(null); setResultB(null)
    const [a, b] = await Promise.all([
      predictRisk({ state: stateA, disaster_category: category, year }).finally(() => setLoadingA(false)),
      predictRisk({ state: stateB, disaster_category: category, year }).finally(() => setLoadingB(false)),
    ])
    setResultA(a); setResultB(b)
  }

  return (
    <div style={styles.page}>
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>State A</label>
          <select style={styles.select} value={stateA} onChange={e => setStateA(e.target.value)}>
            {US_STATES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <span style={styles.vs}>vs</span>
        <div style={styles.controlGroup}>
          <label style={styles.label}>State B</label>
          <select style={styles.select} value={stateB} onChange={e => setStateB(e.target.value)}>
            {US_STATES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div style={styles.controlGroup}>
          <label style={styles.label}>Disaster type</label>
          <select style={styles.select} value={category} onChange={e => setCategory(e.target.value)}>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={styles.controlGroup}>
          <label style={styles.label}>Year</label>
          <select style={styles.select} value={year} onChange={e => setYear(Number(e.target.value))}>
            {[2021,2022,2023,2024].map(y => <option key={y}>{y}</option>)}
          </select>
        </div>
        <button style={styles.btn} onClick={compare}>Compare</button>
      </div>

      <div style={styles.grid}>
        <RegionCard label="A" result={resultA} loading={loadingA} />
        <RegionCard label="B" result={resultB} loading={loadingB} />
      </div>
    </div>
  )
}

const styles = {
  page:         { padding: 24, display: 'flex', flexDirection: 'column', gap: 20, overflowY: 'auto', flex: 1 },
  controls:     { display: 'flex', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap', background: '#fff', padding: 16, borderRadius: 10, border: '1px solid #e5e7eb' },
  controlGroup: { display: 'flex', flexDirection: 'column', gap: 4 },
  label:        { fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.05em' },
  select:       { fontSize: 13, padding: '7px 10px', borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', cursor: 'pointer' },
  vs:           { fontSize: 15, fontWeight: 500, color: '#9ca3af', alignSelf: 'center', paddingBottom: 4 },
  btn:          { padding: '9px 24px', borderRadius: 8, border: 'none', background: '#1D9E75', color: '#fff', fontSize: 14, fontWeight: 500, cursor: 'pointer', alignSelf: 'flex-end' },
  grid:         { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 },
  card:         { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 14 },
  cardHeader:   { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  cardState:    { fontSize: 20, fontWeight: 600 },
  cardTier:     { fontSize: 12, fontWeight: 500, padding: '3px 10px', borderRadius: 20 },
  metricsGrid:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  range:        { fontSize: 13, color: '#6b7280', background: '#f9fafb', borderRadius: 8, padding: '8px 12px' },
  loading:      { color: '#9ca3af', fontSize: 13, padding: 24, textAlign: 'center' },
  empty:        { color: '#9ca3af', fontSize: 13, padding: 24, textAlign: 'center' },
}