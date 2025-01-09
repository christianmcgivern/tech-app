# Step 4: Technician Workflow Implementation

## Overview
This document details the implementation of the technician workflow system, including work order management, technician session handling, and real-time status tracking.

## Components

### Technician Session
The `TechnicianSession` class in `src/core/technician.py` handles:
- Secure login/logout functionality
- Clock in/out management
- Real-time status tracking
- Current job tracking
- Shift time recording

### Status Management
```python
class TechnicianStatus(Enum):
    """
    Status Workflow:
    OFFLINE -> LOGGED_IN -> ON_DUTY -> ON_JOB
                                   -> ON_BREAK
                                   -> OFF_DUTY
    """
    OFFLINE = "offline"
    LOGGED_IN = "logged_in"
    ON_DUTY = "on_duty"
    ON_JOB = "on_job"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"

class WorkflowState(Enum):
    """
    Workflow State Transitions:
    CLOCKED_IN -> TRAVELING_TO_FIRST_JOB -> AT_JOBSITE -> WORKING_ON_JOB -> JOB_COMPLETED
                                                                         -> TRAVELING_TO_NEXT_JOB
                                                                         -> TRAVELING_TO_OFFICE
                                                                         -> DAY_COMPLETED
    """
    CLOCKED_IN = "CLOCKED_IN"
    TRAVELING_TO_FIRST_JOB = "TRAVELING_TO_FIRST_JOB"
    AT_JOBSITE = "AT_JOBSITE"
    WORKING_ON_JOB = "WORKING_ON_JOB"
    JOB_COMPLETED = "JOB_COMPLETED"
    TRAVELING_TO_NEXT_JOB = "TRAVELING_TO_NEXT_JOB"
    TRAVELING_TO_OFFICE = "TRAVELING_TO_OFFICE"
    DAY_COMPLETED = "DAY_COMPLETED"
```

### Workflow State Management
```python
@app.patch("/api/technicians/{technician_id}/workflow-state")
async def update_workflow_state(technician_id: int, state_update: WorkflowStateUpdate):
    """Update the workflow state for a technician's current clock-in record"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Verify the technician exists and is active
        cur.execute("SELECT id FROM technicians WHERE id = %s AND active = true", (technician_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Technician not found or inactive")
        
        # Only update non-locked records from today
        cur.execute("""
            UPDATE technician_clock_records
            SET workflow_state = %s::technician_workflow_state,
                current_work_order_id = %s,
                next_work_order_id = %s
            WHERE technician_id = %s 
            AND clock_in_time::date = CURRENT_DATE 
            AND clock_out_time IS NULL
            AND NOT is_locked
            RETURNING id, workflow_state, current_work_order_id, next_work_order_id
        """, (
            state_update.state,
            state_update.current_work_order_id,
            state_update.next_work_order_id,
            technician_id
        ))
        
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(
                status_code=400,
                detail="No active clock record found or record is locked"
            )
        
        return {
            "id": updated['id'],
            "workflow_state": updated['workflow_state'],
            "current_work_order_id": updated['current_work_order_id'],
            "next_work_order_id": updated['next_work_order_id'],
            "message": "Workflow state updated successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow state: {str(e)}")
    finally:
        conn.close()
```

### Frontend Integration
```typescript
export type WorkflowState = 
  | 'CLOCKED_IN'
  | 'TRAVELING_TO_FIRST_JOB'
  | 'AT_JOBSITE'
  | 'WORKING_ON_JOB'
  | 'JOB_COMPLETED'
  | 'TRAVELING_TO_NEXT_JOB'
  | 'TRAVELING_TO_OFFICE'
  | 'DAY_COMPLETED';

export interface ClockRecord {
    id: number;
    technician_id: number;
    truck_id: number;
    clock_in_time: string;
    clock_out_time: string | null;
    workflow_state: WorkflowState;
    current_work_order_id: number | null;
    next_work_order_id: number | null;
    is_locked: boolean;
}

// API function to update workflow state
async updateWorkflowState(
    technicianId: string,
    state: WorkflowState,
    currentWorkOrderId?: number,
    nextWorkOrderId?: number
) {
    const response = await axios.patch(
        `${API_URL}/technicians/${technicianId}/workflow-state`,
        {
            state,
            current_work_order_id: currentWorkOrderId,
            next_work_order_id: nextWorkOrderId
        }
    );
    return response.data;
}
```

### Voice Agent Integration
The voice agent has been updated to manage workflow states through the following steps:

1. **State Initialization**
   - Check current state on connection
   - Resume workflow from last known state
   - Maintain state across disconnections

2. **State Transitions**
   - Validate state changes
   - Update database records
   - Notify relevant systems

3. **Work Order Tracking**
   - Track current work order
   - Manage work order queue
   - Handle completion states

4. **Error Handling**
   - Validate state transitions
   - Handle invalid states
   - Maintain data consistency

## Implementation Details

### Session Management
```python
class TechnicianSession:
    """Manage technician sessions."""
    
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
```

## Error Handling
1. Session Errors
   - Invalid login attempts
   - Missing technician ID or truck assignment
   - Invalid status transitions
   - Clock in/out validation failures

2. Status Validation
   - Status transition validation
   - Shift time validation
   - Job assignment validation

## Best Practices
1. Validate all status transitions
2. Log all session events
3. Maintain session state consistency
4. Handle concurrent operations safely
5. Implement proper error boundaries
6. Track shift times accurately
7. Validate job assignments
8. Clean up resources properly

## Status
- [x] Session management
- [x] Status tracking
- [x] Clock in/out functionality
- [x] Error handling
- [x] Logging implementation
- [x] Status validation
- [ ] Analytics dashboard (planned)
- [ ] Performance metrics (planned)

## Next Steps
1. Implement analytics dashboard
2. Add performance metrics tracking
3. Enhance error reporting
4. Improve status transition validation
5. Add session analytics
6. Implement shift reports
