"""
Chat handler with support for LangChain agents (Google models) and direct generation (Gemma models).
"""
import logging
import google.generativeai as genai
from typing import Iterator

from .database import get_messages, save_message, get_session, create_session
from .memory import prepare_for_direct_generation
from .models import model_manager
from .agent import create_react_agent, stream_agent_response
from .gemma_tools import stream_gemma_with_tools

logger = logging.getLogger(__name__)


def init_genai():
    """Initialize the Google Generative AI client (lazy - models load on first use)."""
    model_manager.initialize()
    
    # List available models for debugging
    try:
        models = genai.list_models()
        available_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                model_name = m.name.replace('models/', '') if m.name.startswith('models/') else m.name
                available_models.append(model_name)
        
        if available_models:
            logger.info(f"Available models: {', '.join(available_models[:15])}")
    except Exception as e:
        logger.warning(f"Could not list available models: {e}")


def _ensure_session_exists(session_id: str, model: str) -> None:
    """Ensure session exists, create if it doesn't."""
    if not get_session(session_id):
        logger.info(f"Session {session_id} does not exist, creating it with model {model}")
        create_session(session_id, model)


def _handle_gemma_model_stream(
    genai_model: genai.GenerativeModel,
    history: list,
    user_message: str
) -> Iterator[str]:
    """
    Handle streaming for Gemma models using direct generation.
    
    Args:
        genai_model: The initialized Gemma model
        history: Conversation history
        user_message: Current user message
    
    Yields:
        Response chunks
    """
    prompt = prepare_for_direct_generation(history, user_message)
    logger.info("Using streaming direct generation for Gemma model")
    
    response = genai_model.generate_content(prompt, stream=True)
    for chunk in response:
        try:
            chunk_text = chunk.text
            if chunk_text:
                yield chunk_text
        except (ValueError, AttributeError):
            # Skip chunks without text (finish markers, etc.)
            continue


def _handle_google_model_stream(
    actual_model_name: str,
    history: list,
    user_message: str
) -> Iterator[str]:
    """
    Handle streaming for Google models using LangChain agent.
    
    Args:
        actual_model_name: The actual API model name
        history: Conversation history
        user_message: Current user message
    
    Yields:
        Response chunks
    """
    logger.info(f"Using LangChain ReAct agent for model: {actual_model_name}")
    
    # Create ReAct agent
    agent = create_react_agent(actual_model_name)
    
    # Stream agent response
    yield from stream_agent_response(agent, user_message, history)


def chat_with_model_stream(session_id: str, user_message: str, model: str) -> Iterator[str]:
    """
    Stream chat response from the model.
    
    Args:
        session_id: The session ID
        user_message: The new user message
        model: The model name to use
    
    Yields:
        Chunks of the assistant's response
    """
    # Ensure session exists
    _ensure_session_exists(session_id, model)
    
    # Get conversation history
    history = get_messages(session_id)
    logger.info(f"Retrieved {len(history)} messages for session {session_id}")
    
    # Save user message
    save_message(session_id, "user", user_message)
    
    # Get the actual model name from mapping
    actual_model_name = model_manager.get_actual_model_name(model)
    logger.info(f"Using model: {actual_model_name} (requested: {model})")
    
    full_answer = ""
    
    try:
        # Determine if it's a Gemma model
        is_gemma_model = "gemma" in actual_model_name.lower()
        
        if is_gemma_model:
            # Gemma models use prompt-based tool calling (not LangChain)
            genai_model = model_manager.get_model(actual_model_name)
            for chunk in stream_gemma_with_tools(genai_model, user_message, history):
                full_answer += chunk
                yield chunk
        else:
            # Google models use LangChain ReAct agent
            for chunk in _handle_google_model_stream(actual_model_name, history, user_message):
                full_answer += chunk
                yield chunk
        
        # Save assistant response after streaming completes
        save_message(session_id, "assistant", full_answer)
        logger.info(
            f"Chat completed - Session: {session_id}, "
            f"Model: {actual_model_name} (requested: {model}), "
            f"Response length: {len(full_answer)}"
        )
    except Exception as e:
        logger.error(f"Error in chat_with_model_stream for session {session_id}: {e}", exc_info=True)
        raise
