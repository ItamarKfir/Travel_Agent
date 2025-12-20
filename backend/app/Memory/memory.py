"""
Memory/history handler for chat conversations.
Handles building conversation context for different model types.
"""
import logging
from typing import List, Dict, Optional

from .database import get_messages as db_get_messages, save_message as db_save_message
from .database import get_session as db_get_session, create_session as db_create_session

logger = logging.getLogger(__name__)

# Import LangChain message types only when needed (optional dependency)
try:
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMessage = None
    HumanMessage = None
    AIMessage = None

def convert_to_langchain_messages(db_messages: List[Dict]) -> Optional[List]:
    """
    Convert database message format to LangChain message format.
    
    Database format: [{"role": "user|assistant", "content": "...", "created_at": "..."}]
    LangChain format: [HumanMessage(...), AIMessage(...), ...]
    
    Args:
        db_messages: List of message dictionaries from database
        
    Returns:
        List of LangChain BaseMessage objects (HumanMessage or AIMessage) if LangChain is available,
        None otherwise
        
    Note:
        This function requires langchain-core to be installed.
        Returns None if LangChain is not available.
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain not available, cannot convert to LangChain message format")
        return None
    
    langchain_messages = []
    
    for msg in db_messages:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        
        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        else:
            logger.warning(f"Unknown message role '{role}', skipping message")
            continue
    
    return langchain_messages


def convert_db_messages_to_langchain(db_messages: List[Dict]) -> List:
    """
    Convert database message format to LangChain message format.
    
    Database format: [{"role": "user|assistant", "content": "...", "created_at": "..."}]
    LangChain format: [HumanMessage(...), AIMessage(...), ...]
    
    Args:
        db_messages: List of message dictionaries from database
        
    Returns:
        List of LangChain BaseMessage objects (HumanMessage or AIMessage)
        Returns empty list if LangChain is not available.
    """
    # Use function from memory.py, with fallback if None
    langchain_messages = convert_to_langchain_messages(db_messages)
    
    if langchain_messages is None:
        # Fallback if LangChain not available (shouldn't happen, but safe)
        logger.warning("LangChain messages conversion returned None, returning empty list")
        return []
    
    return langchain_messages


def format_messages_for_agent_input(messages: List, current_input: str) -> str:
    """
    Format LangChain messages into a string format for AgentExecutor input.
    
    AgentExecutor expects a single string input, so we format conversation history
    as a text string that includes previous messages with clear separation between
    historical context and the current request.
    
    Args:
        messages: List of LangChain BaseMessage objects (conversation history)
        current_input: Current user input/question
        
    Returns:
        Formatted string with conversation history and current input
    """
    if not messages:
        return current_input
    
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain not available, returning current input only")
        return current_input
    
    # Build formatted input with clear sections
    formatted_parts = []
    
    # Add conversation history section
    formatted_parts.append("=== PREVIOUS CONVERSATION HISTORY ===")
    
    # Number turns for clarity
    turn_num = 1
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            formatted_parts.append(f"\n[Turn {turn_num}] User: {msg.content}")
            turn_num += 1
        elif isinstance(msg, AIMessage):
            formatted_parts.append(f"Assistant: {msg.content}")
    
    # Add clear separator and current request
    formatted_parts.append("\n" + "=" * 50)
    formatted_parts.append("=== CURRENT USER REQUEST (Answer this now) ===")
    formatted_parts.append(f"\nUser: {current_input}")
    formatted_parts.append("=" * 50)
    
    # Join with newlines
    formatted_input = "\n".join(formatted_parts)
    
    return formatted_input


def get_chat_memory(session_id: str) -> List:
    """
    Get chat history from database and convert to LangChain format.
    
    Args:
        session_id: Session ID to retrieve messages for
        
    Returns:
        List of LangChain BaseMessage objects representing conversation history
        Returns empty list if LangChain is not available or on error.
    """
    try:
        # Get messages from database
        db_messages = db_get_messages(session_id)
        
        # Convert to LangChain format
        langchain_messages = convert_db_messages_to_langchain(db_messages)
        
        logger.debug(f"Retrieved {len(langchain_messages)} messages for session {session_id}")
        return langchain_messages
    
    except Exception as e:
        logger.error(f"Error getting chat memory for session {session_id}: {e}")
        return []


def save_chat_message(session_id: str, role: str, content: str) -> bool:
    """
    Save a chat message to the database.
    
    Args:
        session_id: Session ID
        role: Message role ('user' or 'assistant')
        content: Message content
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        return db_save_message(session_id, role, content)
    except Exception as e:
        logger.error(f"Error saving chat message: {e}")
        return False


def ensure_session_exists(session_id: str, model: str) -> bool:
    """
    Ensure a session exists in the database, create if it doesn't.
    
    Args:
        session_id: Session ID
        model: Model name for the session
        
    Returns:
        True if session exists or was created successfully
    """
    try:
        if not db_get_session(session_id):
            logger.info(f"Session {session_id} does not exist, creating it with model {model}")
            return db_create_session(session_id, model)
        return True
    except Exception as e:
        logger.error(f"Error ensuring session exists: {e}")
        return False

