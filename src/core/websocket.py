"""WebSocket client implementation for real-time communication with OpenAI's Realtime API.

This module provides a WebSocket client that handles:
- Secure connection establishment with authentication
- Session management and initialization
- Message queuing and delivery
- Event-based message handling
- Automatic reconnection with exponential backoff
- Resource cleanup

Example usage:
    config = Config(api_key="your-key", model_version="gpt-4o-realtime-preview-2024-12-17")
    client = WebSocketClient(config)
    await client.connect()
    await client.send_message({"type": "your-message"})
    await client.listen()  # Start listening for responses
    await client.disconnect()
"""

import json
import asyncio
import logging
import uuid
import websockets
from typing import Dict, Any, Callable, Optional, List
from .config import Config
from .memory_management import MemoryManager

logger = logging.getLogger(__name__)

class WebSocketClient:
    """WebSocket client for real-time communication with OpenAI's API.
    
    This class manages the WebSocket connection lifecycle, handles message
    routing, and provides automatic reconnection capabilities.
    
    Attributes:
        config (Config): Configuration for the WebSocket client
        is_connected (bool): Current connection status
        message_queue (List[Dict[str, Any]]): Queue for messages when disconnected
        event_handlers (Dict[str, Callable]): Registered event handlers for different message types
    """
    
    def __init__(self, config: Config, memory_manager: Optional[MemoryManager] = None):
        """Initialize WebSocket client with configuration.
        
        Args:
            config: Configuration object containing API key and settings
            memory_manager: Optional memory manager for resource tracking
        """
        self.config = config
        self._ws = None
        self.is_connected = False
        self.message_queue: List[Dict[str, Any]] = []
        self.event_handlers: Dict[str, Callable] = {
            "input_audio_buffer.speech_started": self.handle_speech_started,
            "input_audio_buffer.speech_stopped": self.handle_speech_stopped,
            "response.audio.delta": self.handle_audio_delta,
            "response.text.delta": self.handle_text_delta,
            "response.audio.done": self.handle_audio_done,
            "response.text.done": self.handle_text_done,
            "response.done": self.handle_response_done,
            "error": self.handle_error
        }
        self.session_id = None
        self.current_conversation_id = None
        self.memory_manager = memory_manager
        self.client_id = str(uuid.uuid4())
        
    async def _track_connection(self):
        """Track connection resource usage."""
        if self.memory_manager:
            await self.memory_manager.track_resource(
                self.client_id,
                "websocket",
                1024 * 1024,  # Estimate 1MB per connection
                {
                    "model_version": self.config.model_version,
                    "session_id": self.session_id
                }
            )
            
    async def _release_connection(self):
        """Release connection resource tracking."""
        if self.memory_manager:
            await self.memory_manager.release_resource(self.client_id)
            
    async def _track_message(self, message: Dict[str, Any], size_bytes: int):
        """Track message resource usage.
        
        Args:
            message: Message being sent/received
            size_bytes: Size of the message in bytes
        """
        if self.memory_manager:
            message_id = str(uuid.uuid4())
            await self.memory_manager.track_resource(
                message_id,
                "message",
                size_bytes,
                {
                    "type": message.get("type"),
                    "client_id": self.client_id
                }
            )
            return message_id
        return None
            
    @property
    def ws(self):
        """Get the WebSocket connection."""
        return self._ws
    
    @ws.setter
    def ws(self, value):
        """Set the WebSocket connection and update connection status."""
        self._ws = value
        self.is_connected = value is not None
        
    async def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """Establish WebSocket connection with retry logic."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                url = f"wss://api.openai.com/v1/realtime?model={self.config.model_version}"
                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
                
                async with await websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                    extra_headers=headers,
                    max_size=None
                ) as ws:
                    self.ws = ws
                    await self._track_connection()
                    await self.initialize_session()
                    return True
                    
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay * (2 ** (retry_count - 1)))
        return False

    async def initialize_session(self):
        """Initialize the session with required configuration."""
        session_config = self.config.to_session_config()
        await self.send_message(session_config)
            
    async def disconnect(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.error(f"Disconnect error: {str(e)}")
            finally:
                await self._release_connection()
                self.ws = None
                self.session_id = None
                self.current_conversation_id = None
            
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message through WebSocket."""
        if not self.is_connected:
            self.message_queue.append(message)
            return False
            
        try:
            message_data = json.dumps(message)
            message_size = len(message_data.encode('utf-8'))
            message_id = await self._track_message(message, message_size)
            
            await self.ws.send(message_data)
            
            if self.memory_manager and message_id:
                await self.memory_manager.release_resource(message_id)
            return True
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            return False
            
    async def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register custom event handler."""
        self.event_handlers[event_type] = handler
        
    async def handle_speech_started(self, message: Dict[str, Any]) -> None:
        """Handle speech started event."""
        logger.info(f"Speech started: {message.get('item_id')}")
        
    async def handle_speech_stopped(self, message: Dict[str, Any]) -> None:
        """Handle speech stopped event."""
        logger.info(f"Speech stopped: {message.get('item_id')}")
        
    async def handle_audio_delta(self, message: Dict[str, Any]) -> None:
        """Handle audio delta event."""
        if 'delta' in message:
            audio_data = message['delta']
            if len(audio_data) > self.config.audio_config.max_chunk_size:
                logger.warning("Audio chunk exceeds maximum size")
                return
                
            # Track audio chunk resource usage
            if self.memory_manager:
                chunk_id = str(uuid.uuid4())
                await self.memory_manager.track_resource(
                    chunk_id,
                    "audio_chunk",
                    len(audio_data),
                    {"client_id": self.client_id}
                )
                try:
                    # Process audio chunk
                    pass
                finally:
                    await self.memory_manager.release_resource(chunk_id)
            
    async def handle_text_delta(self, message: Dict[str, Any]) -> None:
        """Handle text delta event."""
        if 'delta' in message:
            # Process text chunk
            pass
            
    async def handle_audio_done(self, message: Dict[str, Any]) -> None:
        """Handle audio done event."""
        logger.info("Audio response completed")
        
    async def handle_text_done(self, message: Dict[str, Any]) -> None:
        """Handle text done event."""
        logger.info("Text response completed")
        
    async def handle_response_done(self, message: Dict[str, Any]) -> None:
        """Handle response done event."""
        logger.info("Response completed")
        
    async def handle_error(self, message: Dict[str, Any]) -> None:
        """Handle error event."""
        logger.error(f"Error received: {message}")
        await self.disconnect()
        
    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message."""
        event_type = message.get("type")
        if event_type in self.event_handlers:
            await self.event_handlers[event_type](message)
        else:
            logger.warning(f"Unhandled event type: {event_type}")
            
    async def listen(self) -> None:
        """Listen for incoming messages."""
        if not self.is_connected:
            return
            
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                await self.process_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.ws = None
        except Exception as e:
            logger.error(f"Listen error: {str(e)}")
            self.ws = None 

    async def send_audio(self, audio_data: bytes) -> bool:
        """Send audio data through WebSocket."""
        if len(audio_data) > self.config.audio_config.max_chunk_size:
            logger.error("Audio data exceeds maximum chunk size")
            return False
            
        # Track audio resource usage
        if self.memory_manager:
            audio_id = str(uuid.uuid4())
            await self.memory_manager.track_resource(
                audio_id,
                "audio_input",
                len(audio_data),
                {"client_id": self.client_id}
            )
            
        try:
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_data
            }
            success = await self.send_message(message)
            
            if self.memory_manager:
                await self.memory_manager.release_resource(audio_id)
            return success
        except Exception as e:
            logger.error(f"Send audio error: {str(e)}")
            if self.memory_manager:
                await self.memory_manager.release_resource(audio_id)
            return False

    async def commit_audio(self) -> bool:
        """Commit the current audio buffer."""
        message = {
            "type": "input_audio_buffer.commit"
        }
        return await self.send_message(message)

    async def clear_audio(self) -> bool:
        """Clear the current audio buffer."""
        message = {
            "type": "input_audio_buffer.clear"
        }
        return await self.send_message(message)

    async def create_response(self, modalities: Optional[List[str]] = None, instructions: Optional[str] = None) -> bool:
        """Create a new response."""
        message = {
            "type": "response.create",
            "response": {
                "modalities": modalities or self.config.modalities,
                "instructions": instructions or self.config.instructions
            }
        }
        return await self.send_message(message) 