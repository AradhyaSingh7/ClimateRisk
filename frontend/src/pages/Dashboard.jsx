import React, { useState, useCallback } from 'react'
import RiskMap from '../components/RiskMap'
import MetricCard from '../components/MetricCard'
import ShapChart from '../components/ShapChart'
import RegionTable from '../components/RegionTable'
import Sidebar from '../components/Sidebar'
import { predictBulk, predictRisk, ALL_STATES } from '../api'

const DEFAULT_FILTERS = { category: 'flood', year: 2024, minRisk: 0 }

export default function Dashboard() {
  const [filters, setFilters]           = useState(DEFAULT_FILTERS)
  const [regions, setRegions]           = useState([])
  const [selectedState, setSelected]    = useState(null)
  const [detail, setDetail]             = useState(null)
  const [loading, setLoading]           = useState(false)
  const [detailLoading, setDetailLoad]  = useState(false)
  const [error, setError]               = useState(null)

  // Load all states onto map
  const handleLoad = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await predictBulk(ALL_STATES, filters.category, filters.year)
      const filtered = data.filter(r => r.risk_score >= filters.minRisk)
      setRegions(filtered)
    } catch (e) {
      setError('API unreachable — is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }, [filters])

  // Drill into a single state
  const handleStateClick = useCallback(async (state) => {
    setSelected(state)
    setDetailLoad(true)
    try {
      const coords = regions.find(r => r.state === state)
      const data = await predictRisk({
        state,
        disaster_category: filters.category,
        year: filters.year,
        mean_lat: coords?.lat ?? 39,
        mean_lon: coords?.lon ?? -98,
      })
      setDetail(data)
    } catch {
      setDetail(null)
    } finally {
      setDetailLoad(false)
    }
  }, [regions, filters])

  const fmt = (n) => {
    if (!n) return '—'
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    return `$${(n / 1e6).toFixed(0)}M`
  }

  return (
    <div style={styles.page}>
      <Sidebar filters={filters} onChange={setFilters} onLoad={handleLoad} loading={loading} />

      <div style={styles.main}>
        {error && <div style={styles.error}>{error}</div>}

        {/* Top metric bar */}
        <div style={styles.metrics}>
          <MetricCard
            label="Selected state"
            value={selectedState ?? 'None'}
          />
          <MetricCard
            label="Risk score"
            value={detail ? `${detail.risk_score}%` : '—'}
            tier={detail?.risk_tier}
          />
          <MetricCard
            label="Est. exposure"
            value={detail ? fmt(detail.estimated_damage_usd) : '—'}
          />
          <MetricCard
            label="Trend (next yr)"
            value={detail?.forecast_next_year ?? '—'}
            tier={
              detail?.forecast_next_year === 'Increasing' ? 'High'
              : detail?.forecast_next_year === 'Decreasing' ? 'Low'
              : undefined
            }
          />
        </div>

        {/* Map */}
        <div style={styles.mapWrap}>
          {!regions.length && !loading && (
            <div style={styles.mapHint}>
              Select a disaster type and click <b>Load map</b> to populate the risk heatmap
            </div>
          )}
          {(regions.length > 0 || loading) && (
            <RiskMap
              regions={regions}
              onStateClick={handleStateClick}
              selectedState={selectedState}
            />
          )}
        </div>

        {/* Bottom panels */}
        <div style={styles.bottom}>
          <div style={styles.tableWrap}>
            <RegionTable
              regions={regions}
              onRowClick={handleStateClick}
              selectedState={selectedState}
            />
          </div>
          <div style={styles.shapWrap}>
            {detailLoading
              ? <div style={styles.loading}>Loading SHAP data...</div>
              : <ShapChart data={detail?.shap_features ?? []} />
            }
          </div>
        </div>

        {/* Damage range detail */}
        {detail && (
          <div style={styles.detailBar}>
            <span style={styles.detailLabel}>Damage range for <b>{detail.state}</b>:</span>
            <span style={styles.detailRange}>
              {fmt(detail.damage_range_low)} – {fmt(detail.damage_range_high)}
            </span>
            <span style={styles.detailProb}>
              High-risk probability: <b>{(detail.high_risk_probability * 100).toFixed(1)}%</b>
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  page:        { display: 'flex', flex: 1, overflow: 'hidden' },
  main:        { flex: 1, padding: 20, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto' },
  metrics:     { display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 12 },
  mapWrap:     { position: 'relative' },
  mapHint:     {
    background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
    height: 380, display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#9ca3af', fontSize: 14, textAlign: 'center', padding: 24,
  },
  bottom:      { display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 16 },
  tableWrap:   {},
  shapWrap:    {},
  loading:     { color: '#9ca3af', fontSize: 13, padding: 16, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10 },
  error:       { background: '#FCEBEB', color: '#A32D2D', borderRadius: 8, padding: '10px 14px', fontSize: 13 },
  detailBar:   {
    background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
    padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
  },
  detailLabel: { fontSize: 13, color: '#6b7280' },
  detailRange: { fontSize: 14, fontWeight: 500, color: '#1a1a1a' },
  detailProb:  { fontSize: 13, color: '#6b7280', marginLeft: 'auto' },
}