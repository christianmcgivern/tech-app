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