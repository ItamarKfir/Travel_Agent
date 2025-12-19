"""
Test the chat system with tool calling integration.
"""
import os
import sys
import logging
import uuid
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat import chat_with_model_stream
from app.database import create_session, get_messages, db
from app.models import model_manager
import google.generativeai as genai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_chat_with_gemma_tools():
    """Test the chat system with Gemma models and tool calling."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return False
    
    genai.configure(api_key=api_key)
    model_manager.initialize()
    
    # Initialize database
    db.initialize()
    print(f"[OK] Database initialized\n")
    
    model_name = "gemma-3-27b"
    print(f"\n{'='*70}")
    print(f"Testing chat system with {model_name} and tool calling")
    print(f"{'='*70}\n")
    
    # Create a test session
    session_id = str(uuid.uuid4())
    create_session(session_id, model_name)
    print(f"[OK] Created test session: {session_id[:8]}...\n")
    
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
            # Collect streaming response
            full_response = ""
            tool_used = False
            
            for chunk in chat_with_model_stream(session_id, user_message, model_name):
                full_response += chunk
                # Check if tool was used
                if "[Using calculate tool:" in chunk:
                    tool_used = True
                    print(f"  → Tool usage detected in stream!")
            
            print(f"\n[OK] Full response: {full_response[:200]}...")
            print(f"[OK] Tool used: {tool_used}")
            
            # Verify response was saved
            messages = get_messages(session_id)
            if messages and messages[-1]['role'] == 'assistant':
                print(f"[OK] Response saved to database")
                passed += 1
            else:
                print(f"[FAIL] Response not saved to database")
                failed += 1
                
        except Exception as e:
            print(f"\n[FAIL] Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Chat Test Results: {passed} passed, {failed} failed")
    print(f"{'='*70}\n")
    
    return failed == 0


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CHAT SYSTEM WITH TOOLS TESTS")
    print("="*70)
    
    test_passed = test_chat_with_gemma_tools()
    
    print("\n" + "="*70)
    print("FINAL RESULT")
    print("="*70)
    print(f"{'[PASSED] ALL TESTS PASSED' if test_passed else '[FAILED] SOME TESTS FAILED'}")
    print("="*70 + "\n")

