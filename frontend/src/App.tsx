import { useState, useEffect, useRef } from 'react'

const API_BASE_URL = 'http://localhost:8000'

const ALLOWED_MODELS = [
  'gemini-2.5-flash-lite',
  'gemini-2.0-flash-lite',
  'gemini-2.5-flash',
  'gemini-2.5-flash'
]

interface Message {
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

interface Session {
  session_id: string
  model: string
}

function App() {
  const [sessionId, setSessionId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('gemini-2.5-flash-lite')
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [backendHealth, setBackendHealth] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    createNewSession(selectedModel)
    checkBackendHealth()
    // Check health every 30 seconds
    const healthInterval = setInterval(checkBackendHealth, 30000)
    return () => clearInterval(healthInterval)
  }, [])

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (response.ok) {
        const data = await response.json()
        setBackendHealth(data.status === 'healthy' ? 'healthy' : 'unhealthy')
      } else {
        setBackendHealth('unhealthy')
      }
    } catch (error) {
      setBackendHealth('unhealthy')
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const createNewSession = async (model: string) => {
    try {
      setIsLoading(true)
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model })
      })
      
      if (!response.ok) throw new Error('Failed to create session')
      
      const data: Session = await response.json()
      setSessionId(data.session_id)
      setSelectedModel(data.model)
      setMessages([])
      
      await loadMessages(data.session_id)
    } catch (error) {
      console.error('Error creating session:', error)
      alert('Failed to create session. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const loadMessages = async (sid: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sid}/messages`)
      if (!response.ok) throw new Error('Failed to load messages')
      
      const loadedMessages: Message[] = await response.json()
      setMessages(loadedMessages.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      })))
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const handleNewSession = async () => {
    await createNewSession(selectedModel)
  }

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(e.target.value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sessionId || !inputValue.trim() || isLoading) return

    const userMessage = inputValue.trim()
    setInputValue('')

    // Add user message to UI immediately
    const newUserMessage: Message = { role: 'user', content: userMessage }
    setMessages(prev => [...prev, newUserMessage])

    // Add placeholder for assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          model: selectedModel
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      // Handle streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullAnswer = ''

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
                fullAnswer += data
                // Update the last assistant message in real-time
                setMessages(prev => {
                  const updated = [...prev]
                  const lastIndex = updated.length - 1
                  if (lastIndex >= 0 && updated[lastIndex].role === 'assistant') {
                    updated[lastIndex] = { role: 'assistant', content: fullAnswer }
                  }
                  return updated
                })
              }
            }
          }
        }
      }
      
      // Reload messages to stay in sync with database
      await loadMessages(sessionId)
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => {
        const updated = [...prev]
        const lastIndex = updated.length - 1
        if (lastIndex >= 0 && updated[lastIndex].role === 'assistant') {
          updated[lastIndex] = {
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.'
          }
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top Bar */}
      <div style={{
        padding: '1rem 1.5rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #1a1a1a 0%, #252525 100%)',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.3)'
      }}>
        <select
          value={selectedModel}
          onChange={handleModelChange}
          style={{
            padding: '0.6rem 1.2rem',
            background: 'linear-gradient(135deg, #2a2a2a 0%, #333 100%)',
            color: '#e0e0e0',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            outline: 'none'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)'
            e.currentTarget.style.transform = 'translateY(-1px)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
        >
          {ALLOWED_MODELS.map(model => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
        
        <button
          onClick={handleNewSession}
          disabled={isLoading}
          style={{
            padding: '0.6rem 1.2rem',
            background: isLoading 
              ? 'linear-gradient(135deg, #2a2a2a 0%, #333 100%)'
              : 'linear-gradient(135deg, #3a3a3a 0%, #4a4a4a 100%)',
            color: '#e0e0e0',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            fontSize: '0.9rem',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.6 : 1,
            transition: 'all 0.2s',
            fontWeight: '500'
          }}
          onMouseEnter={(e) => {
            if (!isLoading) {
              e.currentTarget.style.transform = 'translateY(-1px)'
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = 'none'
          }}
        >
          New Session
        </button>
        
        <div style={{
          marginLeft: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
            color: '#888',
            fontFamily: 'monospace'
          }}>
            <span>Session:</span>
            <span style={{ color: '#aaa' }}>{sessionId ? sessionId.substring(0, 8) : '...'}</span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.75rem'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: backendHealth === 'healthy' ? '#4ade80' : backendHealth === 'unhealthy' ? '#f87171' : '#fbbf24',
              boxShadow: backendHealth === 'healthy' ? '0 0 8px #4ade80' : 'none',
              animation: backendHealth === 'checking' ? 'pulse 2s infinite' : 'none'
            }} />
            <span style={{
              color: backendHealth === 'healthy' ? '#4ade80' : backendHealth === 'unhealthy' ? '#f87171' : '#fbbf24',
              fontWeight: '500'
            }}>
              {backendHealth === 'healthy' ? 'Online' : backendHealth === 'unhealthy' ? 'Offline' : 'Checking...'}
            </span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        background: 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)'
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: '#666',
            marginTop: '2rem'
          }}>
            Start a conversation by typing a message below
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '70%',
              padding: '1rem 1.25rem',
              borderRadius: '16px',
              background: msg.role === 'user' 
                ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
                : 'linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%)',
              color: '#e0e0e0',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              boxShadow: msg.role === 'user' 
                ? '0 4px 12px rgba(59, 130, 246, 0.3)'
                : '0 4px 12px rgba(0, 0, 0, 0.4)',
              border: msg.role === 'user' 
                ? '1px solid rgba(59, 130, 246, 0.2)'
                : '1px solid rgba(255, 255, 255, 0.05)',
              lineHeight: '1.6',
              fontSize: '0.95rem'
            }}
          >
            {msg.content}
          </div>
        ))}
        
        {isLoading && messages[messages.length - 1]?.content === '' && (
          <div style={{
            alignSelf: 'flex-start',
            padding: '1rem 1.25rem',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%)',
            color: '#888',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <div style={{
              width: '12px',
              height: '12px',
              border: '2px solid #444',
              borderTopColor: '#888',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <span>Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '1.5rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        background: 'linear-gradient(135deg, #1a1a1a 0%, #252525 100%)',
        boxShadow: '0 -2px 10px rgba(0, 0, 0, 0.3)'
      }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '0.875rem 1.25rem',
              background: 'linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%)',
              color: '#e0e0e0',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              fontSize: '1rem',
              outline: 'none',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.5)'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            style={{
              padding: '0.875rem 2rem',
              background: (isLoading || !inputValue.trim())
                ? 'linear-gradient(135deg, #2a2a2a 0%, #333 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              color: '#e0e0e0',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: (isLoading || !inputValue.trim()) ? 'not-allowed' : 'pointer',
              opacity: (isLoading || !inputValue.trim()) ? 0.6 : 1,
              transition: 'all 0.2s',
              boxShadow: (isLoading || !inputValue.trim()) ? 'none' : '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}
            onMouseEnter={(e) => {
              if (!isLoading && inputValue.trim()) {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.4)'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = (isLoading || !inputValue.trim()) ? 'none' : '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

