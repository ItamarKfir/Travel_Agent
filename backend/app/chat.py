import logging
import google.generativeai as genai
from Memory.database import get_messages, save_message, get_session, create_session
from Memory.memory import prepare_for_chat, prepare_for_direct_generation
from .models import model_manager

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

def chat_with_model_stream(session_id: str, user_message: str, model: str):
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
    if not get_session(session_id):
        logger.info(f"Session {session_id} does not exist, creating it with model {model}")
        create_session(session_id, model)
    
    # Get conversation history
    history = get_messages(session_id)
    logger.info(f"Retrieved {len(history)} messages for session {session_id}")
    
    # Save user message
    save_message(session_id, "user", user_message)
    
    # Get the actual model name from mapping and get model (lazy initialization)
    actual_model_name = model_manager.get_actual_model_name(model)
    logger.info(f"Using model: {actual_model_name} (requested: {model})")
    
    # Get model from manager (initializes on first use, then reuses cached instance)
    genai_model = model_manager.get_model(actual_model_name)
    
    # Determine if we should use chat or direct generation
    is_gemma_model = "gemma" in actual_model_name.lower()
    full_answer = ""
    
    try:
        if is_gemma_model:
            # Gemma models use direct generation with prompt (streaming)
            prompt = prepare_for_direct_generation(history, user_message)
            logger.info(f"Using streaming direct generation for {actual_model_name}")
            response = genai_model.generate_content(prompt, stream=True)
            for chunk in response:
                try:
                    # Safely get text from chunk - access text property in try block
                    chunk_text = chunk.text
                    if chunk_text:
                        full_answer += chunk_text
                        yield chunk_text
                except (ValueError, AttributeError):
                    # Skip chunks without text (finish markers, etc.)
                    # This happens when chunk has finish_reason but no text content
                    continue
        else:
            # Other models use chat API (streaming)
            chat_history, _ = prepare_for_chat(history, user_message)
            chat = genai_model.start_chat(history=chat_history[:-1])
            logger.info(f"Using streaming chat API for {actual_model_name}")
            response = chat.send_message(user_message, stream=True)
            for chunk in response:
                try:
                    # Safely get text from chunk - access text property in try block
                    chunk_text = chunk.text
                    if chunk_text:
                        full_answer += chunk_text
                        yield chunk_text
                except (ValueError, AttributeError):
                    # Skip chunks without text (finish markers, etc.)
                    # This happens when chunk has finish_reason but no text content
                    continue
        
        # Save assistant response after streaming completes
        save_message(session_id, "assistant", full_answer)
        logger.info(
            f"Chat completed - Session: {session_id}, "
            f"Model used: {actual_model_name} (requested: {model}), "
            f"Response length: {len(full_answer)}"
        )
    except Exception as e:
        logger.error(f"Error in chat_with_model_stream for session {session_id}: {e}", exc_info=True)
        raise

def chat_with_model(session_id: str, user_message: str, model: str) -> str:
    """
    Chat with the model using conversation history.
    
    Args:
        session_id: The session ID
        user_message: The new user message
        model: The model name to use
    
    Returns:
        The assistant's response
    """
    # Ensure session exists
    if not get_session(session_id):
        logger.info(f"Session {session_id} does not exist, creating it with model {model}")
        create_session(session_id, model)
    
    # Get conversation history
    history = get_messages(session_id)
    logger.info(f"Retrieved {len(history)} messages for session {session_id}")
    
    # Save user message
    save_message(session_id, "user", user_message)
    
    try:
        # Get the actual model name from mapping
        actual_model_name = model_manager.get_actual_model_name(model)
        logger.info(f"Using model: {actual_model_name} (requested: {model})")
        
        # Get model from manager (reuses cached instance)
        genai_model = model_manager.get_model(actual_model_name)
        
        # Determine if we should use chat or direct generation
        is_gemma_model = "gemma" in actual_model_name.lower()
        
        if is_gemma_model:
            # Gemma models use direct generation with prompt (streaming)
            prompt = prepare_for_direct_generation(history, user_message)
            logger.info(f"Using streaming direct generation for {actual_model_name}")
            response = genai_model.generate_content(prompt, stream=True)
            answer = ""
            for chunk in response:
                if chunk.text:
                    answer += chunk.text
        else:
            # Other models use chat API (streaming)
            chat_history, _ = prepare_for_chat(history, user_message)
            chat = genai_model.start_chat(history=chat_history[:-1])
            logger.info(f"Using streaming chat API for {actual_model_name}")
            response = chat.send_message(user_message, stream=True)
            answer = ""
            for chunk in response:
                if chunk.text:
                    answer += chunk.text
        
        # Save assistant response
        save_message(session_id, "assistant", answer)
        
        request_length = len(user_message)
        response_length = len(answer)
        logger.info(
            f"Chat completed - Session: {session_id}, "
            f"Model used: {actual_model_name} (requested: {model}), "
            f"Request length: {request_length}, Response length: {response_length}"
        )
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in chat_with_model for session {session_id}: {e}", exc_info=True)
        raise

