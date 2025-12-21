export interface Message {
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export interface Session {
  session_id: string
  model: string
}

export type BackendHealth = 'healthy' | 'unhealthy' | 'checking'

