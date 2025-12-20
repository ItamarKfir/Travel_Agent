"""
Database manager for maintaining a single SQLite connection.
"""
import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = "app_sessions.db"


class Database:
    """Manages a single SQLite connection for reuse."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the database connection and create tables."""
        if self._initialized:
            return
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                model TEXT NOT NULL
            )
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        self.conn.commit()
        self._initialized = True
        logger.info("Database initialized and connection established")
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor with automatic commit/rollback."""
        if not self.conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()
    
    def create_session(self, session_id: str, model: str) -> bool:
        """Create a new session."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO sessions (id, created_at, model) VALUES (?, ?, ?)",
                    (session_id, datetime.utcnow().isoformat(), model)
                )
            logger.info(f"Created session {session_id} with model {model}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Session {session_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session metadata."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """Get all messages for a session, ordered by creation time."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
                    (session_id,)
                )
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Save a message to the database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (session_id, role, content, datetime.utcnow().isoformat())
                )
            logger.debug(f"Saved {role} message for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self.conn = None
                self._initialized = False


# Global database instance
db = Database()

# Backward compatibility functions
def init_db():
    """Initialize the database with required tables."""
    db.initialize()

def create_session(session_id: str, model: str) -> bool:
    """Create a new session."""
    return db.create_session(session_id, model)

def get_session(session_id: str):
    """Get session metadata."""
    return db.get_session(session_id)

def get_messages(session_id: str):
    """Get all messages for a session, ordered by creation time."""
    return db.get_messages(session_id)

def save_message(session_id: str, role: str, content: str) -> bool:
    """Save a message to the database."""
    return db.save_message(session_id, role, content)
