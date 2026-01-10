import React, { useEffect, useState } from 'react'
import { transactionsApi, Transaction } from '../services/api'
import '../App.css'

const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await transactionsApi.getList(50)
      setTransactions(data)
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
      <h1>取引履歴</h1>
      {transactions.length === 0 ? (
        <div className="card">
          <p>取引履歴がありません</p>
        </div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>取引日時</th>
                <th>通貨</th>
                <th>方向</th>
                <th>数量</th>
                <th>価格</th>
                <th>成否</th>
                <th>取引前資産割合</th>
                <th>取引後資産割合</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.transaction_id}>
                  <td>{new Date(transaction.timestamp).toLocaleString('ja-JP')}</td>
                  <td>{transaction.symbol}</td>
                  <td>
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: transaction.side === 'buy' ? '#4caf50' : '#f44336',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      {transaction.side === 'buy' ? '買い' : '売り'}
                    </span>
                  </td>
                  <td>{transaction.amount.toFixed(4)}</td>
                  <td>${transaction.price.toFixed(4)}</td>
                  <td>
                    <span style={{
                      color: transaction.status === 'success' ? 'green' : 'red',
                      fontWeight: 'bold'
                    }}>
                      {transaction.status === 'success' ? '成功' : '失敗'}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.9rem' }}>
                      {Object.entries(transaction.pre_allocation)
                        .filter(([_, value]) => value > 0.01)
                        .map(([symbol, ratio]) => (
                          <div key={symbol}>{symbol}: {(ratio * 100).toFixed(1)}%</div>
                        ))}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.9rem' }}>
                      {Object.entries(transaction.post_allocation)
                        .filter(([_, value]) => value > 0.01)
                        .map(([symbol, ratio]) => (
                          <div key={symbol}>{symbol}: {(ratio * 100).toFixed(1)}%</div>
                        ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Transactions

