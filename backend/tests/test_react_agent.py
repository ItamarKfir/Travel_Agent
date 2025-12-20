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
from app.Tools import get_place_reviews_from_apis

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
    
    def test_agent_with_place_reviews_tool(self, api_key):
        """Test agent with place reviews tool."""
        # Check if API keys are available
        google_places_key = os.getenv("GOOGLE_PLACES_API_KEY")
        tripadvisor_key = os.getenv("TRIPADVISOR_API_KEY")
        
        if not google_places_key and not tripadvisor_key:
            pytest.skip("Neither GOOGLE_PLACES_API_KEY nor TRIPADVISOR_API_KEY is set")
        
        tools = [get_place_reviews_from_apis]
        agent = ReactAgent(
            model=DEFAULT_MODEL,
            tools=tools,
            system_prompt=TRAVEL_AGENT_SYSTEM_PROMPT,
            api_key=api_key
        )
        
        assert agent is not None
        assert len(agent.tools) == 1
        assert agent.agent_executor is not None
        
        # Test with a real query
        response = agent.run("Can you get reviews for Hilton hotel in Tel Aviv?")
        assert response is not None
        assert len(response) > 0


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
        print("\n5. Testing agent with place reviews tool (Hilton, Tel Aviv)...")
        google_places_key = os.getenv("GOOGLE_PLACES_API_KEY")
        tripadvisor_key = os.getenv("TRIPADVISOR_API_KEY")
        
        if not google_places_key and not tripadvisor_key:
            print("   [SKIP] Neither GOOGLE_PLACES_API_KEY nor TRIPADVISOR_API_KEY is set")
        else:
            from app.Tools import get_place_reviews_from_apis
            
            tools = [get_place_reviews_from_apis]
            agent_places = ReactAgent(
                model=DEFAULT_MODEL,
                tools=tools,
                system_prompt=TRAVEL_AGENT_SYSTEM_PROMPT,
                api_key=api_key
            )
            
            query = "Can you get reviews for Hilton hotel in Tel Aviv and summarize it for me ( 5 sentences max)?"
            print(f"   Query: {query}")
            response = agent_places.run(query)
            print(f"   Response length: {len(response)} characters")
            print(f"   Response:\n{response}")
            assert response is not None
            assert len(response) > 0
        
        print("\n" + "-" * 70)
        print("All tests passed!")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

