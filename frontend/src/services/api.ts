import axios from 'axios'

// 環境変数からAPI URLを取得（本番環境ではAPI Gateway URL、開発環境ではlocalhost）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface PortfolioCurrent {
  holdings: Record<string, number>
  values_usdt: Record<string, number>
  total_value_usdt: number
  allocations: Record<string, number>
  timestamp: string
}

export interface Performance {
  period: string
  total_value_usdt: number
  change_percent: number
}

export interface CurrencyPerformance {
  symbol: string
  current_price: number
  change_24h: number
  change_1d?: number
  change_1w?: number
  change_1m?: number
}

export interface Judgment {
  judgment_id: string
  timestamp: string
  confidence_score: number
  target_allocations: Record<string, number>
  reasoning_text: string
  source_urls: string[]
  info_fetch_status: Record<string, boolean>
  failed_sources: string[]
}

export interface Transaction {
  transaction_id: string
  timestamp: string
  symbol: string
  side: string
  amount: number
  price: number
  status: string
  pre_allocation: Record<string, number>
  post_allocation: Record<string, number>
}

export const portfolioApi = {
  getCurrent: async (): Promise<PortfolioCurrent> => {
    const response = await api.get<PortfolioCurrent>('/api/portfolio/current')
    return response.data
  },

  getPerformance: async (): Promise<Performance[]> => {
    const response = await api.get<Performance[]>('/api/portfolio/performance')
    return response.data
  },

  getCurrencyPerformance: async (): Promise<CurrencyPerformance[]> => {
    const response = await api.get<CurrencyPerformance[]>('/api/portfolio/currency-performance')
    return response.data
  },
}

export const judgmentsApi = {
  getList: async (limit: number = 50, lastKey?: string): Promise<Judgment[]> => {
    const params: any = { limit }
    if (lastKey) params.last_key = lastKey
    const response = await api.get<Judgment[]>('/api/judgments', { params })
    return response.data
  },

  getById: async (judgmentId: string): Promise<Judgment> => {
    const response = await api.get<Judgment>(`/api/judgments/${judgmentId}`)
    return response.data
  },
}

export const transactionsApi = {
  getList: async (limit: number = 50, lastKey?: string): Promise<Transaction[]> => {
    const params: any = { limit }
    if (lastKey) params.last_key = lastKey
    const response = await api.get<Transaction[]>('/api/transactions', { params })
    return response.data
  },

  getById: async (transactionId: string): Promise<Transaction> => {
    const response = await api.get<Transaction>(`/api/transactions/${transactionId}`)
    return response.data
  },
}

