"""Work order management and processing system."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from ..utils.logging import setup_logger
from ..utils.config import load_config

logger = setup_logger(__name__)

class WorkOrderStatus(Enum):
    """Possible statuses for a work order."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class WorkOrderPriority(Enum):
    """Priority levels for work orders."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Location:
    """Represents a geographic location."""
    _latitude: float
    _longitude: float

    def __init__(self, latitude: float, longitude: float):
        self._latitude = latitude
        self._longitude = longitude
        self.validate()

    @property
    def latitude(self) -> float:
        """Get the latitude."""
        return self._latitude

    @property
    def longitude(self) -> float:
        """Get the longitude."""
        return self._longitude

    def validate(self) -> bool:
        """Validate location coordinates."""
        if not (-90 <= self._latitude <= 90):
            raise ValueError(f"Invalid latitude: {self._latitude}")
        if not (-180 <= self._longitude <= 180):
            raise ValueError(f"Invalid longitude: {self._longitude}")
        return True

@dataclass
class WorkOrderNote:
    """Represents a note on a work order."""
    _timestamp: datetime
    _content: str
    _author: Optional[str] = None

    def __init__(self, timestamp: datetime, content: str, author: Optional[str] = None):
        self._timestamp = timestamp
        self._content = content
        self._author = author

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp."""
        return self._timestamp

    @property
    def content(self) -> str:
        """Get the content."""
        return self._content

    @property
    def author(self) -> Optional[str]:
        """Get the author."""
        return self._author

@dataclass
class WorkOrder:
    """Represents a single work order."""
    order_id: str
    description: str
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    status: WorkOrderStatus = field(default=WorkOrderStatus.PENDING)
    assigned_technician: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    location: Optional[Location] = None
    notes: List[WorkOrderNote] = field(default_factory=list)

class WorkOrderManager:
    """Manages work orders and their lifecycle."""

    def __init__(self):
        self.config = load_config(validate_api_key=False)
        self.work_orders: Dict[str, WorkOrder] = {}
        self.queue: List[str] = []  # List of order_ids in priority order

    def _log_transaction(self, order_id: str, action: str, details: Optional[Dict[str, Any]] = None):
        """Log a work order transaction."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "order_id": order_id,
            "action": action,
            "details": details or {}
        }
        logger.info(f"Work order transaction: {log_entry}")

    @property
    def queue_size(self) -> int:
        """Get the current size of the work order queue."""
        return len(self.queue)

    def validate_queue_integrity(self) -> bool:
        """Validate the integrity of the work order queue."""
        if len(self.queue) == 0:
            return True
            
        # Check priority ordering
        for i in range(len(self.queue) - 1):
            current = self.work_orders[self.queue[i]]
            next_order = self.work_orders[self.queue[i + 1]]
            if current.priority.value < next_order.priority.value:
                logger.error(f"Queue integrity violation: {current.order_id} -> {next_order.order_id}")
                return False
        return True

    async def create_order(self, order_id: str, description: str, priority: Optional[WorkOrderPriority] = WorkOrderPriority.MEDIUM) -> WorkOrder:
        """Create a new work order."""
        self.validate_order_id(order_id)
        
        if order_id in self.work_orders:
            logger.error(f"Work order {order_id} already exists")
            raise ValueError(f"Work order {order_id} already exists")

        if priority is None:
            logger.error("Priority cannot be None")
            raise ValueError("Priority cannot be None")

        work_order = WorkOrder(order_id=order_id, description=description, priority=priority)
        self.work_orders[order_id] = work_order
        self._add_to_queue(order_id)
        self._log_transaction(order_id, "created", {"priority": priority.name})
        return work_order

    async def assign_order(self, order_id: str, technician_id: str) -> bool:
        """Assign a work order to a technician."""
        if order_id not in self.work_orders:
            logger.error(f"Work order {order_id} not found")
            return False

        work_order = self.work_orders[order_id]
        if work_order.status != WorkOrderStatus.PENDING:
            logger.error(f"Work order {order_id} is not in pending status")
            return False

        work_order.assigned_technician = technician_id
        work_order.status = WorkOrderStatus.ASSIGNED
        self._log_transaction(order_id, "assigned", {"technician_id": technician_id})
        return True

    async def update_location(self, order_id: str, latitude: float, longitude: float) -> bool:
        """Update the location for a work order."""
        if order_id not in self.work_orders:
            logger.error(f"Work order {order_id} not found")
            return False

        try:
            location = Location(latitude=latitude, longitude=longitude)
            location.validate()
            
            work_order = self.work_orders[order_id]
            work_order.location = location
            self._log_transaction(order_id, "location_updated", 
                                {"latitude": latitude, "longitude": longitude})
            return True
        except ValueError as e:
            logger.error(f"Invalid location for work order {order_id}: {e}")
            return False

    def _add_to_queue(self, order_id: str):
        """Add a work order to the queue in priority order."""
        work_order = self.work_orders[order_id]
        
        # Find the correct position based on priority
        for i, queued_id in enumerate(self.queue):
            queued_order = self.work_orders[queued_id]
            if work_order.priority.value > queued_order.priority.value:
                self.queue.insert(i, order_id)
                self._log_transaction(order_id, "queue_inserted", {"position": i})
                return

        # If not inserted, append to the end
        self.queue.append(order_id)
        self._log_transaction(order_id, "queue_appended", {"position": len(self.queue) - 1}) 

    async def start_order(self, order_id: str) -> bool:
        """Start a work order."""
        if order_id not in self.work_orders:
            logger.error(f"Work order {order_id} not found")
            return False

        work_order = self.work_orders[order_id]
        if work_order.status != WorkOrderStatus.ASSIGNED:
            logger.error(f"Work order {order_id} is not in assigned status")
            return False

        work_order.status = WorkOrderStatus.IN_PROGRESS
        work_order.started_at = datetime.now()
        self._log_transaction(order_id, "started", {"started_at": work_order.started_at.isoformat()})
        return True

    async def complete_order(self, order_id: str, notes: Optional[str] = None) -> bool:
        """Complete a work order."""
        if order_id not in self.work_orders:
            logger.error(f"Work order {order_id} not found")
            return False

        work_order = self.work_orders[order_id]
        if work_order.status != WorkOrderStatus.IN_PROGRESS:
            logger.error(f"Work order {order_id} is not in progress")
            return False

        work_order.status = WorkOrderStatus.COMPLETED
        work_order.completed_at = datetime.now()
        
        if notes:
            work_order.notes.append(WorkOrderNote(
                timestamp=datetime.now(),
                content=notes,
                author=work_order.assigned_technician
            ))
            
        self._log_transaction(order_id, "completed", {
            "completed_at": work_order.completed_at.isoformat(),
            "notes": notes if notes else None
        })
        return True

    def get_queue(self) -> List[WorkOrder]:
        """Get the current work order queue."""
        return [self.work_orders[order_id] for order_id in self.queue]

    def get_order(self, order_id: str) -> Optional[WorkOrder]:
        """Get a work order by ID."""
        return self.work_orders.get(order_id)

    def validate_order_id(self, order_id: str) -> bool:
        """Validate a work order ID."""
        if not order_id or not isinstance(order_id, str):
            logger.error("Invalid order ID: must be a non-empty string")
            raise ValueError("Invalid order ID: must be a non-empty string")
        return True 