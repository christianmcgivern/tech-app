import asyncio
import json
import logging
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
    
    async def register(self, websocket: WebSocketServerProtocol, user_id: str):
        """Register a new WebSocket connection."""
        connection_id = id(websocket)
        self.connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"Registered WebSocket connection {connection_id} for user {user_id}")
    
    async def unregister(self, websocket: WebSocketServerProtocol, user_id: str):
        """Unregister a WebSocket connection."""
        connection_id = id(websocket)
        
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"Unregistered WebSocket connection {connection_id} for user {user_id}")
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        if not self.connections:
            return
            
        # Create websockets.gather() tasks for all connections
        tasks = []
        for websocket in self.connections.values():
            try:
                tasks.append(asyncio.create_task(websocket.send(message)))
            except websockets.exceptions.ConnectionClosed:
                continue
        
        # Wait for all sends to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_user(self, user_id: str, message: str):
        """Send a message to a specific user's connections."""
        if user_id not in self.user_connections:
            return
            
        tasks = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                websocket = self.connections[connection_id]
                try:
                    tasks.append(asyncio.create_task(websocket.send(message)))
                except websockets.exceptions.ConnectionClosed:
                    continue
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_users(self, user_ids: Set[str], message: str):
        """Send a message to multiple users' connections."""
        tasks = []
        for user_id in user_ids:
            if user_id in self.user_connections:
                for connection_id in self.user_connections[user_id]:
                    if connection_id in self.connections:
                        websocket = self.connections[connection_id]
                        try:
                            tasks.append(asyncio.create_task(websocket.send(message)))
                        except websockets.exceptions.ConnectionClosed:
                            continue
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, user_id: str):
        """Handle a WebSocket connection."""
        try:
            await self.register(websocket, user_id)
            
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        # Handle incoming messages if needed
                        logger.debug(f"Received message from user {user_id}: {data}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received from user {user_id}")
                        
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                await self.unregister(websocket, user_id)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {str(e)}")
            if websocket in self.connections.values():
                await self.unregister(websocket, user_id) 