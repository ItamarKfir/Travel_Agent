"""
Memory/history handler for chat conversations.
Handles building conversation context for different model types.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def build_chat_history(messages: List[Dict]) -> List[Dict]:
    """
    Build chat history format for Gemini models.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
    
    Returns:
        List of chat history items in Gemini format
    """
    chat_history = []
    for msg in messages:
        if msg["role"] == "user":
            chat_history.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] == "assistant":
            chat_history.append({"role": "model", "parts": [msg["content"]]})
    return chat_history


def build_prompt_with_history(messages: List[Dict], current_message: str) -> str:
    """
    Build a text prompt with conversation history for models that don't support chat.
    
    Args:
        messages: List of previous messages
        current_message: The current user message
    
    Returns:
        Formatted prompt string with conversation history
    """
    prompt_parts = []
    
    for msg in messages:
        if msg["role"] == "user":
            prompt_parts.append(f"User: {msg['content']}")
        elif msg["role"] == "assistant":
            prompt_parts.append(f"Assistant: {msg['content']}")
    
    prompt_parts.append(f"User: {current_message}")
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)


def prepare_for_chat(messages: List[Dict], current_message: str) -> tuple[List[Dict], str]:
    """
    Prepare conversation history and current message for chat API.
    
    Args:
        messages: List of previous messages
        current_message: The current user message
    
    Returns:
        Tuple of (chat_history, current_message)
    """
    chat_history = build_chat_history(messages)
    return chat_history, current_message


def prepare_for_direct_generation(messages: List[Dict], current_message: str) -> str:
    """
    Prepare conversation as a single prompt for direct generation.
    
    Args:
        messages: List of previous messages
        current_message: The current user message
    
    Returns:
        Full prompt string
    """
    return build_prompt_with_history(messages, current_message)

