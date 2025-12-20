"""
Agent Manager for managing LLM agent operations.

This module provides a centralized interface for:
- Creating and managing React agents
- Setting system prompts
- Managing chat history/memory (converting database format to LangChain format)
- Running agents with conversation context
"""
import logging
from typing import List, Optional, Dict
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from .agent import ReactAgent, initialize_agent, DEFAULT_MODEL
from .prompts import TRAVEL_AGENT_SYSTEM_PROMPT, get_system_prompt_with_history
from app.Memory.database import get_messages as db_get_messages, save_message as db_save_message
from app.Memory.database import get_session as db_get_session, create_session as db_create_session
from app.Memory.memory import convert_to_langchain_messages

logger = logging.getLogger(__name__)


def convert_db_messages_to_langchain(db_messages: List[Dict]) -> List[BaseMessage]:
    """
    Convert database message format to LangChain message format.
    
    Database format: [{"role": "user|assistant", "content": "...", "created_at": "..."}]
    LangChain format: [HumanMessage(...), AIMessage(...), ...]
    
    Args:
        db_messages: List of message dictionaries from database
        
    Returns:
        List of LangChain BaseMessage objects (HumanMessage or AIMessage)
    """
    # Use function from memory.py, with fallback if None
    langchain_messages = convert_to_langchain_messages(db_messages)
    
    if langchain_messages is None:
        # Fallback if LangChain not available (shouldn't happen, but safe)
        logger.warning("LangChain messages conversion returned None, returning empty list")
        return []
    
    return langchain_messages


def format_messages_for_agent_input(messages: List[BaseMessage], current_input: str) -> str:
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


def get_chat_memory(session_id: str) -> List[BaseMessage]:
    """
    Get chat history from database and convert to LangChain format.
    
    Args:
        session_id: Session ID to retrieve messages for
        
    Returns:
        List of LangChain BaseMessage objects representing conversation history
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


class AgentManager:
    """
    Manages React agent operations including memory and system prompts.
    
    This class provides a high-level interface for:
    - Creating/managing agent instances
    - Setting system prompts
    - Managing conversation history
    - Running agents with context
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the AgentManager.
        
        Args:
            model: Model name (defaults to DEFAULT_MODEL)
            tools: List of tools for the agent (optional)
            system_prompt: System prompt for the agent (optional)
            api_key: Google API key (optional, uses env var if not provided)
        """
        self.model = model or DEFAULT_MODEL
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.api_key = api_key
        
        # Initialize agent instance
        self._agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the React agent instance."""
        try:
            self._agent = initialize_agent(
                model=self.model,
                tools=self.tools if self.tools else None,
                system_prompt=self.system_prompt,
                api_key=self.api_key
            )
            logger.info(f"AgentManager initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def set_system_prompt(self, prompt: str):
        """
        Set or update the system prompt for the agent.
        
        Args:
            prompt: System prompt text
        """
        self.system_prompt = prompt
        
        if self._agent:
            self._agent.set_system_prompt(prompt)
            logger.info("System prompt updated")
        else:
            logger.warning("Agent not initialized, system prompt will be set on next agent creation")
    
    def get_system_prompt(self) -> Optional[str]:
        """
        Get the current system prompt.
        
        Returns:
            Current system prompt or None
        """
        return self.system_prompt
    
    def get_memory(self, session_id: str) -> List[BaseMessage]:
        """
        Get conversation history for a session in LangChain format.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of LangChain BaseMessage objects
        """
        return get_chat_memory(session_id)
    
    def save_to_memory(self, session_id: str, role: str, content: str) -> bool:
        """
        Save a message to the conversation memory (database).
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            True if saved successfully
        """
        return save_chat_message(session_id, role, content)
    
    def run(
        self,
        input_text: str,
        session_id: Optional[str] = None,
        include_history: bool = True
    ) -> str:
        """
        Run the agent with optional conversation history.
        
        Args:
            input_text: User input/question
            session_id: Optional session ID to include conversation history
            include_history: Whether to include conversation history (default: True)
            
        Returns:
            Agent response text
        """
        try:
            # Determine if we have history and need to use history-aware prompt
            has_history = False
            history = []
            if session_id and include_history:
                history = self.get_memory(session_id)
                has_history = len(history) > 0
            
            # Store original prompt to restore later
            original_prompt = self._agent.system_prompt
            
            # Prepare input with history if requested
            if has_history:
                # Format for agent input with history
                agent_input = format_messages_for_agent_input(history, input_text)
                # Use system prompt with history context
                self._agent.set_system_prompt(get_system_prompt_with_history())
                logger.debug(f"Using history-aware prompt. History length: {len(history)} messages, formatted input length: {len(agent_input)} chars")
            else:
                # First message - no history
                agent_input = input_text
                # Use base system prompt (no history context)
                self._agent.set_system_prompt(TRAVEL_AGENT_SYSTEM_PROMPT)
                logger.debug(f"No history, using base prompt. Input: {input_text[:100]}...")
            
            # Run the agent
            response = self._agent.run(agent_input)
            
            # Restore original prompt
            self._agent.set_system_prompt(original_prompt)
            
            # Save to memory if session_id provided
            if session_id:
                # Save user message
                self.save_to_memory(session_id, "user", input_text)
                # Save assistant response
                self.save_to_memory(session_id, "assistant", response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            raise
    
    def stream(
        self,
        input_text: str,
        session_id: Optional[str] = None,
        include_history: bool = True
    ):
        """
        Stream agent response with optional conversation history.
        
        Args:
            input_text: User input/question
            session_id: Optional session ID to include conversation history
            include_history: Whether to include conversation history (default: True)
            
        Yields:
            Response text chunks
        """
        try:
            # Determine if we have history and need to use history-aware prompt
            has_history = False
            history = []
            if session_id and include_history:
                history = self.get_memory(session_id)
                has_history = len(history) > 0
            
            # Store original prompt to restore later
            original_prompt = self._agent.system_prompt
            
            # Prepare input with history if requested
            if has_history:
                # Format for agent input with history
                agent_input = format_messages_for_agent_input(history, input_text)
                # Use system prompt with history context
                self._agent.set_system_prompt(get_system_prompt_with_history())
                logger.debug(f"Using history-aware prompt for streaming. History length: {len(history)} messages, formatted input length: {len(agent_input)} chars")
            else:
                # First message - no history
                agent_input = input_text
                # Use base system prompt (no history context)
                self._agent.set_system_prompt(TRAVEL_AGENT_SYSTEM_PROMPT)
                logger.debug(f"No history for streaming, using base prompt. Input: {input_text[:100]}...")
            
            # Save user message before streaming (if session_id provided)
            if session_id:
                self.save_to_memory(session_id, "user", input_text)
            
            # Stream agent response
            full_response = ""
            for chunk in self._agent.stream(agent_input):
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Restore original prompt
            self._agent.set_system_prompt(original_prompt)
            
            # Save assistant response after streaming completes
            if session_id and full_response:
                self.save_to_memory(session_id, "assistant", full_response)
        
        except Exception as e:
            logger.error(f"Error streaming agent response: {e}", exc_info=True)
            raise
    
    def get_agent(self) -> ReactAgent:
        """
        Get the underlying ReactAgent instance.
        
        Returns:
            ReactAgent instance
        """
        return self._agent


# Global agent manager instance (singleton pattern)
_agent_manager_instance: Optional[AgentManager] = None


def get_agent_manager(
    model: Optional[str] = None,
    tools: Optional[List] = None,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    force_new: bool = False
) -> AgentManager:
    """
    Get or create the global AgentManager instance.
    
    Args:
        model: Model name (only used if creating new instance)
        tools: Tools for the agent (only used if creating new instance)
        system_prompt: System prompt (only used if creating new instance)
        api_key: Google API key (only used if creating new instance)
        force_new: If True, create a new instance instead of reusing
        
    Returns:
        AgentManager instance
    """
    global _agent_manager_instance
    
    if _agent_manager_instance is None or force_new:
        _agent_manager_instance = AgentManager(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            api_key=api_key
        )
        logger.info("Created new AgentManager instance")
    
    return _agent_manager_instance
