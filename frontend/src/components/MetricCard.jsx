import React from 'react'

const TIER_COLORS = {
  High:   '#A32D2D',
  Medium: '#854D0E',
  Low:    '#3B6D11',
}

export default function MetricCard({ label, value, unit = '', tier }) {
  const color = tier ? TIER_COLORS[tier] ?? '#1a1a1a' : '#1a1a1a'
  return (
    <div style={styles.card}>
      <div style={styles.label}>{label}</div>
      <div style={{ ...styles.value, color }}>
        {value !== undefined && value !== null ? `${value}${unit}` : '—'}
      </div>
    </div>
  )
}

const styles = {
  card: {
    background: '#fff', border: '1px solid #e5e7eb',
    borderRadius: 10, padding: '14px 16px',
  },
  label: { fontSize: 11, color: '#6b7280', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' },
  value: { fontSize: 22, fontWeight: 500 },
}