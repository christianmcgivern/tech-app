# Step 5: Notification System

## Overview
The notification system provides real-time updates to both office staff and technicians through app notifications. The system is integrated with WebSocket connections to ensure immediate delivery of important updates.

## Components

### 1. Notification Types
```python
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
```

### 2. Database Schema
```sql
-- Notifications Table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    notification_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Manual Notifications Table
CREATE TABLE manual_notifications (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    message TEXT,
    priority VARCHAR(50) DEFAULT 'normal',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. WebSocket Manager
```python
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
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        if not self.connections:
            return
            
        tasks = []
        for websocket in self.connections.values():
            try:
                tasks.append(asyncio.create_task(websocket.send(message)))
            except websockets.exceptions.ConnectionClosed:
                continue
        
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
```

### 4. Notification Service
```python
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
            event = {
                "type": "dashboard.notification.update",
                "data": {
                    "unread_count": self.app_delivery.get_unread_count()
                }
            }
            await self.app_delivery.websocket_manager.broadcast(json.dumps(event))
            return True
        return False
```

### 5. Notification Manager
```python
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
```

## Frontend Integration

### 1. Office Platform
```typescript
// WebSocket Hook
const useWebSocket = () => {
  const socket = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const connect = () => {
      socket.current = new WebSocket('ws://localhost:3000/ws');
      
      socket.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      socket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleNotification(data);
      };

      socket.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected, attempting reconnect...');
        setTimeout(connect, 5000);
      };

      socket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connect();

    return () => {
      socket.current?.close();
    };
  }, []);

  return { isConnected, socket: socket.current };
};

// Notification Badge
const NotificationBadge = () => {
  const { unreadCount } = useNotifications();

  return unreadCount > 0 ? (
    <span className="badge">{unreadCount}</span>
  ) : null;
};
```

### 2. Technician App
```typescript
// Notification Context
const NotificationContext = createContext<{
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => Promise<void>;
}>({
  notifications: [],
  unreadCount: 0,
  markAsRead: async () => {}
});

// Notification Provider
export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      socket.current = new WebSocket('ws://localhost:3000/ws');
      
      socket.current.onopen = () => {
        console.log('WebSocket connected');
      };

      socket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'dashboard.notification.update') {
          handleNotificationUpdate(data.data);
        }
      };

      socket.current.onclose = () => {
        console.log('WebSocket disconnected, attempting reconnect...');
        setTimeout(connect, 5000);
      };

      socket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connect();

    return () => {
      socket.current?.close();
    };
  }, []);

  const handleNotificationUpdate = (data: any) => {
    if (data.notification) {
      setNotifications(prev => [...prev, data.notification]);
    }
    if (typeof data.unread_count === 'number') {
      setUnreadCount(data.unread_count);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await api.markNotificationAsRead(id);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, markAsRead }}>
      {children}
    </NotificationContext.Provider>
  );
};
```

## Error Handling

1. **Connection Errors**
   - WebSocket connection failures with automatic reconnection
   - Message delivery failures
   - Queue processing errors
   - Database transaction errors

2. **Notification Errors**
   - Invalid notification types
   - Missing required fields
   - Delivery failures
   - Queue overflow

3. **State Management**
   - Connection state tracking
   - Notification state consistency
   - Queue state management
   - Active alerts tracking

## Best Practices

1. **WebSocket Management**
   - Implement automatic reconnection
   - Handle connection state properly
   - Clean up resources on disconnect
   - Use proper error boundaries

2. **Notification Handling**
   - Queue notifications for reliability
   - Implement proper error handling
   - Track notification state
   - Handle offline scenarios

3. **Performance**
   - Use connection pooling
   - Implement proper cleanup
   - Handle queue overflow
   - Manage memory usage

## Current Status
- [x] Core notification system implemented
- [x] WebSocket integration complete
- [x] Frontend components developed
- [x] Database schema deployed
- [x] Queue management implemented
- [x] Error handling complete
- [x] Connection management implemented
- [x] Testing framework established 