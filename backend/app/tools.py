"""
Tools/functions that the LLM can use.
"""
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def calculate(expression: str) -> Dict[str, Any]:
    """
    Calculate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression as string (e.g., "2 + 2", "10 * 5")
    
    Returns:
        Dict with result or error
    """
    try:
        # Sanitize expression - only allow numbers, operators, and parentheses
        # Remove any potentially dangerous characters
        sanitized = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        # Evaluate safely
        result = eval(sanitized, {"__builtins__": {}}, {})
        
        logger.info(f"Calculator tool used: {expression} = {result}")
        return {
            "success": True,
            "expression": expression,
            "result": result,
            "message": f"Calculated: {expression} = {result}"
        }
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return {
            "success": False,
            "expression": expression,
            "error": str(e),
            "message": f"Error calculating {expression}: {str(e)}"
        }


def get_calculator_tool() -> Dict[str, Any]:
    """Get the calculator tool definition for Gemini function calling."""
    return {
        "function_declarations": [
            {
                "name": "calculate",
                "description": "Calculate a mathematical expression. Use this when the user asks for calculations, math problems, or arithmetic operations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to calculate (e.g., '2 + 2', '10 * 5', '(5 + 3) * 2')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ]
    }


def execute_tool_call(function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool/function call.
    
    Args:
        function_name: Name of the function to call
        args: Arguments for the function
    
    Returns:
        Result from the function
    """
    if function_name == "calculate":
        expression = args.get("expression", "")
        return calculate(expression)
    else:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}",
            "message": f"Unknown function: {function_name}"
        }

