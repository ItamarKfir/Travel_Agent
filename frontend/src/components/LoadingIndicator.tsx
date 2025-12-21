import React from 'react'
import '../App.css'

export const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading-indicator">
      <div className="loading-spinner" />
      <span>Thinking...</span>
    </div>
  )
}

