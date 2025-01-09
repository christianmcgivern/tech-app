# Step 10: Voice Agent Implementation

## Overview
This document details the implementation of a voice agent feature in the technician app, which allows technicians to interact with the system using voice commands. The voice agent specifically acts as a CCTV assistant, helping technicians manage their daily workflow. The implementation uses OpenAI's Realtime API with WebRTC for secure, low-latency voice communication.

## Technical Stack
- **Frontend**: React with TypeScript
- **State Management**: React hooks and custom store
- **Audio Processing**: WebAudio API with WebRTC
- **Communication**: WebRTC with DataChannel for events
- **Voice Processing**: OpenAI GPT-4o Realtime model
- **Database Integration**: PostgreSQL with FastAPI backend
- **Server Architecture**: Multi-server setup with dedicated WebSocket servers

## Server Architecture

### 1. Main Backend Server (`src/backend/main.py`)
- Handles core API endpoints
- Manages database operations
- Provides technician status and work order management
- Implements CORS middleware for secure cross-origin requests

### 2. Office WebSocket Server (`src/backend/office-server/main.py`)
- Manages real-time communication with office dashboard
- Handles notifications and status updates
- Runs on port 8000

### 3. Technician WebSocket Server (`src/backend/technician-server/main.py`)
- Manages real-time communication with technician app
- Handles voice agent WebSocket connections
- Runs on port 8001

## Voice Agent Implementation

### 1. Voice Agent Service (`src/frontend/technician-app/src/services/voiceAgent.ts`)

#### Core Components
- WebRTC connection management
- Audio streaming with PCM16 format
- Database integration through API calls
- Function call handling for workflow operations

#### Class Structure
```typescript
export class VoiceAgent extends EventEmitter {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private technicianId: string | null = null;
  private technicianName: string | null = null;
  private isActive: boolean = false;

  constructor() {
    super();
    this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
  }

  // ... methods for WebRTC setup and audio handling
}
```

### 2. Database Integration

The voice agent interacts with the database through several API endpoints:

#### Technician Status
```typescript
async getTechnicianStatus(technicianId: string) {
  const response = await api.getTechnicianStatus(technicianId);
  return {
    status: response.status,
    truck: response.truck,
    workOrders: response.work_orders
  };
}
```

#### Work Order Management
```typescript
async getWorkOrders(technicianId: string) {
  const response = await api.getTechnicianWorkOrders(technicianId);
  return response;
}

async updateWorkOrderNotes(orderId: number, notes: string, alertOffice: boolean) {
  return await api.updateWorkOrderNotes(orderId, notes, alertOffice);
}
```

### 3. CCTV Assistant Workflow

The voice agent follows a specific workflow for CCTV technicians:

1. **Initial Greeting**
   - Greets technician by name
   - Retrieves current status from database
   - Asks if they're ready to start their day

2. **Work Order Management**
   ```typescript
   const workflowInstructions = `
     1. First, use get_technician_status to get the current status of the technician
     2. Based on the status:
        - If they have active work orders, summarize them and ask if they're ready to continue
        - If they have no active work orders, use get_work_orders to fetch pending work orders
     3. For each work order:
        - Ask if they're ready to travel to the jobsite
        - Track travel status with start_travel and end_travel
        - Guide through job completion
     4. After each job, ask about the next work order
     5. Monitor inventory with check_inventory
   `;
   ```

3. **Job Completion Flow**
   - Confirms completion status
   - Records notes and issues
   - Updates inventory if materials were used
   - Creates notifications if needed

### 4. Security Implementation

1. **API Security**
   - Ephemeral token generation for OpenAI API
   - Secure WebRTC signaling through backend proxy
   - CORS configuration for secure cross-origin requests

2. **Data Channel Security**
   ```typescript
   private setupDataChannel() {
     this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
       ordered: true,
       protocol: 'json'
     });
     this.dataChannel.onopen = () => this.initializeSession();
     this.dataChannel.onmessage = this.handleWebSocketMessage;
   }
   ```

### 5. Error Handling

1. **Connection Management**
   ```typescript
   private handleConnectionError(error: Error) {
     console.error('Connection error:', error);
     this.emit('error', error);
     this.cleanup();
   }
   ```

2. **Session Recovery**
   - Automatic reconnection on failure
   - State preservation during reconnection
   - Error reporting to backend

### Best Practices

1. **Resource Management**
   - Proper cleanup of WebRTC connections
   - Audio context lifecycle management
   - Memory leak prevention

2. **Performance Optimization**
   - Efficient audio streaming
   - Optimized database queries
   - Proper caching strategies

3. **User Experience**
   - Clear voice feedback
   - Error recovery guidance
   - Context-aware responses

## Configuration

### 1. Environment Variables
```env
VITE_API_URL=http://localhost:3000/api
VITE_WS_URL=ws://localhost:8001
OPENAI_API_KEY=your-api-key
```

### 2. Server Setup
```bash
# Start all servers using the main script
./start_all_servers.sh

# Or start individual servers using their respective scripts
./startup_scripts/start_main_api.sh        # Main backend server
./startup_scripts/start_office_ws.sh       # Office WebSocket server
./startup_scripts/start_tech_ws.sh         # Technician WebSocket server
./startup_scripts/start_office_frontend.sh  # Office Frontend
./startup_scripts/start_tech_frontend.sh    # Technician Frontend
```

### 3. Frontend Development
```bash
cd src/frontend/technician-app && npm run dev
```

### Voice Agent Workflow Management

The voice agent now includes comprehensive workflow state management:

```typescript
// Session initialization with workflow instructions
private async initializeSession() {
  const sessionConfig = {
    type: "session.update",
    session: {
      input_audio_format: "pcm16",
      output_audio_format: "pcm16",
      instructions: `You are a voice assistant for technician ${this.technicianName} (ID: ${this.technicianId}) in the field. 
      
First, use get_technician_status to get their current workflow state and work orders.

Based on their workflow_state:

1. If CLOCKED_IN:
   - Get their first work order using get_work_orders
   - Ask if they're ready to travel to first job
   - When confirmed:
     * Use start_travel
     * Update state to TRAVELING_TO_FIRST_JOB

2. If TRAVELING_TO_FIRST_JOB or TRAVELING_TO_NEXT_JOB:
   - Check current_work_order_id to know which job they're traveling to
   - When they say "I've arrived":
     * Use end_travel
     * Update state to AT_JOBSITE

3. If AT_JOBSITE:
   - Ask if they're ready to start work
   - When confirmed:
     * Use start_job
     * Update state to WORKING_ON_JOB

4. If WORKING_ON_JOB:
   - If they indicate job is complete:
     * Use end_job
     * Update state to JOB_COMPLETED
     * Guide them through completion questions:
       - Was everything completed?
       - Are there any notes? (use update_work_order_notes)
       - Was anything broken?
       - Was extra material used? (use check_inventory and update_inventory if needed)
       - Should the office be alerted? (use create_manual_notification if yes)

5. If JOB_COMPLETED:
   - Check if there are more work orders (next_work_order_id)
   - If yes:
     * Update state to TRAVELING_TO_NEXT_JOB
     * Update current_work_order_id to next_work_order_id
     * Get new next_work_order_id
   - If no:
     * Ask if they're ready to return to office
     * Update state to TRAVELING_TO_OFFICE

6. If TRAVELING_TO_OFFICE:
   - When they arrive, ask if they're ready to end their day
   - If yes:
     * Update state to DAY_COMPLETED
     * Trigger clock-out

Always maintain awareness of:
- current_work_order_id: The job they're currently traveling to or working on
- next_work_order_id: The next job in their queue

For any state transition:
1. First call the appropriate function (start_travel, end_travel, start_job, end_job)
2. Then update the workflow state using updateWorkflowState
3. Confirm the state change was successful before proceeding`,
      tools: tools
    }
  };
  this.dataChannel.send(JSON.stringify(sessionConfig));
}

// Function call handling with workflow state updates
private async handleFunctionCall() {
  if (!this.functionCall || !this.dataChannel) return;

  const functionName = this.functionCall.name;
  const args = JSON.parse(this.functionCallArgs);
  
  try {
    let result;
    switch (functionName) {
      case 'start_travel':
        result = await functionMap[functionName](args.work_order_id, args.technician_id);
        break;
      case 'end_travel':
        result = await functionMap[functionName](args.work_order_id, args.technician_id);
        break;
      case 'start_job':
        result = await functionMap[functionName](args.work_order_id, args.technician_id);
        break;
      case 'end_job':
        result = await functionMap[functionName](args.work_order_id, args.technician_id, args.notes);
        break;
      case 'update_workflow_state':
        result = await functionMap[functionName](
          args.technician_id,
          args.state,
          args.current_work_order_id,
          args.next_work_order_id
        );
        break;
      // ... other function cases
    }

    // Send function output back to assistant
    this.dataChannel.send(JSON.stringify({
      type: "conversation.item.create",
      item: {
        type: "function_call_output",
        call_id: this.functionCall.call_id,
        output: JSON.stringify(result)
      }
    }));
  } catch (error) {
    console.error(`Error executing function ${functionName}:`, error);
  }
}

### State Recovery on Reconnection

The voice agent implements robust state recovery when reconnecting:

```typescript
public async connect() {
  try {
    await this.setupWebRTC();
    
    // Get current technician status and workflow state
    const status = await api.getTechnicianStatus(this.technicianId);
    
    // Initialize session with current state
    await this.initializeSession();
    
    // Resume from last known state
    if (status.workflow_state) {
      this.dataChannel.send(JSON.stringify({
        type: "conversation.item.create",
        item: {
          type: "text",
          text: `Resuming from state: ${status.workflow_state}. Current work order: ${status.current_work_order_id}`
        }
      }));
    }
  } catch (error) {
    console.error('Error connecting:', error);
    this.cleanup();
    throw error;
  }
}

### Error Handling and State Validation

The voice agent includes comprehensive error handling for state transitions:

```typescript
private async validateStateTransition(
  currentState: WorkflowState,
  newState: WorkflowState
): Promise<boolean> {
  const validTransitions: { [key in WorkflowState]: WorkflowState[] } = {
    'CLOCKED_IN': ['TRAVELING_TO_FIRST_JOB'],
    'TRAVELING_TO_FIRST_JOB': ['AT_JOBSITE'],
    'AT_JOBSITE': ['WORKING_ON_JOB'],
    'WORKING_ON_JOB': ['JOB_COMPLETED'],
    'JOB_COMPLETED': ['TRAVELING_TO_NEXT_JOB', 'TRAVELING_TO_OFFICE'],
    'TRAVELING_TO_NEXT_JOB': ['AT_JOBSITE'],
    'TRAVELING_TO_OFFICE': ['DAY_COMPLETED'],
    'DAY_COMPLETED': []
  };

  return validTransitions[currentState].includes(newState);
}
```