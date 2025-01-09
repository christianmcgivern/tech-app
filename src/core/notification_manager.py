import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .notification import (
    Notification,
    NotificationService,
    NotificationType
)

class NotificationManager:
    """Manages notification triggers and integrates with work order and technician systems."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.active_alerts: Dict[str, Notification] = {}
    
    async def handle_work_order_update(
        self,
        work_order_id: str,
        status: str,
        notes: Optional[str] = None,
        issues: Optional[str] = None,
        alert_office: bool = False
    ):
        """Handle notifications for work order updates."""
        notifications = []
        
        # Create status update notification
        notification_id = str(uuid.uuid4())
        status_notification = Notification(
            id=notification_id,
            type=NotificationType.STATUS_UPDATE,
            message=f"Work order {work_order_id} status updated to: {status}",
            timestamp=datetime.now(),
            priority=1,
            metadata={
                "work_order_id": work_order_id,
                "status": status,
                "notes": notes
            }
        )
        self.active_alerts[notification_id] = status_notification
        notifications.append(status_notification)
        
        # Handle issues if reported
        if issues:
            notification_id = str(uuid.uuid4())
            issue_notification = Notification(
                id=notification_id,
                type=NotificationType.ISSUE_DETECTED,
                message=f"Issue reported for work order {work_order_id}: {issues}",
                timestamp=datetime.now(),
                priority=2,
                metadata={
                    "work_order_id": work_order_id,
                    "issue_description": issues
                }
            )
            self.active_alerts[notification_id] = issue_notification
            notifications.append(issue_notification)
            
        # Handle office alerts
        if alert_office:
            notification_id = str(uuid.uuid4())
            office_notification = Notification(
                id=notification_id,
                type=NotificationType.OFFICE_ALERT,
                message=f"Office alert requested for work order {work_order_id}",
                timestamp=datetime.now(),
                priority=3,
                metadata={
                    "work_order_id": work_order_id,
                    "status": status,
                    "notes": notes,
                    "issues": issues
                }
            )
            self.active_alerts[notification_id] = office_notification
            notifications.append(office_notification)
        
        # Queue all notifications
        for notification in notifications:
            await self.notification_service.queue_notification(notification)
    
    async def handle_equipment_alert(
        self,
        equipment_id: str,
        issue_type: str,
        description: str,
        severity: int = 1
    ):
        """Handle notifications for equipment issues."""
        notification_id = str(uuid.uuid4())
        notification = Notification(
            id=notification_id,
            type=NotificationType.EQUIPMENT_ALERT,
            message=f"Equipment alert: {issue_type} - {description}",
            timestamp=datetime.now(),
            priority=severity,
            metadata={
                "equipment_id": equipment_id,
                "issue_type": issue_type,
                "description": description
            }
        )
        self.active_alerts[notification_id] = notification
        await self.notification_service.queue_notification(notification)
    
    async def handle_inventory_alert(
        self,
        item_id: str,
        current_level: int,
        threshold: int,
        location: str
    ):
        """Handle notifications for inventory levels."""
        if current_level <= threshold:
            notification_id = str(uuid.uuid4())
            notification = Notification(
                id=notification_id,
                type=NotificationType.INVENTORY_ALERT,
                message=f"Low inventory alert for item {item_id} at location {location}",
                timestamp=datetime.now(),
                priority=2,
                metadata={
                    "item_id": item_id,
                    "current_level": current_level,
                    "threshold": threshold,
                    "location": location
                }
            )
            self.active_alerts[notification_id] = notification
            await self.notification_service.queue_notification(notification)
    
    def get_active_alerts(self) -> List[Notification]:
        """Get list of active alerts."""
        return list(self.active_alerts.values())
    
    async def acknowledge_alert(self, alert_id: str):
        """Acknowledge and remove an alert."""
        if alert_id in self.active_alerts:
            # Mark notification as read in the notification service
            await self.notification_service.mark_as_read(alert_id)
            # Remove from active alerts
            del self.active_alerts[alert_id] 