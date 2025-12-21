import React from 'react'
import { Message } from '../types'
import '../App.css'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  return (
    <div className={`message-bubble ${message.role}`}>
      {message.content}
    </div>
  )
}

