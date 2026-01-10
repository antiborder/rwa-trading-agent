import React, { useEffect, useState } from 'react'
import { judgmentsApi, Judgment } from '../services/api'
import '../App.css'

const Judgments: React.FC = () => {
  const [judgments, setJudgments] = useState<Judgment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await judgmentsApi.getList(50)
      setJudgments(data)
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

  return (
    <div>
      <h1>判断履歴</h1>
      {judgments.length === 0 ? (
        <div className="card">
          <p>判断履歴がありません</p>
        </div>
      ) : (
        judgments.map((judgment) => (
          <div key={judgment.judgment_id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 className="card-title">判断ID: {judgment.judgment_id}</h2>
              <div>
                <span style={{ 
                  padding: '0.25rem 0.5rem', 
                  borderRadius: '4px',
                  backgroundColor: judgment.confidence_score >= 8 ? '#4caf50' : '#ff9800',
                  color: 'white',
                  fontWeight: 'bold'
                }}>
                  Confidence: {judgment.confidence_score}/10
                </span>
              </div>
            </div>
            <p><strong>判断日時:</strong> {new Date(judgment.timestamp).toLocaleString('ja-JP')}</p>
            
            <div style={{ marginTop: '1rem' }}>
              <h3>判断結果（目標資産比率）</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>資産</th>
                    <th>目標割合</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(judgment.target_allocations)
                    .filter(([_, value]) => value > 0.001)
                    .map(([symbol, ratio]) => (
                      <tr key={symbol}>
                        <td>{symbol}</td>
                        <td>{(ratio * 100).toFixed(2)}%</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <h3>判断根拠</h3>
              <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{judgment.reasoning_text}</p>
            </div>

            {judgment.source_urls.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h3>参考URL</h3>
                <ul>
                  {judgment.source_urls.map((url, index) => (
                    <li key={index}>
                      <a href={url} target="_blank" rel="noopener noreferrer">
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ marginTop: '1rem' }}>
              <h3>情報取得状況</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>情報源</th>
                    <th>取得状況</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(judgment.info_fetch_status).map(([source, status]) => (
                    <tr key={source}>
                      <td>{source}</td>
                      <td style={{ color: status ? 'green' : 'red' }}>
                        {status ? '成功' : '失敗'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {judgment.failed_sources.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h3>取得失敗した情報源</h3>
                <ul>
                  {judgment.failed_sources.map((source, index) => (
                    <li key={index} style={{ color: 'red' }}>{source}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}

export default Judgments

