"""Technician session management and workflow logic."""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from ..utils.logging import setup_logger
from ..utils.config import load_config

logger = setup_logger(__name__)

class TechnicianStatus(Enum):
    """Possible statuses for a technician."""
    OFFLINE = "offline"
    LOGGED_IN = "logged_in"
    ON_DUTY = "on_duty"
    ON_JOB = "on_job"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"

class TechnicianSession:
    """Manages technician session and state."""

    def __init__(self):
        self.config = load_config()
        self.technician_id: Optional[str] = None
        self.truck_id: Optional[str] = None
        self.status: TechnicianStatus = TechnicianStatus.OFFLINE
        self.shift_start: Optional[datetime] = None
        self.shift_end: Optional[datetime] = None
        self.current_job_id: Optional[str] = None
        self.session_data: Dict[str, Any] = {}

    async def login(self, technician_id: str) -> bool:
        """Log in a technician."""
        try:
            # TODO: Implement actual authentication
            self.technician_id = technician_id
            self.status = TechnicianStatus.LOGGED_IN
            logger.info(f"Technician {technician_id} logged in")
            return True
        except Exception as e:
            logger.error(f"Login failed for technician {technician_id}: {e}")
            return False

    async def assign_truck(self, truck_id: str) -> bool:
        """Assign a truck to the technician."""
        if self.status == TechnicianStatus.OFFLINE:
            logger.error("Cannot assign truck: Technician not logged in")
            return False

        try:
            # TODO: Implement truck validation
            self.truck_id = truck_id
            logger.info(f"Truck {truck_id} assigned to technician {self.technician_id}")
            return True
        except Exception as e:
            logger.error(f"Truck assignment failed: {e}")
            return False

    async def clock_in(self) -> bool:
        """Clock in the technician for their shift."""
        if not self.technician_id or not self.truck_id:
            logger.error("Cannot clock in: Missing technician ID or truck assignment")
            return False

        try:
            self.shift_start = datetime.now()
            self.status = TechnicianStatus.ON_DUTY
            logger.info(f"Technician {self.technician_id} clocked in at {self.shift_start}")
            return True
        except Exception as e:
            logger.error(f"Clock in failed: {e}")
            return False

    async def clock_out(self) -> bool:
        """Clock out the technician from their shift."""
        if self.status not in [TechnicianStatus.ON_DUTY, TechnicianStatus.ON_BREAK]:
            logger.error("Cannot clock out: Invalid status")
            return False

        try:
            self.shift_end = datetime.now()
            self.status = TechnicianStatus.OFF_DUTY
            logger.info(f"Technician {self.technician_id} clocked out at {self.shift_end}")
            return True
        except Exception as e:
            logger.error(f"Clock out failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get the current technician status."""
        return {
            "technician_id": self.technician_id,
            "truck_id": self.truck_id,
            "status": self.status.value,
            "shift_start": self.shift_start.isoformat() if self.shift_start else None,
            "shift_end": self.shift_end.isoformat() if self.shift_end else None,
            "current_job_id": self.current_job_id
        } 