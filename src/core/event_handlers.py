"""Event handlers for the Realtime API WebSocket events."""

from typing import Dict, Any, Optional, Callable
import base64
from functools import wraps
from ..utils.logging import setup_logger
from ..core.audio import AudioHandler
from ..core.work_order import WorkOrderManager

logger = setup_logger(__name__)

def error_boundary(func: Callable):
    """Decorator to add error boundary to event handlers."""
    @wraps(func)
    async def wrapper(self, event: Dict[str, Any], *args, **kwargs):
        try:
            return await func(self, event, *args, **kwargs)
        except Exception as e:
            event_type = event.get("type", "unknown")
            logger.error(f"Error in event handler {func.__name__} for event {event_type}: {e}")
            # Optionally propagate certain errors
            if isinstance(e, (ValueError, KeyError)):
                raise
    return wrapper

class EventHandlers:
    def __init__(self, websocket_client, audio_handler: Optional[AudioHandler] = None, work_order_manager: Optional[WorkOrderManager] = None):
        """Initialize event handlers.
        
        Args:
            websocket_client: WebSocket client instance
            audio_handler: Optional audio handler instance
            work_order_manager: Optional work order manager instance
        """
        self.websocket_client = websocket_client
        self.audio_handler = audio_handler
        self.work_order_manager = work_order_manager
        self._validate_handlers()

    def _validate_handlers(self):
        """Validate that required handlers are initialized."""
        if not self.audio_handler:
            logger.warning("Audio handler not initialized - audio features will be disabled")
        if not self.work_order_manager:
            logger.warning("Work order manager not initialized - work order features will be disabled")

    @error_boundary
    async def handle_session_created(self, event: Dict[str, Any]):
        """Handle session.created event."""
        session_id = event.get("session_id")
        if not session_id:
            raise ValueError("Session ID not found in session.created event")
        logger.info(f"Session created with ID: {session_id}")

    @error_boundary
    async def handle_session_updated(self, event: Dict[str, Any]):
        """Handle session.updated event."""
        logger.info("Session configuration updated")

    @error_boundary
    async def handle_input_audio_buffer_speech_started(self, event: Dict[str, Any]):
        """Handle input_audio_buffer.speech_started event."""
        logger.info("Speech started in input audio buffer")

    @error_boundary
    async def handle_input_audio_buffer_speech_stopped(self, event: Dict[str, Any]):
        """Handle input_audio_buffer.speech_stopped event."""
        logger.info("Speech stopped in input audio buffer")

    @error_boundary
    async def handle_input_audio_buffer_committed(self, event: Dict[str, Any]):
        """Handle input_audio_buffer.committed event."""
        logger.info("Audio buffer committed")

    @error_boundary
    async def handle_input_audio_buffer_cleared(self, event: Dict[str, Any]):
        """Handle input_audio_buffer.cleared event."""
        logger.info("Audio buffer cleared")

    @error_boundary
    async def handle_conversation_item_created(self, event: Dict[str, Any]):
        """Handle conversation.item.created event."""
        item_id = event.get("item_id")
        if not item_id:
            raise ValueError("Item ID not found in conversation.item.created event")
        logger.info(f"Conversation item created: {item_id}")

    @error_boundary
    async def handle_response_created(self, event: Dict[str, Any]):
        """Handle response.created event."""
        response_id = event.get("response_id")
        if not response_id:
            raise ValueError("Response ID not found in response.created event")
        logger.info(f"New response started: {response_id}")

    @error_boundary
    async def handle_response_text_delta(self, event: Dict[str, Any]):
        """Handle response.text.delta event."""
        text = event.get("text", "")
        logger.debug(f"Received text delta: {text}")

    @error_boundary
    async def handle_response_text_done(self, event: Dict[str, Any]):
        """Handle response.text.done event."""
        logger.info("Text response completed")

    @error_boundary
    async def handle_response_audio_delta(self, event: Dict[str, Any]):
        """Handle response.audio.delta event."""
        if not self.audio_handler:
            logger.warning("Audio handler not initialized - skipping audio delta")
            return

        try:
            if audio_data := event.get("audio"):
                decoded_audio = base64.b64decode(audio_data)
                await self.audio_handler.play_audio(decoded_audio)
                logger.debug("Processed audio delta successfully")
            else:
                logger.warning("No audio data in audio delta event")
        except base64.binascii.Error as e:
            logger.error(f"Failed to decode audio data: {e}")
        except Exception as e:
            logger.error(f"Failed to process audio delta: {e}")

    @error_boundary
    async def handle_response_audio_done(self, event: Dict[str, Any]):
        """Handle response.audio.done event."""
        logger.info("Audio response completed")

    @error_boundary
    async def handle_response_function_call_delta(self, event: Dict[str, Any]):
        """Handle response.function_call_arguments.delta event."""
        delta = event.get("delta", "")
        logger.debug(f"Received function call delta: {delta}")

    @error_boundary
    async def handle_response_function_call_done(self, event: Dict[str, Any]):
        """Handle response.function_call_arguments.done event."""
        call_id = event.get("call_id")
        if not call_id:
            raise ValueError("Call ID not found in function call done event")
        logger.info(f"Function call completed: {call_id}")

    @error_boundary
    async def handle_error(self, event: Dict[str, Any]):
        """Handle error event."""
        error = event.get("error", {})
        error_message = error.get("message", "Unknown error")
        error_type = error.get("type", "Unknown type")
        logger.error(f"Error received - Type: {error_type}, Message: {error_message}")

    @error_boundary
    async def handle_rate_limits(self, event: Dict[str, Any]):
        """Handle rate_limits.updated event."""
        rate_limits = event.get("rate_limits", [])
        for limit in rate_limits:
            name = limit.get("name", "unknown")
            remaining = limit.get("remaining", 0)
            reset_seconds = limit.get("reset_seconds", 0)
            logger.info(f"Rate limit update - {name}: {remaining} remaining, resets in {reset_seconds}s")

    @error_boundary
    async def handle_work_order_update(self, event: Dict[str, Any]):
        """Handle work order update events."""
        if not self.work_order_manager:
            logger.error("Work order manager not initialized")
            return

        order_id = event.get("order_id")
        if not order_id:
            raise ValueError("No order_id in work order update event")

        try:
            latitude = event.get("latitude")
            longitude = event.get("longitude")
            if latitude is None or longitude is None:
                raise ValueError("Missing location coordinates in work order update")

            success = await self.work_order_manager.update_location(
                order_id, latitude, longitude
            )
            if not success:
                logger.warning(f"Failed to update work order location for {order_id}")
        except Exception as e:
            logger.error(f"Failed to update work order location: {e}")
            raise 