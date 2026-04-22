import React from 'react'

const TIER_STYLE = {
  High:   { background: '#FCEBEB', color: '#A32D2D' },
  Medium: { background: '#FAEEDA', color: '#633806' },
  Low:    { background: '#EAF3DE', color: '#3B6D11' },
}

const TREND_ICON = {
  Increasing: '↑',
  Decreasing: '↓',
  Stable:     '→',
}
const TREND_COLOR = {
  Increasing: '#A32D2D',
  Decreasing: '#3B6D11',
  Stable:     '#6b7280',
}

export default function RegionTable({ regions = [], onRowClick, selectedState }) {
  const sorted = [...regions].sort((a, b) => b.risk_score - a.risk_score).slice(0, 10)

  if (!sorted.length) return <div style={styles.empty}>No data yet — select disaster type and load map.</div>

  return (
    <div style={styles.wrap}>
      <div style={styles.title}>Top regions by risk score</div>
      <table style={styles.table}>
        <thead>
          <tr>
            {['State', 'Tier', 'Risk', 'Exposure', 'Trend'].map(h => (
              <th key={h} style={styles.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(r => (
            <tr
              key={r.state}
              style={{
                ...styles.tr,
                background: r.state === selectedState ? '#f0fdf4' : 'transparent',
                cursor: 'pointer',
              }}
              onClick={() => onRowClick && onRowClick(r.state)}
            >
              <td style={styles.td}><b>{r.state}</b></td>
              <td style={styles.td}>
                <span style={{ ...styles.badge, ...TIER_STYLE[r.risk_tier] }}>
                  {r.risk_tier}
                </span>
              </td>
              <td style={styles.td}>{r.risk_score}%</td>
              <td style={styles.td}>
                ${r.estimated_damage_usd >= 1e9
                  ? `${(r.estimated_damage_usd / 1e9).toFixed(1)}B`
                  : `${(r.estimated_damage_usd / 1e6).toFixed(0)}M`}
              </td>
              <td style={{ ...styles.td, color: TREND_COLOR[r.forecast_next_year ?? 'Stable'] }}>
                {TREND_ICON[r.forecast_next_year ?? 'Stable']} {r.forecast_next_year ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const styles = {
  wrap:  { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '14px 16px', overflowX: 'auto' },
  title: { fontSize: 12, fontWeight: 500, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 10 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th:    { textAlign: 'left', fontSize: 11, color: '#9ca3af', padding: '6px 8px', borderBottom: '1px solid #f3f4f6', fontWeight: 500 },
  tr:    { borderBottom: '1px solid #f3f4f6', transition: 'background .15s' },
  td:    { padding: '9px 8px', verticalAlign: 'middle' },
  badge: { fontSize: 11, fontWeight: 500, padding: '2px 8px', borderRadius: 20 },
  empty: { color: '#9ca3af', fontSize: 13, padding: 16 },
}