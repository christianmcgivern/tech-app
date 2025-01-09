"""Connection pool module for managing WebSocket connections."""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, AsyncContextManager
from contextlib import asynccontextmanager
from .websocket import WebSocketClient
from .config import Config

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Connection pool for managing WebSocket connections.
    
    This class provides:
    - Connection pooling with size limits
    - Connection reuse
    - Automatic cleanup of idle connections
    - Connection health monitoring
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        """Initialize connection pool.
        
        Args:
            max_size: Maximum number of connections in the pool
            ttl: Time-to-live in seconds for idle connections
        """
        self.pool: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.last_cleanup = time.time()
        
    @asynccontextmanager
    async def get_connection(self, config: Config) -> AsyncContextManager[WebSocketClient]:
        """Get a connection from the pool or create a new one.
        
        Args:
            config: WebSocket client configuration
            
        Returns:
            AsyncContextManager yielding a WebSocket client
            
        Raises:
            RuntimeError: If pool is exhausted and no connections can be cleaned up
        """
        conn = None
        try:
            conn = await self._acquire_connection(config)
            yield conn
        finally:
            if conn is not None:
                await self._release_connection(conn)
            
    async def _acquire_connection(self, config: Config) -> WebSocketClient:
        """Acquire a connection from the pool or create a new one.
        
        Args:
            config: WebSocket client configuration
            
        Returns:
            WebSocket client
            
        Raises:
            RuntimeError: If pool is exhausted and no connections can be cleaned up
        """
        # Try to find an existing connection
        for conn_id, conn_data in list(self.pool.items()):
            if self._is_connection_compatible(conn_data["client"], config):
                if await self._is_connection_valid(conn_data["client"]):
                    conn_data["last_used"] = time.time()
                    return conn_data["client"]
                else:
                    await self._remove_connection(conn_id)
                    
        # Clean up if pool is full
        if len(self.pool) >= self.max_size:
            await self._cleanup_expired()
            if len(self.pool) >= self.max_size:
                raise RuntimeError("Connection pool exhausted")
                
        # Create new connection
        client = WebSocketClient(config)
        try:
            if await client.connect():
                conn_id = str(uuid.uuid4())
                self.pool[conn_id] = {
                    "client": client,
                    "created_at": time.time(),
                    "last_used": time.time()
                }
                return client
            else:
                await client.disconnect()
                raise RuntimeError("Failed to create new connection")
        except Exception as e:
            await client.disconnect()
            raise RuntimeError(f"Failed to create new connection: {str(e)}")
            
    async def _release_connection(self, client: WebSocketClient):
        """Release a connection back to the pool.
        
        Args:
            client: WebSocket client to release
        """
        # Update last used time
        for conn_data in list(self.pool.values()):
            if conn_data["client"] is client:
                conn_data["last_used"] = time.time()
                break
                
    async def _remove_connection(self, conn_id: str):
        """Remove a connection from the pool.
        
        Args:
            conn_id: Connection ID to remove
        """
        if conn_id in self.pool:
            client = self.pool[conn_id]["client"]
            await client.disconnect()
            del self.pool[conn_id]
            
    async def _cleanup_expired(self):
        """Remove expired connections from the pool."""
        current_time = time.time()
        self.last_cleanup = current_time
        
        for conn_id, conn_data in list(self.pool.items()):
            if current_time - conn_data["last_used"] > self.ttl:
                logger.debug(f"Removing expired connection {conn_id}")
                await self._remove_connection(conn_id)
                
    def _is_connection_compatible(self, client: WebSocketClient, config: Config) -> bool:
        """Check if a connection is compatible with the given configuration.
        
        Args:
            client: WebSocket client to check
            config: Configuration to check against
            
        Returns:
            True if connection is compatible, False otherwise
        """
        return (
            client.config.model_version == config.model_version and
            client.config.voice == config.voice and
            client.config.modalities == config.modalities
        )
                
    async def _is_connection_valid(self, client: WebSocketClient) -> bool:
        """Check if a connection is still valid.
        
        Args:
            client: WebSocket client to check
            
        Returns:
            True if connection is valid, False otherwise
        """
        return client.is_connected
        
    async def close(self):
        """Close all connections in the pool."""
        for conn_id in list(self.pool.keys()):
            await self._remove_connection(conn_id)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.
        
        Returns:
            Dictionary containing pool statistics
        """
        current_time = time.time()
        active_count = sum(1 for c in self.pool.values() if current_time - c["last_used"] <= self.ttl)
        
        return {
            "total_connections": len(self.pool),
            "active_connections": active_count,
            "idle_connections": len(self.pool) - active_count,
            "pool_utilization": len(self.pool) / self.max_size
        } 