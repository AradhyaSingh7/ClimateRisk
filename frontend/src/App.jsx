import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Compare from './pages/Compare'
import About from './pages/About'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/"        element={<Dashboard />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/about"   element={<About />} />
      </Routes>
    </BrowserRouter>
  )
}