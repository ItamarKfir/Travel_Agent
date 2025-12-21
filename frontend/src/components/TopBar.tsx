import React from 'react'
import { BackendHealth } from '../types'
import '../App.css'

interface TopBarProps {
  selectedModel: string
  sessionId: string
  backendHealth: BackendHealth
  isLoading: boolean
  allowedModels: string[]
  onModelChange: (e: React.ChangeEvent<HTMLSelectElement>) => void
  onNewSession: () => void
}

export const TopBar: React.FC<TopBarProps> = ({
  selectedModel,
  sessionId,
  backendHealth,
  isLoading,
  allowedModels,
  onModelChange,
  onNewSession,
}) => {
  const getHealthIndicatorClass = () => {
    return `health-indicator ${backendHealth}`
  }

  const getHealthTextClass = () => {
    return `health-text ${backendHealth}`
  }

  const getHealthText = () => {
    switch (backendHealth) {
      case 'healthy':
        return 'Online'
      case 'unhealthy':
        return 'Offline'
      case 'checking':
        return 'Checking...'
    }
  }

  return (
    <div className="top-bar">
      <select
        value={selectedModel}
        onChange={onModelChange}
        className="top-bar-select"
      >
        {allowedModels.map(model => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
      </select>

      <button
        onClick={onNewSession}
        disabled={isLoading}
        className="top-bar-button"
      >
        New Session
      </button>

      <div className="top-bar-right">
        <div className="session-info">
          <span>Session:</span>
          <span className="session-id">
            {sessionId ? sessionId.substring(0, 8) : '...'}
          </span>
        </div>
        <div className="health-status">
          <div className={getHealthIndicatorClass()} />
          <span className={getHealthTextClass()}>{getHealthText()}</span>
        </div>
      </div>
    </div>
  )
}

