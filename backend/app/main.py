import logging
import uuid
from fastapi import FastAPI, HTTPException, status  # type: ignore
from fastapi.responses import StreamingResponse  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from dotenv import load_dotenv  # type: ignore
from app.LLM.models import (
    SessionCreate, SessionResponse, SessionDetail, Message,
    ChatRequest, ChatResponse, ALLOWED_MODELS
)
from app.Memory.database import init_db, get_session, get_messages
from app.LLM import get_agent_manager, DEFAULT_MODEL, TRAVEL_AGENT_SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    load_dotenv()
except UnicodeDecodeError:
    # If .env file has wrong encoding, log warning but continue
    logger.warning("Could not load .env file due to encoding issue. Using environment variables only.")
except Exception as e:
    logger.warning(f"Could not load .env file: {e}. Using environment variables only.")

# Initialize FastAPI app
app = FastAPI(title="LLM Chat API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and agent manager on startup
@app.on_event("startup")
async def startup_event():
    init_db()  # Initialize database connection
    try:
        # Initialize agent manager with tools
        from app.Tools import get_place_reviews_from_apis
        tools = [get_place_reviews_from_apis]
        
        # Initialize the agent manager (will be cached as singleton)
        get_agent_manager(
            model=DEFAULT_MODEL,
            tools=tools,
            system_prompt=TRAVEL_AGENT_SYSTEM_PROMPT
        )
        logger.info("Agent manager initialized with tools")
    except Exception as e:
        logger.error(f"Failed to initialize agent manager: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    from app.Memory.database import db
    db.close()

@app.get("/")
async def root():
    return {"message": "LLM Chat API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        from app.Memory.database import db
        if not db._initialized:
            return {"status": "unhealthy", "database": "not_initialized"}, 503
        
        # Quick DB query to verify connection
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check agent manager
        from app.LLM.agent_manager import _agent_manager_instance
        if _agent_manager_instance is None:
            return {"status": "unhealthy", "agent_manager": "not_initialized"}, 503
        
        return {
            "status": "healthy",
            "database": "connected",
            "agent_manager": "initialized"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 503

@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(session_data: SessionCreate):
    """Create a new chat session."""
    model = session_data.model
    if model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model must be one of: {', '.join(ALLOWED_MODELS)}"
        )
    
    from app.LLM.agent_manager import ensure_session_exists
    session_id = str(uuid.uuid4())
    if ensure_session_exists(session_id, model):
        logger.info(f"Created new session {session_id} with model {model}")
        return SessionResponse(session_id=session_id, model=model)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@app.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_endpoint(session_id: str):
    """Get session metadata."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return SessionDetail(**session)

@app.get("/sessions/{session_id}/messages", response_model=list[Message])
async def get_messages_endpoint(session_id: str):
    """Get all messages for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    messages = get_messages(session_id)
    return [Message(**msg) for msg in messages]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Send a chat message and get a streaming response using the Agent Manager."""
    # Note: Model validation is kept for API compatibility, but agent manager uses DEFAULT_MODEL
    if request.model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model must be one of: {', '.join(ALLOWED_MODELS)}"
        )
    
    # Ensure session exists
    from app.LLM.agent_manager import ensure_session_exists
    if not ensure_session_exists(request.session_id, request.model):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ensure session exists"
        )
    
    logger.info(
        f"Chat request - Session: {request.session_id}, "
        f"Message length: {len(request.message)}"
    )
    
    try:
        # Get the agent manager instance
        agent_manager = get_agent_manager()
        
        def generate():
            try:
                # Stream agent response with automatic history management
                for chunk in agent_manager.stream(
                    input_text=request.message,
                    session_id=request.session_id,
                    include_history=True
                ):
                    if chunk:
                        yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
                
                logger.info(
                    f"Chat completed - Session: {request.session_id}"
                )
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to get response from AI model. Please try again."
        )

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)

