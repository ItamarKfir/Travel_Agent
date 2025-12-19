"""
Prompt-based tool calling for Gemma models using JSON-only output pattern.
"""
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Tool definitions for Gemma models
TOOLS_DEFINITION = {
    "calculate": {
        "description": "Calculate a mathematical expression. Use this when the user asks for calculations, math problems, or arithmetic operations.",
        "arguments": {
            "expression": "string - The mathematical expression to calculate (e.g., '2 + 2', '10 * 5', '(5 + 3) * 2')"
        }
    }
}

SYSTEM_INSTRUCTIONS = """You are a helpful assistant.

You have access to these tools:

Tool: calculate
Description: Calculate a mathematical expression. Use this when the user asks for calculations, math problems, or arithmetic operations.
JSON Schema:
{
  "name": "calculate",
  "arguments": {
    "expression": "string - The mathematical expression to calculate (e.g., '2 + 2', '10 * 5')"
  }
}

RULES:
- If you need a tool, respond with ONLY a JSON object:
  {"tool_name": "calculate", "arguments": {"expression": "..."}}
- If you do NOT need a tool, respond with ONLY:
  {"final": "<your answer>"}
- No extra keys. No markdown. No explanations outside JSON.
- Always respond in valid JSON format only.
"""


def build_tool_prompt(user_text: str, conversation_history: list = None) -> str:
    """Build a prompt for Gemma with tool definitions."""
    prompt = SYSTEM_INSTRUCTIONS
    
    # Add conversation history if provided
    if conversation_history:
        prompt += "\n\nConversation history:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
    
    prompt += f"\n\nUser: {user_text}\nAssistant:"
    return prompt


def parse_gemma_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parse Gemma's JSON response, handling markdown code blocks if present."""
    # Remove markdown code blocks if present
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


def handle_gemma_tool_call(
    model: genai.GenerativeModel,
    user_message: str,
    conversation_history: list,
    tool_executor: callable
) -> Tuple[str, bool]:
    """
    Handle tool calling with Gemma model using prompt-based approach.
    
    Args:
        model: The Gemma model instance
        user_message: The user's message
        conversation_history: List of previous messages
        tool_executor: Function to execute tools (function_name, args) -> result
    
    Returns:
        Tuple of (response_text, tool_was_used)
    """
    # First turn: ask model what to do
    prompt = build_tool_prompt(user_message, conversation_history)
    
    try:
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        logger.debug(f"Gemma raw response: {raw_response}")
        
        data = parse_gemma_response(raw_response)
        
        if not data:
            # If we can't parse JSON, return the raw response
            logger.warning("Could not parse JSON from Gemma, returning raw response")
            return raw_response, False
        
        # If model answered directly
        if "final" in data:
            return data["final"], False
        
        # If model requested a tool
        if "tool_name" in data:
            tool_name = data["tool_name"]
            args = data.get("arguments", {})
            
            logger.info(f"Gemma requested tool: {tool_name} with args: {args}")
            
            # Execute the tool
            tool_result = tool_executor(tool_name, args)
            
            if not tool_result.get("success"):
                return f"Error: {tool_result.get('error', 'Tool execution failed')}", True
            
            # Second turn: give tool result back and ask for final answer
            tool_result_json = json.dumps(tool_result, ensure_ascii=False)
            followup_prompt = (
                f"{SYSTEM_INSTRUCTIONS}\n\n"
                f"User: {user_message}\n"
                f"Assistant: {raw_response}\n"
                f"Tool result ({tool_name}): {tool_result_json}\n"
                f"Assistant:"
            )
            
            followup_response = model.generate_content(followup_prompt)
            raw_response2 = followup_response.text.strip()
            logger.debug(f"Gemma followup response: {raw_response2}")
            
            data2 = parse_gemma_response(raw_response2)
            
            if data2 and "final" in data2:
                # Include tool usage message
                tool_message = f"[Using {tool_name} tool: {tool_result.get('message', '')}]\n\n"
                return tool_message + data2["final"], True
            else:
                # Fallback to raw response if JSON parsing fails
                tool_message = f"[Using {tool_name} tool: {tool_result.get('message', '')}]\n\n"
                return tool_message + raw_response2, True
        
        # Unknown format
        logger.warning(f"Unexpected JSON format from Gemma: {data}")
        return raw_response, False
        
    except Exception as e:
        logger.error(f"Error in Gemma tool calling: {e}", exc_info=True)
        raise

