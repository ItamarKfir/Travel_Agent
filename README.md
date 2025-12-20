# Smart AI Business Assistant

A powerful AI-powered business intelligence assistant that helps business owners understand customer feedback by analyzing reviews from **TripAdvisor** and **Google Places**. The application uses advanced Large Language Models (LLMs) to analyze, summarize, and provide actionable insights from customer reviews, helping businesses identify strengths, weaknesses, and opportunities for improvement.

## 🎯 Purpose

This application is designed for **business owners** who want to:
- **Understand customer sentiment** by analyzing reviews from multiple platforms
- **Identify common complaints and praises** across all customer feedback
- **Get actionable recommendations** on how to improve their business
- **Track what customers are saying** about their establishment in real-time
- **Make data-driven decisions** based on comprehensive review analysis

### 💼 Use Cases

**Hotel/Restaurant Owners:**
- "What are guests saying about our hotel's cleanliness?"
- "Analyze reviews for [Restaurant Name] and tell me how to improve"
- "What do customers love most about our service?"

**Business Managers:**
- "Get reviews for [Business Name] in [Location] and summarize key feedback"
- "What are the top 3 complaints customers have?"
- "Compare what Google Places vs TripAdvisor reviewers say"

**Marketing Teams:**
- "What themes emerge from our customer reviews?"
- "What should we highlight in our marketing based on positive feedback?"
- "Identify areas where we're losing customers based on negative reviews"

## ✨ Key Features

### Review Collection & Analysis
- **Multi-Platform Review Aggregation**: Automatically fetches reviews from both **Google Places** and **TripAdvisor** APIs
- **Intelligent Review Analysis**: Uses advanced LLM models to analyze sentiment, extract key themes, and identify patterns
- **Comprehensive Summarization**: Provides concise summaries of customer feedback highlighting main points
- **Actionable Insights**: Delivers specific recommendations on how businesses can improve based on review analysis

### AI-Powered Intelligence
- **Multiple LLM Models**: Support for Google Gemini models (gemini-2.5-flash-lite, gemini-2.5-flash) for flexible performance
- **ReAct Agent Framework**: Uses LangChain's ReAct (Reasoning + Acting) agent for intelligent tool usage and reasoning
- **Context-Aware Conversations**: Maintains conversation history to provide context-aware responses and follow-up analysis
- **Real-time Streaming**: Streams AI responses in real-time for better user experience

### User Experience
- **Session Management**: Create and manage multiple analysis sessions for different businesses or locations
- **Persistent History**: All conversations and analyses saved to SQLite database for future reference
- **Modern Dark Mode UI**: Clean, professional interface built with React and TypeScript
- **Interactive Chat Interface**: Natural language interface for asking questions about reviews and getting insights

## 🏗️ Project Structure

```
Travel_Agent/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── API/               # External API integrations
│   │   │   ├── google_places.py    # Google Places API client
│   │   │   └── tripadvisor.py      # TripAdvisor API client
│   │   ├── LLM/               # LLM and AI agent logic
│   │   │   ├── agent.py            # LangChain ReAct agent
│   │   │   ├── agent_manager.py   # Agent lifecycle management
│   │   │   ├── models.py           # Model configuration
│   │   │   └── prompts.py          # AI system prompts
│   │   ├── Memory/             # Conversation memory management
│   │   │   ├── database.py         # SQLite database operations
│   │   │   └── memory.py           # Memory/history handlers
│   │   ├── Tools/             # LangChain tools
│   │   │   └── place_reviews_tool.py  # Review fetching tool
│   │   └── main.py            # FastAPI application entry point
│   └── app_sessions.db        # SQLite database (auto-created)
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx            # Main React component
│   │   └── main.tsx          # Application entry point
│   └── package.json          # Node.js dependencies
└── README.md
```

## Prerequisites

### Backend Requirements
- **Python**: 3.11 or higher
- **pip**: Python package manager (usually comes with Python)
- **Google API Key**: For Google Generative AI (Gemini models) access
- **Google Places API Key**: For fetching Google Places reviews (optional, can use same key)
- **TripAdvisor API Key**: For fetching TripAdvisor reviews (optional)

### Frontend Requirements
- **Node.js**: 18.0.0 or higher
- **npm**: Node package manager (comes with Node.js)

## Installation & Setup

### Backend Installation

#### Step 1: Verify Python Installation
Check if Python is installed:
```bash
python --version
# or on Windows
py --version
```
You should see Python 3.11 or higher.

#### Step 2: Navigate to Backend Directory
```bash
cd backend
```

#### Step 3: Create Virtual Environment
Create an isolated Python environment:
```bash
# Windows
py -m venv venv

# Linux/Mac
python3 -m venv venv
```

#### Step 4: Activate Virtual Environment
```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

After activation, you should see `(venv)` in your terminal prompt.

#### Step 5: Install Python Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

**Python Packages Installed:**

**Web Framework:**
- `fastapi==0.115.0` - Modern, fast web framework for building REST APIs
- `uvicorn[standard]==0.32.0` - High-performance ASGI server for running FastAPI
- `pydantic==2.9.2` - Data validation and settings management using Python type annotations

**AI & LLM:**
- `google-generativeai>=0.7.0,<0.8.0` - Official Google Generative AI SDK for Gemini models
- `langchain==0.3.0` - Framework for developing LLM-powered applications with tool integration
- `langchain-google-genai==2.0.0` - LangChain integration for Google Gemini models
- `langchain-core==0.3.0` - Core LangChain abstractions and interfaces

**API Integrations:**
- `googlemaps==4.10.0` - Google Maps/Places API client for fetching place details and reviews
- `requests==2.31.0` - HTTP library for making API requests to TripAdvisor and other services

**Utilities:**
- `python-dotenv==1.0.1` - Load environment variables from .env files
- `pytest==8.3.3` - Testing framework for writing and running tests

#### Step 6: Configure Environment Variables
Create a `.env` file in the `backend` directory:
```bash
# Windows (PowerShell)
New-Item -Path .env -ItemType File

# Linux/Mac
touch .env
```

Add your API keys to the `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

**Note**: 
- Replace `your_google_api_key_here` with your actual Google API key
- The same key can be used for both Google Generative AI (Gemini) and Google Places API
- For TripAdvisor, you may need a separate API key (check TripAdvisor API documentation)

### Backend Running

#### Option 1: Using Run Scripts (Recommended for Windows)
```powershell
# PowerShell script
.\run.ps1

# Or double-click run.bat in Windows Explorer
```

#### Option 2: Manual Command
With virtual environment activated:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Debug Mode (with verbose logging)
```powershell
# Windows PowerShell
.\run_debug.ps1
```

**Backend Server:**
- URL: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

The `--reload` flag enables auto-reload on code changes (development mode).

---

### Frontend Installation

#### Step 1: Verify Node.js Installation
Check if Node.js and npm are installed:
```bash
node --version
npm --version
```
You should see Node.js 18.0.0 or higher and npm 9.0.0 or higher.

#### Step 2: Navigate to Frontend Directory
```bash
cd frontend
```

#### Step 3: Install Node.js Dependencies
Install all required npm packages:
```bash
npm install
```

**Node.js Packages Installed:**

**Dependencies (Production):**
- `react@^18.3.1` - React library for building user interfaces
- `react-dom@^18.3.1` - React DOM renderer

**DevDependencies (Development):**
- `@types/react@^18.3.1` - TypeScript type definitions for React
- `@types/react-dom@^18.3.1` - TypeScript type definitions for React DOM
- `@vitejs/plugin-react@^4.3.1` - Vite plugin for React
- `typescript@^5.5.3` - TypeScript compiler and language
- `vite@^5.4.0` - Next generation frontend build tool

This will create a `node_modules` directory with all dependencies.

### Frontend Running

#### Development Server
Start the development server with hot module replacement:
```bash
npm run dev
```

**Frontend Server:**
- URL: `http://localhost:5173`
- Hot Module Replacement: Enabled (auto-refresh on code changes)

#### Build for Production
Create an optimized production build:
```bash
npm run build
```

#### Preview Production Build
Preview the production build locally:
```bash
npm run preview
```

---

## Running the Full Application

### Start Both Servers

1. **Terminal 1 - Backend:**
   ```bash
   cd backend
   .\venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open Browser:**
   Navigate to `http://localhost:5173` to access the application.

## Usage

### Quick Start

1. **Start Backend Server:**
   - Open a terminal in the `backend` directory
   - Activate virtual environment and run the server (see [Backend Running](#backend-running))

2. **Start Frontend Server:**
   - Open another terminal in the `frontend` directory
   - Run `npm run dev` (see [Frontend Running](#frontend-running))

3. **Access Application:**
   - Open your browser and navigate to `http://localhost:5173`

4. **Using the Application:**
   - Select a model from the dropdown menu (gemini-2.5-flash-lite recommended for faster responses)
   - Ask the AI assistant about any business or place (e.g., "Get reviews for DoubleTree Hotel in Milan")
   - The AI will automatically fetch reviews from Google Places and TripAdvisor
   - Ask follow-up questions like:
     - "What are the main complaints?"
     - "How can this business improve?"
     - "Summarize the positive feedback"
     - "What do customers say about the service?"
   - All conversations are automatically saved for future reference
   - Click "New Session" to start analyzing a different business

## 🤖 LLM Technology Deep Dive

### Google Gemini Models

The application leverages Google's latest Gemini family of Large Language Models:

- **Gemini 2.5 Flash Lite**: Optimized for speed and efficiency, perfect for quick responses and lower latency
- **Gemini 2.5 Flash**: Balanced model offering better reasoning capabilities while maintaining good performance

**Why Gemini?**
- **Multimodal Understanding**: Can process and understand complex text, context, and structured data
- **Advanced Reasoning**: Uses chain-of-thought reasoning for better analysis
- **Tool Integration**: Seamlessly integrates with external APIs through LangChain
- **Cost-Effective**: Efficient models that provide high-quality results at lower costs

### LangChain ReAct Agent

The application uses LangChain's **ReAct (Reasoning + Acting)** agent pattern:

**How ReAct Works:**
1. **Reasoning**: The LLM thinks about what action to take
2. **Acting**: Executes tools (like fetching reviews) based on reasoning
3. **Observing**: Analyzes the results from tools
4. **Iterating**: Repeats the process until it has enough information to answer

**Benefits:**
- **Intelligent Tool Usage**: Automatically decides when to fetch reviews vs. when to answer directly
- **Context-Aware**: Maintains conversation history to understand references ("it", "that hotel", etc.)
- **Self-Correcting**: Can re-query APIs if initial results are insufficient
- **Transparent**: Shows reasoning process (thought → action → observation → answer)

### Memory & Context Management

- **Conversation Memory**: Stores all messages in SQLite database
- **Context Injection**: Automatically includes relevant conversation history in prompts
- **Session Isolation**: Each session maintains its own independent context
- **Long-term Memory**: Can reference previous analyses and insights across sessions

### Prompt Engineering

The system uses carefully crafted prompts to ensure:
- **Domain Focus**: Specialized for business review analysis
- **Accuracy**: Never invents or guesses information
- **Source Attribution**: Always cites where information comes from (Google Places, TripAdvisor)
- **Actionable Insights**: Provides specific, implementable recommendations


## 🔧 Technology Stack

### AI & Machine Learning
- **Google Gemini Models**: State-of-the-art LLMs for natural language understanding and generation
  - `gemini-2.5-flash-lite`: Fast, efficient model for quick responses
  - `gemini-2.5-flash`: Balanced model with better reasoning capabilities
- **LangChain Framework**: Orchestrates LLM interactions with tools and memory
  - **ReAct Agent**: Implements Reasoning + Acting pattern for intelligent tool usage
  - **Tool Integration**: Seamlessly connects LLM with external APIs (Google Places, TripAdvisor)
  - **Memory Management**: Maintains conversation context across interactions

### Backend Architecture
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Uvicorn**: High-performance ASGI server with async support
- **SQLite**: Lightweight database for session and conversation persistence
- **Pydantic**: Type-safe data validation and serialization

### Frontend Architecture
- **React 18**: Component-based UI library with hooks
- **TypeScript**: Type-safe JavaScript for better code quality
- **Vite**: Next-generation build tool for fast development and optimized production builds

### API Integrations
- **Google Places API**: Fetches place details, ratings, and customer reviews
- **TripAdvisor API**: Retrieves location reviews and ratings from TripAdvisor platform
- **Google Generative AI API**: Powers the LLM for analysis and insights

## Environment Variables

### Backend
- `GOOGLE_API_KEY`: Your Google API key (required for both Gemini models and Google Places API)

## 💾 Database

The backend uses SQLite (`app_sessions.db`) to store:
- **sessions**: Session metadata (id, created_at, model used)
- **messages**: Complete conversation history (id, session_id, role, content, created_at)

The database is created automatically on first run. All conversations and analyses are persisted, allowing you to:
- Review past analyses
- Continue conversations from where you left off
- Track insights over time
- Maintain context across multiple sessions

## 🚀 How It Works

### Review Analysis Workflow

1. **User Query**: Business owner asks about a place (e.g., "Analyze reviews for Hotel XYZ in Paris")

2. **Review Collection**: 
   - AI agent uses `get_place_reviews_from_apis` tool
   - Simultaneously queries Google Places and TripAdvisor APIs
   - Fetches latest reviews, ratings, and place details

3. **AI Analysis**:
   - LLM receives formatted review data from both sources
   - Analyzes sentiment, themes, and patterns across all reviews
   - Identifies common complaints, praises, and suggestions

4. **Insight Generation**:
   - Summarizes key findings
   - Provides actionable recommendations
   - Highlights areas for improvement
   - Presents balanced view of customer feedback

5. **Interactive Follow-up**:
   - Business owner can ask specific questions
   - AI uses conversation history for context-aware responses
   - Can drill down into specific aspects (service, cleanliness, value, etc.)

### Example Conversation Flow

```
User: "Get reviews for DoubleTree by Hilton Milan Malpensa"

AI: [Fetches reviews from Google Places and TripAdvisor]
    "I found DoubleTree by Hilton Milan Malpensa at [address]. 
     Google Places: 4.2/5.0 (1,234 reviews), TripAdvisor: 4.0/5.0 (567 reviews)..."

User: "What are the main complaints?"

AI: [Analyzes all reviews] 
    "Based on the reviews, the main complaints are:
     1. Slow check-in process during peak hours
     2. Airport shuttle timing issues
     3. Room cleanliness in some areas
     ..."

User: "How can they improve?"

AI: [Provides actionable recommendations]
    "To improve based on customer feedback:
     1. Implement express check-in for returning guests
     2. Add real-time shuttle tracking
     3. Increase housekeeping staff during busy periods
     ..."
```

## Development

### Backend
- **Logging**: Comprehensive logging to console with configurable levels
- **Database**: SQLite database at `backend/app_sessions.db`
- **API Documentation**: Interactive Swagger UI at `http://localhost:8000/docs`
- **Hot Reload**: Auto-reload on code changes (development mode)

### Frontend
- **Hot Module Replacement**: Instant updates during development
- **TypeScript**: Full type safety for better code quality
- **Dark Mode**: Modern, professional dark theme
- **Real-time Streaming**: SSE (Server-Sent Events) for live AI responses

## Troubleshooting

### Backend Issues

1. **Python not found:**
   - Windows: Try using `py` instead of `python`
   - Linux/Mac: Ensure Python 3.11+ is installed and in PATH
   - Verify with: `python --version` or `py --version`

2. **Virtual environment activation fails:**
   - Windows PowerShell: Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - Ensure you're in the `backend` directory
   - Try: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)

3. **pip install fails:**
   - Upgrade pip: `python -m pip install --upgrade pip`
   - Ensure virtual environment is activated (you should see `(venv)` in prompt)
   - Try: `pip install --upgrade -r requirements.txt`

4. **Backend won't start:**
   - Check that `GOOGLE_API_KEY` is set in `.env` file
   - Verify the `.env` file is in the `backend` directory
   - Check port 8000 is not already in use
   - Review error messages in terminal

5. **Module not found errors:**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check you're running from the correct directory

6. **Database errors:**
   - Delete `backend/app_sessions.db` to reset (will lose all data)
   - Ensure write permissions in the `backend` directory
   - Check disk space availability

### Frontend Issues

1. **Node.js not found:**
   - Install Node.js from [nodejs.org](https://nodejs.org/)
   - Verify installation: `node --version` and `npm --version`
   - Restart terminal after installation

2. **npm install fails:**
   - Clear npm cache: `npm cache clean --force`
   - Delete `node_modules` and `package-lock.json`, then run `npm install` again
   - Check internet connection
   - Try: `npm install --legacy-peer-deps`

3. **Port 5173 already in use:**
   - Stop other applications using port 5173
   - Or change port in `vite.config.ts`

4. **CORS errors:**
   - Ensure backend is running on port 8000
   - Ensure frontend is running on port 5173
   - Check browser console for specific error messages
   - Verify CORS settings in `backend/app/main.py`

### General Issues

1. **Model errors:**
   - Verify your API key has access to the selected models
   - Check Google API quota and billing status
   - Review backend logs for specific error messages

2. **Connection refused:**
   - Ensure both servers are running
   - Check firewall settings
   - Verify URLs match (localhost:8000 for backend, localhost:5173 for frontend)

3. **Hot reload not working:**
   - Frontend: Vite HMR should work automatically
   - Backend: Ensure `--reload` flag is used with uvicorn
   - Check file watchers are not disabled

## License

See LICENSE file.
