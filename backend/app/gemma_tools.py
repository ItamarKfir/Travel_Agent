"""
Prompt-based tool calling for Gemma models (they don't support native function calling).
"""
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, List, Tuple, Optional, Iterator

from .tools import get_available_tools, get_tool_description, execute_tool_call

logger = logging.getLogger(__name__)


# System instructions for Gemma to use tools via JSON
GEMMA_TOOL_SYSTEM_INSTRUCTIONS = """You are a helpful assistant with access to tools.

Available tools:
{tools_description}

RULES:
- If you need a tool, respond with ONLY a JSON object:
  {{"tool_name": "<name>", "arguments": {{...}}}}
- If you do NOT need a tool, respond with ONLY:
  {{"final": "<your answer>"}}
- No extra keys. No markdown. No explanations outside JSON.
- Always respond in valid JSON format only."""


def _build_tool_descriptions() -> str:
    """Build tool descriptions for the prompt."""
    tools = get_available_tools()
    descriptions = []
    
    for tool_name in tools.keys():
        desc = get_tool_description(tool_name)
        descriptions.append(f"Tool: {tool_name}\nDescription: {desc}")
    
    return "\n\n".join(descriptions)


def _build_tool_prompt(user_text: str, conversation_history: List[Dict]) -> str:
    """Build a prompt for Gemma with tool instructions and history."""
    tools_desc = _build_tool_descriptions()
    system_instructions = GEMMA_TOOL_SYSTEM_INSTRUCTIONS.format(tools_description=tools_desc)
    
    history_str = ""
    for msg in conversation_history[-5:]:  # Last 5 messages for context
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            history_str += f"User: {content}\n"
        elif role == "assistant":
            history_str += f"Assistant: {content}\n"
    
    return f"{system_instructions}\n\n{history_str}User: {user_text}\nAssistant:"


def _parse_gemma_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse Gemma's JSON response, handling markdown code blocks if present.
    Returns the parsed JSON or None if parsing fails.
    """
    # Remove markdown code block if present
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove ```json
    if response_text.startswith("```"):
        response_text = response_text[3:]  # Remove ```
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove closing ```
    response_text = response_text.strip()
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from Gemma response: {e}")
        logger.debug(f"Response text: {response_text}")
        return None


def _handle_gemma_tool_call(
    model: genai.GenerativeModel,
    user_message: str,
    conversation_history: List[Dict]
) -> Tuple[str, bool]:
    """
    Handle prompt-based tool calling for Gemma models.
    Returns the final response text and a boolean indicating if a tool was used.
    """
    # First turn: ask model what to do
    prompt = _build_tool_prompt(user_message, conversation_history)
    
    # Use non-streaming for tool detection
    response = model.generate_content(prompt)
    raw_gemma_response = response.text.strip()
    
    logger.debug(f"Gemma raw response: {raw_gemma_response}")
    
    data = _parse_gemma_response(raw_gemma_response)
    
    if data is None:
        logger.warning("Gemma did not return valid JSON for tool calling. Falling back to direct response.")
        return raw_gemma_response, False
    
    # If model answered directly
    if "final" in data:
        return data["final"], False
    
    # If model requested a tool
    if "tool_name" in data:
        tool_name = data["tool_name"]
        args = data.get("arguments", {})
        
        logger.info(f"Gemma requested tool: {tool_name} with args: {args}")
        
        # Execute the tool using the execute_tool_call function
        # Note: execute_tool_call expects (function_name, args) -> result
        tool_result = execute_tool_call(tool_name, args)
        
        if not tool_result.get("success"):
            return f"Error: {tool_result.get('error', 'Tool execution failed')}", True
        
        # Second turn: give tool result back and ask for final answer
        tool_result_json = json.dumps(tool_result, ensure_ascii=False)
        followup_prompt = (
            f"{GEMMA_TOOL_SYSTEM_INSTRUCTIONS.format(tools_description=_build_tool_descriptions())}\n\n"
            f"User: {user_message}\n"
            f"Assistant: {raw_gemma_response}\n"
            f"Tool result ({tool_name}): {tool_result_json}\n"
            f"Assistant:"
        )
        
        followup_response = model.generate_content(followup_prompt)
        raw_final_gemma_response = followup_response.text.strip()
        logger.debug(f"Gemma followup response: {raw_final_gemma_response}")
        
        final_data = _parse_gemma_response(raw_final_gemma_response)
        
        if final_data and "final" in final_data:
            # Prepend tool usage message
            tool_message = f"[Using {tool_name} tool: {tool_result.get('message', '')}]\n\n"
            return tool_message + final_data["final"], True
        else:
            # Fallback to raw response if JSON parsing fails
            tool_message = f"[Using {tool_name} tool: {tool_result.get('message', '')}]\n\n"
            return tool_message + raw_final_gemma_response, True
    
    # Unknown format
    logger.warning(f"Unexpected JSON format from Gemma: {data}")
    return raw_gemma_response, False


def stream_gemma_with_tools(
    model: genai.GenerativeModel,
    user_message: str,
    conversation_history: List[Dict]
) -> Iterator[str]:
    """
    Stream Gemma response with prompt-based tool calling.
    
    Args:
        model: The Gemma model instance
        user_message: Current user message
        conversation_history: Conversation history
    
    Yields:
        Response chunks
    """
    try:
        # Try tool calling first
        response_text, tool_used = _handle_gemma_tool_call(
            model=model,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        if tool_used:
            # Tool was used, yield the response in chunks (simulate streaming)
            tool_message = ""
            if "[Using" in response_text:
                # Extract tool message if present
                parts = response_text.split("\n\n", 1)
                if len(parts) > 1:
                    tool_message = parts[0] + "\n\n"
                    response_text = parts[1]
            
            # Yield tool message if present
            if tool_message:
                yield tool_message
            
            # Yield the final response in chunks (simulate streaming)
            chunk_size = 10
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield chunk
            
            logger.info("Tool calling used for Gemma model")
        else:
            # No tool used, use regular streaming generation
            from .memory import prepare_for_direct_generation
            prompt = prepare_for_direct_generation(conversation_history, user_message)
            logger.info("Using streaming direct generation for Gemma model (no tool needed)")
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                try:
                    chunk_text = chunk.text
                    if chunk_text:
                        yield chunk_text
                except (ValueError, AttributeError):
                    continue
    except Exception as e:
        # Fallback to regular generation if tool calling fails
        logger.warning(f"Tool calling failed, falling back to regular generation: {e}")
        from .memory import prepare_for_direct_generation
        prompt = prepare_for_direct_generation(conversation_history, user_message)
        logger.info("Using streaming direct generation for Gemma model (fallback)")
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            try:
                chunk_text = chunk.text
                if chunk_text:
                    yield chunk_text
            except (ValueError, AttributeError):
                continue

