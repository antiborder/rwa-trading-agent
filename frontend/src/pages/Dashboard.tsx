import React, { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { portfolioApi, PortfolioCurrent, Performance, CurrencyPerformance } from '../services/api'
import '../App.css'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff']

const Dashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioCurrent | null>(null)
  const [performance, setPerformance] = useState<Performance[]>([])
  const [currencyPerformance, setCurrencyPerformance] = useState<CurrencyPerformance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [portfolioData, performanceData, currencyData] = await Promise.all([
        portfolioApi.getCurrent(),
        portfolioApi.getPerformance(),
        portfolioApi.getCurrencyPerformance(),
      ])

      setPortfolio(portfolioData)
      setPerformance(performanceData)
      setCurrencyPerformance(currencyData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">読み込み中...</div>
  }

  if (error) {
    return (
      <div>
        <div className="error">{error}</div>
        <button onClick={loadData}>再読み込み</button>
      </div>
    )
  }

  const pieData = portfolio
    ? Object.entries(portfolio.allocations)
        .filter(([_, value]) => value > 0.01)
        .map(([name, value]) => ({
          name,
          value: value * 100,
        }))
    : []

  const performanceData = performance.map((p) => ({
    period: p.period,
    change: p.change_percent,
  }))

  return (
    <div>
      <h1>ダッシュボード</h1>

      {portfolio && (
        <>
          <div className="card">
            <h2 className="card-title">資産内訳</h2>
            <div style={{ display: 'flex', gap: '2rem' }}>
              <div style={{ flex: 1 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ flex: 1 }}>
                <h3>総資産: ${portfolio.total_value_usdt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h3>
                <table className="table">
                  <thead>
                    <tr>
                      <th>資産</th>
                      <th>数量</th>
                      <th>USDT価値</th>
                      <th>割合</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(portfolio.allocations)
                      .filter(([_, value]) => value > 0.01)
                      .map(([symbol, ratio]) => (
                        <tr key={symbol}>
                          <td>{symbol}</td>
                          <td>{portfolio.holdings[symbol]?.toFixed(4) || '0.0000'}</td>
                          <td>${portfolio.values_usdt[symbol]?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}</td>
                          <td>{(ratio * 100).toFixed(2)}%</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="card-title">資産全体の騰落率</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
                <Legend />
                <Bar dataKey="change" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
            <table className="table">
              <thead>
                <tr>
                  <th>期間</th>
                  <th>総資産</th>
                  <th>騰落率</th>
                </tr>
              </thead>
              <tbody>
                {performance.map((p) => (
                  <tr key={p.period}>
                    <td>{p.period}</td>
                    <td>${p.total_value_usdt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td style={{ color: p.change_percent >= 0 ? 'green' : 'red' }}>
                      {p.change_percent >= 0 ? '+' : ''}{p.change_percent.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="card">
        <h2 className="card-title">各通貨の騰落率</h2>
        <table className="table">
          <thead>
            <tr>
              <th>通貨</th>
              <th>現在価格</th>
              <th>24時間</th>
              <th>1日</th>
              <th>1週間</th>
              <th>1ヶ月</th>
            </tr>
          </thead>
          <tbody>
            {currencyPerformance.map((cp) => (
              <tr key={cp.symbol}>
                <td>{cp.symbol}</td>
                <td>${cp.current_price.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 4 })}</td>
                <td style={{ color: cp.change_24h >= 0 ? 'green' : 'red' }}>
                  {cp.change_24h >= 0 ? '+' : ''}{cp.change_24h.toFixed(2)}%
                </td>
                <td style={{ color: (cp.change_1d || 0) >= 0 ? 'green' : 'red' }}>
                  {typeof cp.change_1d === 'number' ? `${cp.change_1d >= 0 ? '+' : ''}${cp.change_1d.toFixed(2)}%` : '-'}
                </td>
                <td style={{ color: (cp.change_1w || 0) >= 0 ? 'green' : 'red' }}>
                  {typeof cp.change_1w === 'number' ? `${cp.change_1w >= 0 ? '+' : ''}${cp.change_1w.toFixed(2)}%` : '-'}
                </td>
                <td style={{ color: (cp.change_1m || 0) >= 0 ? 'green' : 'red' }}>
                  {typeof cp.change_1m === 'number' ? `${cp.change_1m >= 0 ? '+' : ''}${cp.change_1m.toFixed(2)}%` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard

