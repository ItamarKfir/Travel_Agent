"""
Tests for LangChain React Agent.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import app
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from dotenv import load_dotenv
from langchain_core.tools import tool
from app.LLM import (
    ReactAgent,
    get_agent,
    initialize_agent,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    TRAVEL_AGENT_SYSTEM_PROMPT
)

# Load environment variables
load_dotenv()


# Define a simple test tool
@tool
def calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression. Input should be a string like '2+2'."""
    try:
        result = eval(expression)
        return f"The result is {result}"
    except Exception as e:
        return f"Error calculating: {e}"


class TestReactAgent:
    """Test suite for ReactAgent."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set")
        return api_key
    
    def test_agent_initialization_without_tools(self, api_key):
        """Test agent initialization without tools."""
        agent = ReactAgent(
            model=DEFAULT_MODEL,
            tools=None,
            api_key=api_key
        )
        assert agent is not None
        assert agent.model_name == DEFAULT_MODEL
        assert len(agent.tools) == 0
        assert agent.agent_executor is None
    
    def test_agent_initialization_with_tools(self, api_key):
        """Test agent initialization with tools."""
        tools = [calculator]
        agent = ReactAgent(
            model=DEFAULT_MODEL,
            tools=tools,
            api_key=api_key
        )
        assert agent is not None
        assert len(agent.tools) == 1
        assert agent.agent_executor is not None
    
    def test_set_model(self, api_key):
        """Test changing the model."""
        agent = ReactAgent(api_key=api_key)
        original_model = agent.model_name
        
        agent.set_model("gemini-2.0-flash-lite")
        assert agent.model_name == "gemini-2.0-flash-lite"
        assert agent.model_name != original_model
    
    def test_set_system_prompt(self, api_key):
        """Test setting system prompt."""
        agent = ReactAgent(api_key=api_key)
        
        custom_prompt = "You are a helpful assistant."
        agent.set_system_prompt(custom_prompt)
        assert agent.system_prompt == custom_prompt
    
    def test_add_tools(self, api_key):
        """Test adding tools to agent."""
        agent = ReactAgent(api_key=api_key)
        assert len(agent.tools) == 0
        
        agent.add_tools([calculator])
        assert len(agent.tools) == 1
    
    def test_run_without_tools(self, api_key):
        """Test running agent without tools."""
        agent = ReactAgent(api_key=api_key)
        
        response = agent.run("What is 2+2?")
        assert response is not None
        assert len(response) > 0
    
    def test_run_with_tools(self, api_key):
        """Test running agent with tools."""
        tools = [calculator]
        agent = ReactAgent(
            model=DEFAULT_MODEL,
            tools=tools,
            api_key=api_key
        )
        
        response = agent.run("Calculate 5 + 3")
        assert response is not None
        assert len(response) > 0
    
    def test_get_agent_singleton(self, api_key):
        """Test get_agent singleton pattern."""
        agent1 = get_agent(api_key=api_key)
        agent2 = get_agent()
        
        assert agent1 is agent2  # Should be the same instance
    
    def test_initialize_agent_new_instance(self, api_key):
        """Test initialize_agent creates new instance."""
        agent1 = get_agent(api_key=api_key)
        agent2 = initialize_agent(api_key=api_key)
        
        assert agent1 is not agent2  # Should be different instances


if __name__ == "__main__":
    # Run basic integration test
    import sys
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set in environment")
        sys.exit(1)
    
    print("Testing LangChain React Agent...")
    print("-" * 70)
    
    try:
        # Test 1: Agent without tools
        print("\n1. Testing agent without tools...")
        agent = ReactAgent(api_key=api_key)
        response = agent.run("What is the capital of France?")
        print(f"   [OK] Response: {response[:100]}...")
        
        # Test 2: Agent with tools
        print("\n2. Testing agent with calculator tool...")
        tools = [calculator]
        agent_with_tools = ReactAgent(
            model=DEFAULT_MODEL,
            tools=tools,
            api_key=api_key
        )
        response = agent_with_tools.run("Calculate 10 * 5")
        print(f"   [OK] Response: {response[:200]}...")
        
        # Test 3: System prompt
        print("\n3. Testing agent with custom system prompt...")
        agent_prompt = ReactAgent(
            model=DEFAULT_MODEL,
            system_prompt=TRAVEL_AGENT_SYSTEM_PROMPT,
            api_key=api_key
        )
        response = agent_prompt.run("Hello, can you help me plan a trip?")
        print(f"   [OK] Response: {response[:200]}...")
        
        # Test 4: Singleton pattern
        print("\n5. Testing singleton pattern...")
        agent_single1 = get_agent(api_key=api_key)
        agent_single2 = get_agent()
        assert agent_single1 is agent_single2
        print("   [OK] Singleton pattern works correctly")
        
        print("\n" + "-" * 70)
        print("All tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

