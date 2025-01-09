"""Session manager module for handling WebSocket session lifecycle and state."""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .config import Config
from .websocket import WebSocketClient
from .memory_management import MemoryManager
from .connection_pool import ConnectionPool

logger = logging.getLogger(__name__)

class Session:
    """WebSocket session representation."""
    
    def __init__(self, session_id: str, config: Config):
        """Initialize session.
        
        Args:
            session_id: Unique session identifier
            config: Session configuration
        """
        self.session_id = session_id
        self.config = config
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.state = "initializing"
        self.client: Optional[WebSocketClient] = None
        self.conversation_id: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_active = datetime.now()
        
    def is_expired(self, ttl: int = 1800) -> bool:
        """Check if session has expired.
        
        Args:
            ttl: Time-to-live in seconds (default 30 minutes)
            
        Returns:
            True if session has expired, False otherwise
        """
        return (datetime.now() - self.last_active).total_seconds() > ttl

class SessionManager:
    """Session manager for handling WebSocket sessions.
    
    This class provides:
    - Session lifecycle management
    - Session state tracking
    - Automatic cleanup of expired sessions
    - Integration with connection pool and memory manager
    """
    
    def __init__(self, 
                 max_sessions: int = 100,
                 session_ttl: int = 1800,
                 connection_pool: Optional[ConnectionPool] = None,
                 memory_manager: Optional[MemoryManager] = None):
        """Initialize session manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_ttl: Session time-to-live in seconds (default 30 minutes)
            connection_pool: Optional connection pool for WebSocket connections
            memory_manager: Optional memory manager for resource tracking
        """
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl
        self.connection_pool = connection_pool
        self.memory_manager = memory_manager
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start session manager and cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def stop(self):
        """Stop session manager and cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.cleanup_all_sessions()
        
    async def create_session(self, config: Config) -> Session:
        """Create a new session.
        
        Args:
            config: Session configuration
            
        Returns:
            New session instance
            
        Raises:
            RuntimeError: If session limit is reached
        """
        if len(self.sessions) >= self.max_sessions:
            await self.cleanup_expired_sessions()
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("Session limit reached")
                
        session_id = str(uuid.uuid4())
        session = Session(session_id, config)
        
        try:
            if self.connection_pool:
                async with self.connection_pool.get_connection(config) as client:
                    session.client = client
                    session.state = "active"
            else:
                client = WebSocketClient(config, self.memory_manager)
                if await client.connect():
                    session.client = client
                    session.state = "active"
                else:
                    raise RuntimeError("Failed to establish WebSocket connection")
                    
            if self.memory_manager:
                await self.memory_manager.track_resource(
                    session_id,
                    "session",
                    1024 * 1024,  # Estimate 1MB per session
                    {
                        "model_version": config.model_version,
                        "created_at": session.created_at.isoformat()
                    }
                )
                
            self.sessions[session_id] = session
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            if session.client and not self.connection_pool:
                await session.client.disconnect()
            raise
            
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session instance if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired(self.session_ttl):
                await self.cleanup_session(session_id)
                return None
            session.update_activity()
        return session
        
    async def cleanup_session(self, session_id: str):
        """Clean up a specific session.
        
        Args:
            session_id: Session identifier to clean up
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.client and not self.connection_pool:
                await session.client.disconnect()
            if self.memory_manager:
                await self.memory_manager.release_resource(session_id)
            del self.sessions[session_id]
            
    async def cleanup_expired_sessions(self):
        """Clean up all expired sessions."""
        for session_id, session in list(self.sessions.items()):
            if session.is_expired(self.session_ttl):
                logger.info(f"Cleaning up expired session {session_id}")
                await self.cleanup_session(session_id)
                
    async def cleanup_all_sessions(self):
        """Clean up all sessions."""
        for session_id in list(self.sessions.keys()):
            await self.cleanup_session(session_id)
            
    async def _cleanup_loop(self):
        """Background task for cleaning up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics.
        
        Returns:
            Dictionary containing session statistics
        """
        current_time = datetime.now()
        active_count = sum(1 for s in self.sessions.values() 
                         if not s.is_expired(self.session_ttl))
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_count,
            "expired_sessions": len(self.sessions) - active_count,
            "session_utilization": len(self.sessions) / self.max_sessions
        } 