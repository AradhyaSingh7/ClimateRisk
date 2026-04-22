import React from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',        label: 'Dashboard' },
  { to: '/compare', label: 'Compare regions' },
  { to: '/about',   label: 'About' },
]

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <span style={styles.brand}>ClimateRisk</span>
      <div style={styles.links}>
        {links.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            end
            style={({ isActive }) => ({
              ...styles.link,
              color: isActive ? '#1a1a1a' : '#6b7280',
              fontWeight: isActive ? 500 : 400,
            })}
          >
            {l.label}
          </NavLink>
        ))}
      </div>
      <span style={styles.badge}>ML Project</span>
    </nav>
  )
}

const styles = {
  nav: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 24px', height: 52, background: '#fff',
    borderBottom: '1px solid #e5e7eb', flexShrink: 0,
  },
  brand: { fontSize: 15, fontWeight: 600, letterSpacing: '-0.01em' },
  links: { display: 'flex', gap: 24 },
  link:  { textDecoration: 'none', fontSize: 14, transition: 'color .15s' },
  badge: {
    fontSize: 11, padding: '3px 10px', borderRadius: 20,
    background: '#EAF3DE', color: '#3B6D11', fontWeight: 500,
  },
}