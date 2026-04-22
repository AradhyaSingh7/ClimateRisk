import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Risk score → colour
function riskColor(score) {
  if (score >= 65) return '#E24B4A'
  if (score >= 35) return '#EF9F27'
  return '#639922'
}

export default function RiskMap({ regions = [], onStateClick, selectedState }) {
  const mapRef    = useRef(null)
  const mapObj    = useRef(null)
  const layerRef  = useRef(null)

  // Init map once
  useEffect(() => {
    if (mapObj.current) return
    mapObj.current = L.map(mapRef.current, {
      center: [38.5, -96],
      zoom: 4,
      zoomControl: true,
      scrollWheelZoom: true,
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap contributors © CARTO',
      maxZoom: 10,
    }).addTo(mapObj.current)
  }, [])

  // Update circles whenever data changes
  useEffect(() => {
    if (!mapObj.current || !regions.length) return

    if (layerRef.current) layerRef.current.clearLayers()
    layerRef.current = L.layerGroup().addTo(mapObj.current)

    regions.forEach(r => {
      const color   = riskColor(r.risk_score)
      const radius  = 60000 + r.risk_score * 2000   // scale by risk

      const circle = L.circle([r.lat, r.lon], {
        color,
        fillColor: color,
        fillOpacity: 0.55,
        weight: 1.5,
        radius,
      })

      circle.bindTooltip(
        `<b>${r.state}</b><br>
         Risk: <b>${r.risk_score}%</b><br>
         Tier: <b>${r.risk_tier}</b><br>
         Exposure: <b>$${(r.estimated_damage_usd / 1e6).toFixed(0)}M</b>`,
        { sticky: true }
      )

      circle.on('click', () => onStateClick && onStateClick(r.state))

      if (r.state === selectedState) {
        circle.setStyle({ weight: 3, color: '#1a1a1a', fillOpacity: 0.75 })
      }

      circle.addTo(layerRef.current)
    })
  }, [regions, selectedState])

  return (
    <div style={styles.wrap}>
      <div style={styles.legend}>
        <span style={styles.legText}>Low</span>
        <div style={styles.legBar} />
        <span style={styles.legText}>High</span>
      </div>
      <div ref={mapRef} style={styles.map} />
    </div>
  )
}

const styles = {
  wrap: { position: 'relative', borderRadius: 10, overflow: 'hidden', border: '1px solid #e5e7eb' },
  map:  { height: 380, width: '100%' },
  legend: {
    position: 'absolute', bottom: 16, right: 16, zIndex: 1000,
    display: 'flex', alignItems: 'center', gap: 6,
    background: 'rgba(255,255,255,0.9)', borderRadius: 20,
    padding: '4px 10px', fontSize: 11, color: '#6b7280',
  },
  legBar: {
    width: 72, height: 5, borderRadius: 3,
    background: 'linear-gradient(to right, #639922, #EF9F27, #E24B4A)',
  },
  legText: { fontSize: 11, color: '#6b7280' },
}