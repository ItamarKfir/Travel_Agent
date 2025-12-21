import React from 'react'
import '../App.css'

interface InputAreaProps {
  inputValue: string
  isLoading: boolean
  onInputChange: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
}

export const InputArea: React.FC<InputAreaProps> = ({
  inputValue,
  isLoading,
  onInputChange,
  onSubmit,
}) => {
  return (
    <div className="input-area">
      <form onSubmit={onSubmit} className="input-form">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder="Ask about a business, get reviews, or request analysis (e.g., 'Get reviews for Hotel XYZ in Paris')..."
          disabled={isLoading}
          className="input-field"
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="send-button"
        >
          Send
        </button>
      </form>
    </div>
  )
}

