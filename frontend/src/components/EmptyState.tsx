import React from 'react'
import '../App.css'

interface EmptyStateProps {
  onExampleClick: (example: string) => void
}

const EXAMPLE_QUESTIONS = [
  'Tell me about Hilton Tel Aviv',
  'What are the main complaints about Hilton Tel Aviv?',
  'Summarize the positive feedback from customers on Sheraton Grand Tel Aviv',
  'Compare reviews from Google Places vs TripAdvisor for Sheraton Grand Tel Aviv',
]

export const EmptyState: React.FC<EmptyStateProps> = ({ onExampleClick }) => {
  const handleExampleClick = (example: string) => {
    const cleaned = example
      .replace('[Hotel/Restaurant Name]', '')
      .replace(' in [Location]', '')
      .trim()
    onExampleClick(cleaned)
  }

  return (
    <div className="empty-state">
      <div className="empty-state-header">
        <h2 className="empty-state-title">🤖 Smart AI Business Assistant</h2>
        <p className="empty-state-description">
          Analyze customer reviews from Google Places and TripAdvisor to get
          actionable insights for your business
        </p>
      </div>

      <div className="empty-state-section">
        <h3 className="empty-state-section-title">
          <span>💬</span> Example Questions
        </h3>
        <div className="example-questions">
          {EXAMPLE_QUESTIONS.map((example, idx) => (
            <div
              key={idx}
              onClick={() => handleExampleClick(example)}
              className="example-question"
            >
              &quot;{example}&quot;
            </div>
          ))}
        </div>
      </div>

      <div className="empty-state-tip">
        <p className="empty-state-tip-text">
          💡 <strong>Tip:</strong> Start by asking about a specific business or
          place. The AI will automatically fetch reviews and provide analysis.
        </p>
      </div>
    </div>
  )
}

