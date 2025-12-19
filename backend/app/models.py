"""
Model manager and Pydantic models.
"""
import os
import logging
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, Dict

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = "You are a helpful assistant. Be concise and accurate. If unsure, say you are unsure."

# Models that don't support system_instruction
MODELS_WITHOUT_SYSTEM_INSTRUCTION = ["gemma-3-27b-it", "gemma-3-1b-it", "gemma-3-4b-it", "gemma-3-12b-it"]

# Model name mapping: user-friendly names to actual API model names
MODEL_MAPPING = {
    "gemma-3-27b": "gemma-3-27b-it",
    "gemini-2.5-flash-lite": "gemini-2.0-flash-lite",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemma-3-12b": "gemma-3-12b-it"
}

ALLOWED_MODELS = [
    "gemma-3-27b",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemma-3-12b"
]


class ModelManager:
    """Manages initialized model instances for lazy loading."""
    
    def __init__(self):
        self.models: Dict[str, genai.GenerativeModel] = {}
        self._initialized = False
    
    def initialize(self, api_key: Optional[str] = None):
        """Initialize the Google Generative AI client."""
        if self._initialized:
            return
        
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        logger.info("Google Generative AI initialized")
        self._initialized = True
    
    def get_actual_model_name(self, user_model: str) -> str:
        """Get the actual API model name from user-friendly name."""
        return MODEL_MAPPING.get(user_model, user_model)
    
    def get_model(self, model_name: str) -> genai.GenerativeModel:
        """
        Get or create a model instance (lazy loading).
        
        Args:
            model_name: The model name to get
        
        Returns:
            Initialized GenerativeModel instance
        """
        # Ensure genai is initialized
        if not self._initialized:
            self.initialize()
        
        # Return cached model if available
        if model_name in self.models:
            return self.models[model_name]
        
        # Create new model instance
        use_system_instruction = model_name not in MODELS_WITHOUT_SYSTEM_INSTRUCTION
        
        if use_system_instruction:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_INSTRUCTION
            )
            logger.info(f"Initialized model: {model_name} with system instruction")
        else:
            model = genai.GenerativeModel(model_name=model_name)
            logger.info(f"Initialized model: {model_name} without system instruction")
        
        # Cache the model
        self.models[model_name] = model
        return model


# Global model manager instance
model_manager = ModelManager()


# Pydantic models for API
class SessionCreate(BaseModel):
    model: Optional[str] = Field(default="gemma-3-27b")

class SessionResponse(BaseModel):
    session_id: str
    model: str

class SessionDetail(BaseModel):
    session_id: str
    model: str
    created_at: str

class Message(BaseModel):
    role: str
    content: str
    created_at: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str

class ChatResponse(BaseModel):
    session_id: str
    model: str
    answer: str
