import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Judgments from './pages/Judgments'
import Transactions from './pages/Transactions'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <h1 className="nav-title">RWA Trading Agent</h1>
            <div className="nav-links">
              <Link to="/" className="nav-link">ダッシュボード</Link>
              <Link to="/judgments" className="nav-link">判断履歴</Link>
              <Link to="/transactions" className="nav-link">取引履歴</Link>
            </div>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/judgments" element={<Judgments />} />
            <Route path="/transactions" element={<Transactions />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

