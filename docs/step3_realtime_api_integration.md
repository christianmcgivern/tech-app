# Step 3: Realtime API Integration

## Overview
This document details the integration of OpenAI's Realtime API for voice communication in the technician app, using WebRTC for secure, low-latency audio streaming.

## Implementation Details

### Backend Proxy
The backend proxy is implemented in the office WebSocket server (`src/backend/office-server/main.py`):
```python
@app.post("/api/voice/realtime/connect")
async def connect_realtime(request: dict):
    """Handle WebRTC signaling for voice agent connection"""
    try:
        sdp = request.get('sdp')
        model = request.get('model')
        
        if not sdp or not model:
            raise HTTPException(status_code=400, detail="Missing sdp or model in request")
        
        url = f"https://api.openai.com/v1/realtime?model={model}"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/sdp",
            "OpenAI-Beta": "realtime=v1"
        }
        
        logger.debug(f"Making request to OpenAI: URL={url}, Headers={headers}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=sdp)
            
            logger.debug(f"OpenAI Response: Status={response.status_code}, Body={response.text}")
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to connect to OpenAI: {response.text}"
                )
            
            # For 201 Created response, return the SDP answer
            if response.status_code == 201:
                return {"sdp": response.text}
            
            # For 200 OK response, parse JSON and return SDP
            data = response.json()
            return {"sdp": data.get("sdp", response.text)}
    except Exception as e:
        logger.error(f"Error in connect_realtime: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend WebRTC Client
The `VoiceAgent` class in `src/frontend/technician-app/src/services/voiceAgent.ts` provides:

#### Core Components
```typescript
export class VoiceAgent extends EventEmitter {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private isActive: boolean = false;
  private functionCall: FunctionCall | null = null;
  private technicianId: string | null = null;
  private technicianName: string | null = null;

  constructor() {
    super();
    this.audioContext = new AudioContext();
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/voice/realtime';
    this.model = 'gpt-4o-realtime-preview-2024-12-17';
    this.audioElement = document.createElement('audio');
    this.audioElement.autoplay = true;
  }
}
```

#### Connection Management
1. **WebRTC Setup**
   - Create RTCPeerConnection with STUN server
   - Set up audio playback handlers
   - Get local media stream with specific audio configuration
   - Create data channel for events
   - Create and set local description (offer)
   - Send offer to backend proxy and get answer
   - Set remote description
   - Handle ICE connection state changes

2. **Audio Configuration**
```typescript
const mediaConfig = {
  audio: {
    sampleRate: 24000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
  }
};
```

3. **Session Initialization**
```typescript
private async initializeSession() {
  const sessionConfig = {
    type: "session.update",
    session: {
      input_audio_format: "pcm16",
      output_audio_format: "pcm16",
      language: "es",
      enable_voice_activity_detection: true,
      enable_direct_audio_output: true,
      instructions: `You are a voice assistant for technician ${this.technicianName}...`,
      tools: tools
    }
  };
  this.dataChannel.send(JSON.stringify(sessionConfig));
}
```

#### Message Handling
1. **WebSocket Message Types**
   - session.created/updated
   - input_audio_buffer events
   - conversation.item.created
   - response.created/done
   - response.output_item.added
   - response.audio_transcript.delta

2. **Function Call Handling**
```typescript
private async handleFunctionCall() {
  if (!this.functionCall || !this.dataChannel) return;

  const functionName = this.functionCall.name;
  const args = JSON.parse(this.functionCallArgs);
  
  try {
    let result;
    switch (functionName) {
      case 'get_work_orders':
        result = await functionMap[functionName](args.technician_id);
        break;
      // ... other function cases
    }

    // Send function output back to assistant
    this.dataChannel.send(JSON.stringify({
      type: "conversation.item.create",
      item: {
        type: "function_call_output",
        role: "system",
        output: JSON.stringify(result)
      }
    }));
  } catch (error) {
    // Handle and report errors
  }
}
```

#### Audio Processing
1. **Playback Management**
```typescript
private async playAudioDelta(base64Audio: string) {
  if (!this.audioContext) return;

  try {
    // Resume audio context if needed
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    // Decode and play audio
    const audioData = atob(base64Audio);
    const audioArray = new Uint8Array(audioData.length);
    for (let i = 0; i < audioData.length; i++) {
      audioArray[i] = audioData.charCodeAt(i);
    }

    const audioBuffer = await this.audioContext.decodeAudioData(audioArray.buffer);
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);
    source.start();
  } catch (error) {
    console.error('Error playing audio:', error);
  }
}
```

#### Resource Management
1. **Cleanup**
```typescript
private cleanup() {
  // Stop media streams
  if (this.mediaStream) {
    this.mediaStream.getTracks().forEach(track => track.stop());
  }
  
  // Close connections
  if (this.dataChannel) this.dataChannel.close();
  if (this.peerConnection) this.peerConnection.close();
  
  // Clean up audio
  if (this.audioElement) this.audioElement.srcObject = null;
  if (this.audioContext && this.audioContext.state !== 'closed') {
    this.audioContext.close();
  }
  
  // Reset state
  this.mediaStream = null;
  this.dataChannel = null;
  this.peerConnection = null;
  this.audioContext = null;
  this.isActive = false;
}
```

2. **Error Handling**
- Connection state monitoring
- Automatic cleanup on errors
- Detailed error logging
- Graceful disconnection

## Best Practices
1. **Resource Management**
   - Proper cleanup of WebRTC connections
   - Audio context lifecycle management
   - Memory leak prevention

2. **Error Handling**
   - Graceful degradation
   - Detailed error logging
   - Automatic recovery when possible

3. **Security**
   - Secure WebRTC configuration
   - Proper API key handling
   - Input validation

4. **Performance**
   - Efficient audio streaming
   - Proper resource cleanup
   - Connection state monitoring 