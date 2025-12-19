"""
Test script for Gemma prompt-based tool calling.
"""
import os
import sys
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gemma_tools import handle_gemma_tool_call, build_tool_prompt
from app.tools import execute_tool_call

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_gemma_calculator():
    """Test calculator tool with Gemma 3 27B-IT."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return
    
    genai.configure(api_key=api_key)
    
    # Initialize Gemma model
    model_name = "gemma-3-27b-it"
    print(f"\n{'='*60}")
    print(f"Testing {model_name} with calculator tool")
    print(f"{'='*60}\n")
    
    try:
        model = genai.GenerativeModel(model_name=model_name)
        print(f"✓ Model {model_name} initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize model: {e}")
        return
    
    # Test cases
    test_cases = [
        "how much is 2+2?",
        "what is 10 * 5?",
        "calculate 15 + 23",
        "what's 100 divided by 4?",
    ]
    
    for i, user_message in enumerate(test_cases, 1):
        print(f"\n{'─'*60}")
        print(f"Test {i}: {user_message}")
        print(f"{'─'*60}")
        
        try:
            response, tool_used = handle_gemma_tool_call(
                model=model,
                user_message=user_message,
                conversation_history=[],
                tool_executor=execute_tool_call
            )
            
            print(f"\n✓ Response: {response}")
            print(f"✓ Tool used: {tool_used}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_gemma_calculator()

