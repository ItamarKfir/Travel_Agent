"""
Tools/functions that the LLM can use via LangChain agents.
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate(expression: str) -> str:
    """
    Calculate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression as string (e.g., "2 + 2", "10 * 5")
    
    Returns:
        String result of the calculation
    """
    try:
        # Sanitize expression - only allow numbers, operators, and parentheses
        sanitized = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        # Evaluate safely
        result = eval(sanitized, {"__builtins__": {}}, {})
        
        logger.info(f"Calculator tool used: {expression} = {result}")
        return f"Result: {result}"
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return f"Error: {str(e)}"


def get_available_tools() -> Dict[str, Any]:
    """
    Get dictionary of available tools for LangChain.
    
    Returns:
        Dictionary mapping tool names to functions
    """
    return {
        "calculate": calculate
    }


def get_tool_description(tool_name: str) -> str:
    """
    Get description for a specific tool.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Description string
    """
    descriptions = {
        "calculate": "Calculate a mathematical expression. Input should be a string with the expression (e.g., '2 + 2', '10 * 5', '(5 + 3) * 2'). Returns the result as a string."
    }
    return descriptions.get(tool_name, "No description available")


def get_tool_descriptions() -> str:
    """
    Get human-readable descriptions of all available tools.
    
    Returns:
        String description of tools
    """
    return """
Available tools:
- calculate(expression: str): Calculate a mathematical expression. 
  Example: calculate("2 + 2") returns "Result: 4"
"""


def execute_tool_call(function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool/function call.
    
    Args:
        function_name: Name of the function to call
        args: Arguments for the function
    
    Returns:
        Result dict with success, result/error, and message
    """
    tools = get_available_tools()
    
    if function_name not in tools:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}",
            "message": f"Unknown function: {function_name}"
        }
    
    try:
        # Call the tool function
        tool_func = tools[function_name]
        result = tool_func(**args)
        
        return {
            "success": True,
            "result": result,
            "message": str(result)
        }
    except Exception as e:
        logger.error(f"Error executing tool {function_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Error executing {function_name}: {str(e)}"
        }

