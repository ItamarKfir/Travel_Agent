"""
LangChain agent for Google models with tool support (LangChain 1.x API).
"""
import os
import logging
import warnings
from typing import List, Dict, Iterator, Optional

# Suppress Pydantic serialization warnings from LangChain
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from .tools import get_available_tools, get_tool_description

logger = logging.getLogger(__name__)


def _convert_history_to_langchain(messages: List[Dict]) -> List:
    """
    Convert database message format to LangChain message format.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
    
    Returns:
        List of LangChain message objects
    """
    langchain_messages = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
    
    return langchain_messages


def _create_tools_for_langchain() -> List[Tool]:
    """
    Create LangChain Tool objects from available tools.
    
    Returns:
        List of LangChain Tool objects
    """
    tools_dict = get_available_tools()
    langchain_tools = []
    
    for tool_name, tool_func in tools_dict.items():
        tool = Tool(
            name=tool_name,
            func=tool_func,
            description=get_tool_description(tool_name)
        )
        langchain_tools.append(tool)
    
    return langchain_tools


def create_react_agent(model_name: str, api_key: Optional[str] = None):
    """
    Create a ReAct agent for a Google model.
    
    In LangChain 1.x, create_agent() returns a graph (StateGraph) that implements
    the ReAct pattern: Reason → Act (use tool) → Observe → repeat until done.
    
    The "graph" is just the execution engine - it's still a ReAct agent internally.
    
    Args:
        model_name: The model name to use (e.g., "gemini-2.5-flash-lite")
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        Compiled ReAct agent (as a StateGraph for execution)
    """
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    # Create LLM
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.7,
    )
    
    # Create tools
    tools = _create_tools_for_langchain()
    
    # Create ReAct agent (returns a graph, but it's a ReAct agent)
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a helpful assistant with access to tools. When you need to perform calculations, use the calculate tool.",
    )
    
    logger.info(f"Created ReAct agent for model: {model_name}")
    return agent


def run_agent_with_history(
    agent,
    user_message: str,
    conversation_history: List[Dict]
) -> str:
    """
    Run the ReAct agent (simple - no history, just current message).
    
    Args:
        agent: The ReAct agent (StateGraph from create_react_agent)
        user_message: The current user message
        conversation_history: Ignored (for compatibility)
    
    Returns:
        The agent's response
    """
    # Simple - just use the user message, no history
    langchain_messages = [HumanMessage(content=user_message)]
    
    # Run agent
    try:
        result = agent.invoke({"messages": langchain_messages})
        
        # Extract the last AI message
        messages = result.get("messages", [])
        if messages:
            # Find the last AI message (skip tool messages)
            for msg in reversed(messages):
                if hasattr(msg, "type") and msg.type == "ai":
                    content = msg.content
                    # Handle different content types
                    if isinstance(content, str):
                        response = content
                    elif isinstance(content, list):
                        # Join list of strings
                        response = "".join(str(part) for part in content)
                    else:
                        response = str(content)
                    
                    logger.info(f"Agent response generated (length: {len(response)})")
                    return response
            
            # Fallback: get last message regardless of type
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                content = last_message.content
                if isinstance(content, str):
                    response = content
                elif isinstance(content, list):
                    response = "".join(str(part) for part in content)
                else:
                    response = str(content)
            else:
                response = str(last_message)
        else:
            response = "No response generated"
        
        logger.info(f"Agent response generated (length: {len(response)})")
        return response
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        raise


def stream_agent_response(
    agent,
    user_message: str,
    conversation_history: List[Dict]
) -> Iterator[str]:
    """
    Stream ReAct agent response chunks (simple - no history, just current message).
    
    Args:
        agent: The ReAct agent (StateGraph from create_react_agent)
        user_message: The current user message
        conversation_history: Ignored (for compatibility)
    
    Yields:
        Chunks of the agent's response
    """
    # Simple - just use the user message, no history
    langchain_messages = [HumanMessage(content=user_message)]
    
    # Stream agent response
    try:
        # Use stream_mode="values" to get state updates
        last_content = ""
        chunks_yielded = 0
        
        for chunk in agent.stream({"messages": langchain_messages}, stream_mode="values"):
            # chunk is a dict with "messages" key
            if isinstance(chunk, dict) and "messages" in chunk:
                messages = chunk["messages"]
                if messages:
                    # Get the last message (most recent)
                    last_message = messages[-1]
                    
                    # Skip non-AI messages (tool messages, etc.)
                    if hasattr(last_message, "type") and last_message.type != "ai":
                        continue
                    
                    # Extract content
                    content = None
                    if hasattr(last_message, "content"):
                        content = last_message.content
                    elif hasattr(last_message, "text"):
                        content = last_message.text
                    
                    if content:
                        # Handle different content types
                        text_content = None
                        if isinstance(content, str):
                            text_content = content
                        elif isinstance(content, list):
                            # Content might be a list of parts
                            text_parts = []
                            for part in content:
                                if isinstance(part, str):
                                    text_parts.append(part)
                                elif hasattr(part, "text"):
                                    text_parts.append(str(part.text))
                                else:
                                    text_parts.append(str(part))
                            text_content = "".join(text_parts)
                        
                        if text_content:
                            # Only yield new content (incremental)
                            if len(text_content) > len(last_content):
                                new_content = text_content[len(last_content):]
                                last_content = text_content
                                yield new_content
                                chunks_yielded += 1
        
        # If no chunks were yielded, fall back to non-streaming
        if chunks_yielded == 0:
            logger.warning("No chunks yielded from streaming, falling back to non-streaming")
            raise Exception("No chunks yielded")
            
    except Exception as e:
        logger.debug(f"Streaming failed or no chunks: {e}, falling back to non-streaming")
        # Fallback to non-streaming - get final result and yield it
        try:
            result = agent.invoke({"messages": langchain_messages})
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = None
                
                # Try to extract content
                if hasattr(last_message, "content"):
                    content = last_message.content
                    if isinstance(content, str):
                        response = content
                    elif isinstance(content, list):
                        # Join list of strings
                        response = "".join(str(part) for part in content)
                    else:
                        response = str(content)
                elif hasattr(last_message, "text"):
                    response = last_message.text
                else:
                    response = str(last_message)
            else:
                response = "No response generated"
            
            # Yield response in chunks for streaming effect (word by word for better UX)
            if response:
                words = response.split()
                for word in words:
                    yield word + " "
        except Exception as e2:
            logger.error(f"Error in fallback: {e2}", exc_info=True)
            yield f"Error: {str(e2)}"
