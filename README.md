# LLM Chat Application

A full-stack LLM chat application with FastAPI backend and React frontend, supporting multiple Google Gemini/Gemma models with persistent chat history.

## Features

- **Multiple Models**: Support for 4 different models (gemma-3-27b, gemini-2.5-flash-lite, gemini-2.5-flash, gemma-3-12b)
- **Session Management**: Create and manage multiple chat sessions
- **Persistent History**: All conversations saved to SQLite database
- **Dark Mode UI**: Modern, clean dark-themed interface
- **Real-time Chat**: Stream responses from Google Generative AI

## Project Structure

```
Travel_Agent/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   └── app_sessions.db       # SQLite database (created automatically)
├── frontend/        # React + Vite frontend
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google API Key for Generative AI

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   py -m venv venv
   ```
   Note: On Windows, use `py` instead of `python` if `python` command is not found.

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the `backend` directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   ```
   Copy from `.env.example` and add your actual API key.

6. Run the backend server:
   
   **Option 1: Using the run script (recommended for Windows):**
   ```powershell
   .\run.ps1
   ```
   Or double-click `run.bat` in Windows Explorer.
   
   **Option 2: Manual activation:**
   ```bash
   venv\Scripts\activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Usage

1. Start the backend server (see Backend Setup)
2. Start the frontend server (see Frontend Setup)
3. Open `http://localhost:5173` in your browser
4. Select a model from the dropdown
5. Start chatting! Your messages are automatically saved
6. Click "New Session" to start a fresh conversation

## API Endpoints

### POST /sessions
Create a new chat session.

**Request:**
```json
{
  "model": "gemini-2.5-flash"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "model": "gemini-2.5-flash"
}
```

### GET /sessions/{session_id}
Get session metadata.

**Response:**
```json
{
  "session_id": "uuid-string",
  "model": "gemini-2.5-flash",
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /sessions/{session_id}/messages
Get all messages for a session.

**Response:**
```json
[
  {
    "role": "user",
    "content": "Hello",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "role": "assistant",
    "content": "Hi! How can I help?",
    "created_at": "2024-01-01T00:00:01"
  }
]
```

### POST /chat
Send a chat message and get a response.

**Request:**
```json
{
  "session_id": "uuid-string",
  "message": "Hello, how are you?",
  "model": "gemini-2.5-flash"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "model": "gemini-2.5-flash",
  "answer": "I'm doing well, thank you!"
}
```

## Environment Variables

### Backend
- `GOOGLE_API_KEY`: Your Google Generative AI API key (required)

## Database

The backend uses SQLite (`app_sessions.db`) to store:
- **sessions**: Session metadata (id, created_at, model)
- **messages**: Chat messages (id, session_id, role, content, created_at)

The database is created automatically on first run.

## Development

### Backend
- Logs are printed to console
- Database file: `backend/app_sessions.db`
- API docs available at `http://localhost:8000/docs`

### Frontend
- Hot module replacement enabled
- TypeScript for type safety
- Dark mode styling

## Troubleshooting

1. **Backend won't start**: Check that `GOOGLE_API_KEY` is set in `.env`
2. **CORS errors**: Ensure backend is running on port 8000 and frontend on 5173
3. **Database errors**: Delete `backend/app_sessions.db` to reset (will lose all data)
4. **Model errors**: Verify your API key has access to the selected models

## License

See LICENSE file.
