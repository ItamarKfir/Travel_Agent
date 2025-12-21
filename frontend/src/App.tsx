import { useState, useEffect, useRef } from 'react'
import { Message, BackendHealth } from './types'
import { apiClient } from './api/client'
import { TopBar } from './components/TopBar'
import { EmptyState } from './components/EmptyState'
import { MessageBubble } from './components/MessageBubble'
import { InputArea } from './components/InputArea'
import { LoadingIndicator } from './components/LoadingIndicator'
import './App.css'

const ALLOWED_MODELS = [
  'gemini-2.5-flash-lite',
  'gemini-2.0-flash-lite',
  'gemini-2.5-flash',
  'gemini-2.5-flash',
]

function App() {
  const [sessionId, setSessionId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('gemini-2.5-flash-lite')
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [backendHealth, setBackendHealth] = useState<BackendHealth>('checking')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    createNewSession(selectedModel)
    checkBackendHealth()
    // Check health every 30 seconds
    const healthInterval = setInterval(checkBackendHealth, 30000)
    return () => clearInterval(healthInterval)
  }, [])

  const checkBackendHealth = async () => {
    const health = await apiClient.checkHealth()
    setBackendHealth(health)
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadMessages = async (sid: string) => {
    try {
      const loadedMessages = await apiClient.getMessages(sid)
      setMessages(
        loadedMessages.map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
        }))
      )
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const createNewSession = async (model: string) => {
    try {
      setIsLoading(true)
      const session = await apiClient.createSession(model)
      setSessionId(session.session_id)
      setSelectedModel(session.model)
      setMessages([])
      await loadMessages(session.session_id)
    } catch (error) {
      console.error('Error creating session:', error)
      alert('Failed to create session. Please try again.')
    } finally {
      setIsLoading(false)
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
      let fullAnswer = ''
      
      await apiClient.sendMessage(
        sessionId,
        userMessage,
        selectedModel,
        (chunk) => {
          fullAnswer += chunk
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
      )
      
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
            content: 'Sorry, I encountered an error. Please try again.',
          }
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleClick = (example: string) => {
    setInputValue(example)
  }

  const isShowingLoadingIndicator = isLoading && messages[messages.length - 1]?.content === ''

  return (
    <div className="app-container">
      <TopBar
        selectedModel={selectedModel}
        sessionId={sessionId}
        backendHealth={backendHealth}
        isLoading={isLoading}
        allowedModels={ALLOWED_MODELS}
        onModelChange={handleModelChange}
        onNewSession={handleNewSession}
      />

      <div className="messages-area">
        {messages.length === 0 && (
          <EmptyState onExampleClick={handleExampleClick} />
        )}

        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {isShowingLoadingIndicator && <LoadingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      <InputArea
        inputValue={inputValue}
        isLoading={isLoading}
        onInputChange={setInputValue}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

export default App
