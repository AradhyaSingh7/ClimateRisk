import React from 'react'

const CATEGORIES = ['flood', 'wildfire', 'drought', 'hurricane']
const YEARS = [2020, 2021, 2022, 2023, 2024]

export default function Sidebar({ filters, onChange, onLoad, loading }) {
  const set = (key, val) => onChange({ ...filters, [key]: val })

  return (
    <aside style={styles.aside}>
      <div style={styles.section}>
        <div style={styles.label}>Disaster type</div>
        <div style={styles.pills}>
          {CATEGORIES.map(c => (
            <button
              key={c}
              style={{
                ...styles.pill,
                ...(filters.category === c ? styles.pillActive : {}),
              }}
              onClick={() => set('category', c)}
            >
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div style={styles.section}>
        <div style={styles.label}>Year</div>
        <select
          style={styles.select}
          value={filters.year}
          onChange={e => set('year', Number(e.target.value))}
        >
          {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      <div style={styles.section}>
        <div style={styles.label}>Min risk score</div>
        <input
          type="range" min={0} max={80} step={5}
          value={filters.minRisk}
          onChange={e => set('minRisk', Number(e.target.value))}
          style={{ width: '100%' }}
        />
        <div style={styles.rangeLabels}>
          <span>0%</span><span style={{ color: '#1a1a1a', fontWeight: 500 }}>{filters.minRisk}%+</span>
        </div>
      </div>

      <button
        style={{ ...styles.loadBtn, opacity: loading ? 0.6 : 1 }}
        onClick={onLoad}
        disabled={loading}
      >
        {loading ? 'Loading...' : 'Load map'}
      </button>

      <div style={styles.section}>
        <div style={styles.label}>Legend</div>
        <div style={styles.legendItem}><span style={{ ...styles.dot, background: '#E24B4A' }} />High risk ≥ 65%</div>
        <div style={styles.legendItem}><span style={{ ...styles.dot, background: '#EF9F27' }} />Medium 35–64%</div>
        <div style={styles.legendItem}><span style={{ ...styles.dot, background: '#639922' }} />Low &lt; 35%</div>
      </div>
    </aside>
  )
}

const styles = {
  aside:      { width: 220, background: '#fff', borderRight: '1px solid #e5e7eb', padding: 16, display: 'flex', flexDirection: 'column', gap: 20, flexShrink: 0, overflowY: 'auto' },
  section:    { display: 'flex', flexDirection: 'column', gap: 8 },
  label:      { fontSize: 11, fontWeight: 500, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' },
  pills:      { display: 'flex', flexWrap: 'wrap', gap: 6 },
  pill:       { fontSize: 12, padding: '4px 10px', borderRadius: 20, border: '1px solid #e5e7eb', background: 'transparent', cursor: 'pointer', color: '#6b7280' },
  pillActive: { background: '#E1F5EE', borderColor: '#1D9E75', color: '#0F6E56', fontWeight: 500 },
  select:     { fontSize: 13, padding: '6px 8px', borderRadius: 8, border: '1px solid #e5e7eb', color: '#1a1a1a', background: '#fff', cursor: 'pointer' },
  rangeLabels:{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#6b7280', marginTop: 4 },
  loadBtn:    { padding: '10px 0', borderRadius: 8, border: 'none', background: '#1D9E75', color: '#fff', fontSize: 13, fontWeight: 500, cursor: 'pointer' },
  legendItem: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#6b7280' },
  dot:        { width: 10, height: 10, borderRadius: '50%', display: 'inline-block', flexShrink: 0 },
}