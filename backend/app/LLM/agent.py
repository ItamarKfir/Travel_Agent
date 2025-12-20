"""
LangChain React Agent for Travel Agent application.

This module provides a ReAct agent with tool support
and customizable model initialization.
"""
import os
import logging
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage
from .prompts import DEFAULT_SYSTEM_PROMPT, REACT_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash-lite"


class ReactAgent:
    """LangChain ReAct Agent with tool support."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the ReAct agent.
        
        Args:
            model: Model name (defaults to gemini-2.0-flash-lite)
            tools: List of tools to use (optional)
            system_prompt: System prompt for the agent (optional)
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.model_name = model or DEFAULT_MODEL
        self.tools = tools or []
        # Use prompt from prompts.py if not provided, otherwise use provided
        self.system_prompt = system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Initialize model and agent
        self._initialize_model()
        self._initialize_agent()
        
        logger.info(f"ReAct agent initialized with model: {self.model_name}")
    
    def _initialize_model(self):
        """Initialize the language model."""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.7
            )
            logger.debug(f"Model {self.model_name} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise
    
    def _initialize_agent(self):
        """Initialize the ReAct agent executor."""
        if not self.tools:
            # No tools - create simple agent without tools
            logger.debug("Initializing agent without tools")
            self.agent_executor = None
            return
        
        try:
            # Create ReAct prompt template (this is the reasoning format structure)
            # Try LangChain hub first, fallback to custom template
            try:
                prompt = hub.pull("hwchase17/react")
                logger.debug("Using ReAct prompt from LangChain hub")
            except Exception:
                prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)
                logger.debug("Using custom ReAct prompt template")
            
            # create_react_agent: Creates the agent's logic/runnable (the "brain")
            # This defines HOW the agent reasons (ReAct pattern: Thought -> Action -> Observation)
            # NOT a separate agent - it's the reasoning chain
            agent_runnable = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # AgentExecutor: Wraps the agent runnable and executes it
            # This is the "executor" that runs the agent logic and handles tool calls
            # Together: agent_runnable (logic) + AgentExecutor (execution) = One complete agent
            self.agent_executor = AgentExecutor(
                agent=agent_runnable,  # Pass the agent logic from create_react_agent
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            logger.debug(f"ReAct agent initialized with {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def set_model(self, model: str):
        """
        Change the model used by the agent.
        
        Args:
            model: New model name
        """
        self.model_name = model
        self._initialize_model()
        if self.tools:
            self._initialize_agent()
        logger.info(f"Model changed to: {model}")
    
    def set_system_prompt(self, prompt: str):
        """
        Set the system prompt for the agent.
        
        Args:
            prompt: System prompt text
        """
        self.system_prompt = prompt
        logger.debug("System prompt updated")
    
    def add_tools(self, tools: List[BaseTool]):
        """
        Add tools to the agent.
        
        Args:
            tools: List of tools to add
        """
        self.tools.extend(tools)
        if self.agent_executor:
            self._initialize_agent()
        logger.info(f"Added {len(tools)} tools to agent")
    
    def run(self, input_text: str) -> str:
        """
        Run the agent with given input.
        
        Args:
            input_text: User input/question
        
        Returns:
            Agent response
        """
        try:
            if not self.agent_executor:
                # No tools - direct LLM call
                if self.system_prompt:
                    messages = [
                        HumanMessage(content=f"{self.system_prompt}\n\n{input_text}")
                    ]
                else:
                    messages = [HumanMessage(content=input_text)]
                
                response = self.llm.invoke(messages)
                result = response.content
            else:
                # Use agent with tools
                # Prepare input with system prompt if available
                if self.system_prompt:
                    full_input = f"{self.system_prompt}\n\n{input_text}"
                else:
                    full_input = input_text
                
                result = self.agent_executor.invoke({
                    "input": full_input
                })
                result = result.get("output", "")
            
            logger.debug(f"Agent response generated (length: {len(result)})")
            return result
            
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            raise
    
    def stream(self, input_text: str):
        """
        Stream agent response.
        
        Args:
            input_text: User input/question
        
        Yields:
            Response chunks
        """
        try:
            if not self.agent_executor:
                # No tools - stream LLM directly
                if self.system_prompt:
                    messages = [
                        HumanMessage(content=f"{self.system_prompt}\n\n{input_text}")
                    ]
                else:
                    messages = [HumanMessage(content=input_text)]
                
                full_response = ""
                for chunk in self.llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                        yield chunk.content
            else:
                # Agent with tools - run normally (streaming with tools is complex)
                result = self.run(input_text)
                yield result
            
        except Exception as e:
            logger.error(f"Error streaming agent response: {e}", exc_info=True)
            raise


# Global agent instance (singleton)
_agent_instance: Optional[ReactAgent] = None


def get_agent(
    model: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    force_new: bool = False
) -> ReactAgent:
    """
    Get or create the global agent instance.
    
    Args:
        model: Model name (only used if creating new instance)
        tools: Tools to use (only used if creating new instance)
        system_prompt: System prompt (only used if creating new instance)
        api_key: Google API key (only used if creating new instance)
        force_new: If True, create a new instance instead of reusing
    
    Returns:
        ReactAgent instance
    """
    global _agent_instance
    
    if _agent_instance is None or force_new:
        _agent_instance = ReactAgent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            api_key=api_key
        )
        logger.info("Created new agent instance")
    
    return _agent_instance


def initialize_agent(
    model: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None
) -> ReactAgent:
    """
    Initialize the agent (convenience function that creates new instance).
    
    Args:
        model: Model name
        tools: Tools to use
        system_prompt: System prompt
        api_key: Google API key
    
    Returns:
        ReactAgent instance
    """
    return get_agent(model=model, tools=tools, system_prompt=system_prompt, api_key=api_key, force_new=True)

