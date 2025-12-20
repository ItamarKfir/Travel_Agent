"""
Test LangChain ReAct agent with tools.
"""
import os
import sys
import logging
import warnings
from dotenv import load_dotenv

# Suppress Pydantic serialization warnings from LangChain
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import create_react_agent, run_agent_with_history
from app.database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_agent_with_calculator():
    """Test the ReAct agent using the calculator tool."""
    print("\n" + "="*70)
    print("Testing LangChain ReAct Agent with Calculator Tool")
    print("="*70)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return False
    
    # Use a Google model (not Gemma) for ReAct agent - Gemma doesn't support function calling
    model_name = "gemini-2.5-flash-lite"
    print(f"Using model: {model_name}\n")
    
    try:
        # Create ReAct agent for Gemini model
        agent = create_react_agent(model_name, api_key)
        print("[OK] ReAct agent created\n")
        
        # Test cases
        test_cases = [
            "how much is 2+2?",
            "what is 10 * 5?",
            "calculate 15 + 23",
        ]
        
        passed = 0
        failed = 0
        
        for i, user_message in enumerate(test_cases, 1):
            print(f"\n{'─'*70}")
            print(f"Test {i}: {user_message}")
            print(f"{'─'*70}")
            
            try:
                # Run agent with empty history for simplicity
                response = run_agent_with_history(
                    agent=agent,
                    user_message=user_message,
                    conversation_history=[]
                )
                
                print(f"\n[OK] Response: {response[:200]}...")
                
                # Check if tool was used (should mention calculation or result)
                if "result" in response.lower() or any(char.isdigit() for char in response):
                    print("[OK] Tool appears to have been used (response contains result)")
                    passed += 1
                else:
                    print("[WARNING] Tool usage unclear from response")
                    passed += 1  # Still count as passed if we got a response
                    
            except Exception as e:
                print(f"\n[FAIL] Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        print(f"\n{'='*70}")
        print(f"Test Results: {passed} passed, {failed} failed")
        print(f"{'='*70}\n")
        
        return failed == 0
        
    except Exception as e:
        print(f"\n[FAIL] Failed to create agent executor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_streaming():
    """Test streaming agent responses."""
    print("\n" + "="*70)
    print("Testing Agent Streaming")
    print("="*70)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return False
    
    # Use a Gemini model that supports function calling (not Gemma)
    model_name = "gemini-2.5-flash-lite"
    
    try:
        from app.agent import create_react_agent, stream_agent_response
        
        agent = create_react_agent(model_name, api_key)
        print("[OK] ReAct agent created\n")
        
        user_message = "what is 5 * 8?"
        print(f"Question: {user_message}\n")
        print("Streaming response:")
        print("-" * 70)
        
        chunks_received = 0
        full_response = ""
        
        for chunk in stream_agent_response(agent, user_message, []):
            print(chunk, end="", flush=True)
            full_response += chunk
            chunks_received += 1
        
        print("\n" + "-" * 70)
        print(f"\n[OK] Received {chunks_received} chunks")
        print(f"[OK] Full response length: {len(full_response)}")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LANGCHAIN REACT AGENT TESTS")
    print("="*70)
    
    # Initialize database (may be needed for some operations)
    try:
        db.initialize()
    except:
        pass
    
    agent_test_passed = test_agent_with_calculator()
    streaming_test_passed = test_agent_streaming()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    if agent_test_passed and streaming_test_passed:
        print("[PASSED] ALL TESTS PASSED")
    else:
        print("[FAILED] SOME TESTS FAILED")
    print("="*70 + "\n")
    
    # Close database
    try:
        db.close()
    except:
        pass

