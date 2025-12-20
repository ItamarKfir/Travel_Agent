"""
Model manager and Pydantic models.
"""
import os
import logging
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Model name mapping: user-friendly names to actual API model names
MODEL_MAPPING = {
    "gemini-2.5-flash-lite": "gemini-2.0-flash-lite",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",
    "gemini-2.5-flash": "gemini-2.5-flash",
}

ALLOWED_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]

# Pydantic models for API
class SessionCreate(BaseModel):
    model: Optional[str] = Field(default="gemini-2.5-flash-lite")

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
