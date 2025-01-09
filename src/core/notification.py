from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications that can be sent."""
    ISSUE_DETECTED = "issue_detected"
    OFFICE_ALERT = "office_alert"
    STATUS_UPDATE = "status_update"
    EQUIPMENT_ALERT = "equipment_alert"
    INVENTORY_ALERT = "inventory_alert"
    WORK_ORDER_UPDATE = "work_order_update"

@dataclass
class Notification:
    """Data class representing a notification."""
    id: str
    type: NotificationType
    message: str
    timestamp: datetime
    priority: int
    metadata: Optional[Dict] = None
    recipient_ids: Optional[List[str]] = None
    read: bool = False

class NotificationDeliveryMethod(ABC):
    """Abstract base class for notification delivery methods."""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send a notification using this delivery method."""
        pass

class AppNotificationDelivery(NotificationDeliveryMethod):
    """In-app notification delivery implementation."""
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.unread_notifications: Dict[str, Notification] = {}
    
    async def send(self, notification: Notification) -> bool:
        if not self.websocket_manager:
            logger.error("WebSocket manager not initialized")
            return False
            
        try:
            # Store notification
            self.unread_notifications[notification.id] = notification
            
            # Create dashboard update event
            event = {
                "type": "dashboard.notification.update",
                "data": {
                    "unread_count": len(self.unread_notifications),
                    "notification": {
                        "id": notification.id,
                        "type": notification.type.value,
                        "message": notification.message,
                        "timestamp": notification.timestamp.isoformat(),
                        "priority": notification.priority,
                        "metadata": notification.metadata
                    }
                }
            }
            # Send through WebSocket
            await self.websocket_manager.broadcast(json.dumps(event))
            return True
        except Exception as e:
            logger.error(f"Failed to send app notification: {str(e)}")
            return False
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read and remove it from unread count."""
        if notification_id in self.unread_notifications:
            notification = self.unread_notifications.pop(notification_id)
            notification.read = True
            return True
        return False
    
    def get_unread_count(self) -> int:
        """Get the current number of unread notifications."""
        return len(self.unread_notifications)

class NotificationService:
    """Main notification service that handles sending notifications through app delivery only."""
    
    def __init__(self):
        self.app_delivery = None
        self.notification_queue = asyncio.Queue()
        self._running = False
    
    def initialize_app_delivery(self, websocket_manager):
        """Initialize app notification delivery."""
        self.app_delivery = AppNotificationDelivery(websocket_manager)
        logger.info("Initialized app notification delivery")
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send a notification through app delivery."""
        if not self.app_delivery:
            logger.error("App delivery not initialized")
            return False
        
        try:
            return await self.app_delivery.send(notification)
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    async def queue_notification(self, notification: Notification):
        """Queue a notification for processing."""
        await self.notification_queue.put(notification)
    
    async def start_processing(self):
        """Start processing notifications from the queue."""
        self._running = True
        while self._running:
            try:
                notification = await self.notification_queue.get()
                await self.send_notification(notification)
                self.notification_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing notification: {str(e)}")
    
    def stop_processing(self):
        """Stop processing notifications."""
        self._running = False
    
    def get_unread_count(self) -> int:
        """Get the current number of unread notifications."""
        if self.app_delivery:
            return self.app_delivery.get_unread_count()
        return 0
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        if self.app_delivery and self.app_delivery.mark_as_read(notification_id):
            # Send updated count through WebSocket
            event = {
                "type": "dashboard.notification.update",
                "data": {
                    "unread_count": self.app_delivery.get_unread_count()
                }
            }
            await self.app_delivery.websocket_manager.broadcast(json.dumps(event))
            return True
        return False 