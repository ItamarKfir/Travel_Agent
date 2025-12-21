import { Message, Session } from '../types'

const API_BASE_URL = 'http://localhost:8000'

export const apiClient = {
  async checkHealth(): Promise<'healthy' | 'unhealthy'> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (response.ok) {
        const data = await response.json()
        return data.status === 'healthy' ? 'healthy' : 'unhealthy'
      }
      return 'unhealthy'
    } catch {
      return 'unhealthy'
    }
  },

  async createSession(model: string): Promise<Session> {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model }),
    })

    if (!response.ok) {
      throw new Error('Failed to create session')
    }

    return response.json()
  },

  async getMessages(sessionId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`)
    if (!response.ok) {
      throw new Error('Failed to load messages')
    }
    return response.json()
  },

  async sendMessage(
    sessionId: string,
    message: string,
    model: string,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        model,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to get response')
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              break
            } else if (data.startsWith('[ERROR]')) {
              throw new Error(data.slice(8))
            } else if (data) {
              onChunk(data)
            }
          }
        }
      }
    }
  },
}

