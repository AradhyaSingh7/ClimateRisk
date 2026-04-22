import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const COLORS = ['#1D9E75', '#27B88A', '#39CC9F', '#52DCB4', '#76E8C8', '#A3F0DB']

export default function ShapChart({ data = [] }) {
  if (!data.length) return <div style={styles.empty}>No SHAP data</div>

  const sorted = [...data].sort((a, b) => b.importance_pct - a.importance_pct)

  return (
    <div style={styles.wrap}>
      <div style={styles.title}>Feature importance (SHAP)</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 4, right: 20, bottom: 4, left: 10 }}
        >
          <XAxis type="number" unit="%" tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fontSize: 12 }}
            width={120}
            tickFormatter={s => s.replace(/_/g, ' ')}
          />
          <Tooltip
            formatter={(v) => [`${v}%`, 'Importance']}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="importance_pct" radius={[0, 4, 4, 0]}>
            {sorted.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={styles.note}>
        SHAP values show which features most influenced the risk prediction for this region.
      </div>
    </div>
  )
}

const styles = {
  wrap:  { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '14px 16px' },
  title: { fontSize: 12, fontWeight: 500, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 12 },
  empty: { color: '#9ca3af', fontSize: 13, padding: 16 },
  note:  { fontSize: 11, color: '#9ca3af', marginTop: 10 },
}