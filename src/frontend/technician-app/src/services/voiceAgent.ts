import { useTechnicianStore } from '../store/technicianStore';
import { tools, functionMap } from './voiceAgentTools';

// Simple browser-compatible EventEmitter
class EventEmitter {
  private listeners: { [key: string]: Function[] } = {};

  on(event: string, callback: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event: string, ...args: any[]) {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(callback => callback(...args));
  }

  removeListener(event: string, callback: Function) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }
}

interface VoiceAgentConfig {
  modalities: string[];
  instructions: string;
  voice: string;
  input_audio_format: string;
  output_audio_format: string;
  turn_detection: {
    type: string;
    threshold: number;
    prefix_padding_ms: number;
    silence_duration_ms: number;
  };
  tools: any[];
}

interface FunctionCall {
  name: string;
  arguments: string;
  call_id?: string;
}

export class VoiceAgent extends EventEmitter {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private isActive: boolean = false;
  private functionCall: FunctionCall | null = null;
  private functionCallArgs: string = '';
  private functionCallArgumentsBuffer: string = '';
  private baseUrl: string;
  private model: string;
  private technicianId: string | null = null;
  private technicianName: string | null = null;
  private hasActiveResponse: boolean = false;

  constructor() {
    super();
    this.audioContext = new AudioContext();
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/voice/realtime';
    this.model = 'gpt-4o-realtime-preview-2024-12-17';
    this.audioElement = document.createElement('audio');
    this.audioElement.autoplay = true;
  }

  private async ensureAudioContext() {
    if (!this.audioContext || this.audioContext.state === 'closed') {
      this.audioContext = new AudioContext();
    }
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
  }

  public setTechnicianInfo(id: string, name: string) {
    this.technicianId = id;
    this.technicianName = name;
  }

  public async connect() {
    if (this.peerConnection) {
      console.log('WebRTC connection already exists');
      return;
    }

    try {
      console.log('Connecting to WebRTC...');
      
      // First, get an ephemeral token from our backend
      const tokenResponse = await fetch(`${this.baseUrl}/token`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors'
      });

      if (!tokenResponse.ok) {
        const errorText = await tokenResponse.text();
        console.error('Failed to get ephemeral token:', errorText);
        throw new Error(`Failed to get ephemeral token: ${errorText}`);
      }

      const { token } = await tokenResponse.json();
      console.log('Got ephemeral token');
      
      // Create peer connection with STUN/TURN servers
      this.peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' }
        ]
      });
      console.log('Created peer connection');

      // Set up audio playback
      this.peerConnection.ontrack = (e) => {
        console.log('Received remote track');
        if (this.audioElement) {
          this.audioElement.srcObject = e.streams[0];
          this.audioElement.play().catch(error => {
            console.error('Error playing audio:', error);
          });
        }
      };

      // Add local audio track with proper configuration
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 24000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          }
        });
        console.log('Got local media stream');
        
        this.mediaStream.getTracks().forEach(track => {
          console.log('Adding track to peer connection:', track.kind);
          this.peerConnection?.addTrack(track, this.mediaStream!);
        });
      } catch (mediaError) {
        console.error('Error getting media stream:', mediaError);
        throw mediaError;
      }

      // Set up data channel for events
      this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
        ordered: true
      });
      console.log('Created data channel');

      this.dataChannel.onopen = () => {
        console.log('Data channel opened');
        this.emit('datachannel_open');
        this.initializeSession().then(() => {
          // Immediately request initial status after initialization
          if (this.dataChannel && this.technicianId) {
            console.log('Requesting initial technician status...');
            this.dataChannel.send(JSON.stringify({
              type: "response.create",
              response: {
                modalities: ["text", "audio"]
              }
            }));
          }
        }).catch(error => {
          console.error('Error initializing session:', error);
          this.cleanup();
          this.emit('error', error);
        });
      };
      this.dataChannel.onclose = () => {
        console.log('Data channel closed');
        this.emit('datachannel_close');
      };
      this.dataChannel.onerror = (error) => {
        console.error('Data channel error:', error);
        this.emit('datachannel_error', error);
      };
      this.dataChannel.onmessage = this.handleWebSocketMessage.bind(this);

      // Create and set local description
      try {
        const offer = await this.peerConnection.createOffer({
          offerToReceiveAudio: true
        });
        console.log('Created offer');
        await this.peerConnection.setLocalDescription(offer);
        console.log('Set local description');

        // Get answer from server through our backend proxy
        const response = await fetch(`${this.baseUrl}/connect`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          mode: 'cors',
          body: JSON.stringify({
            sdp: offer.sdp,
            model: this.model
          })
        });

        const responseData = await response.json();
        console.log('Got SDP answer from server');

        // Set remote description
        const answer = {
          type: 'answer' as RTCSdpType,
          sdp: responseData.sdp
        };
        await this.peerConnection.setRemoteDescription(answer);
        console.log('Set remote description');
      } catch (sdpError) {
        console.error('Error in SDP exchange:', sdpError);
        throw sdpError;
      }

      // Set up connection state handling
      this.peerConnection.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', this.peerConnection?.iceConnectionState);
        if (this.peerConnection?.iceConnectionState === 'disconnected') {
          this.handleDisconnect();
        }
      };

      this.isActive = true;
      console.log('WebRTC connected');
      this.emit('connected');
    } catch (error) {
      console.error('Error connecting to WebRTC:', error);
      this.cleanup();
      throw error;
    }
  }

  private async initializeSession() {
    if (!this.dataChannel) {
      console.error('No data channel available');
      throw new Error('No data channel available');
    }

    if (this.dataChannel.readyState !== 'open') {
      console.error('Data channel is not open');
      throw new Error('Data channel is not open');
    }

    if (!this.technicianId || !this.technicianName) {
      console.error('Technician information not set');
      throw new Error('Technician information not set');
    }

    try {
      console.log('Initializing session...');
      const sessionConfig = {
        type: "session.update",
        session: {
          input_audio_format: "pcm16",
          output_audio_format: "pcm16",
          modalities: ["text", "audio"],
          voice: "alloy",
          temperature: 0.8,
          max_response_output_tokens: "inf",
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
3. Confirm the state change was successful before proceeding

If the connection is lost or browser is closed, when reconnecting:
1. Get the current state using get_technician_status
2. Resume from that exact point in the workflow
3. Provide a brief reminder of what they were doing`,
          tools: tools
        }
      };
      this.dataChannel.send(JSON.stringify(sessionConfig));
      console.log('Session initialized');
    } catch (error) {
      console.error('Error initializing session:', error);
      throw error;
    }
  }

  private async handleWebSocketMessage(event: MessageEvent) {
    try {
      const message = JSON.parse(event.data);
      console.log('Received message:', message.type);

      switch (message.type) {
        case 'session.created':
          console.log('Session created successfully');
          break;
        case 'session.updated':
          console.log('Session updated successfully');
          break;
        case 'error':
          if (message.error?.message?.includes('already has an active response')) {
            console.log('Ignoring duplicate response request');
            // Don't set hasActiveResponse here, as it might be a stale request
            break;
          }
          console.error('Server error:', message.error?.message || 'Unknown error');
          this.emit('error', new Error(message.error?.message || 'Unknown error'));
          break;
        case 'input_audio_buffer.speech_started':
          console.log('Speech started');
          this.emit('speech_started');
          break;
        case 'input_audio_buffer.speech_stopped':
          console.log('Speech stopped');
          this.emit('speech_stopped');
          break;
        case 'input_audio_buffer.committed':
          console.log('Audio buffer committed');
          if (this.dataChannel && !this.hasActiveResponse) {
            console.log('Requesting response after audio commit');
            this.hasActiveResponse = true;
            this.dataChannel.send(JSON.stringify({
              type: "response.create",
              response: {
                modalities: ["text", "audio"]
              }
            }));
          }
          break;
        case 'response.created':
          console.log('Full response:', message.response);
          console.log('Response created with ID:', message.response?.id || 'unknown');
          this.hasActiveResponse = true;
          break;
        case 'response.function_call.started':
          this.functionCallArgumentsBuffer = '';
          break;
        case 'response.function_call_arguments.delta':
          this.functionCallArgumentsBuffer += message.delta;
          break;
        case 'response.function_call_arguments.done':
          console.log('Function call arguments completed:', message.name, this.functionCallArgumentsBuffer);
          this.functionCall = {
            name: message.name,
            arguments: this.functionCallArgumentsBuffer,
            call_id: message.call_id
          };
          this.functionCallArgs = this.functionCallArgumentsBuffer;
          this.functionCallArgumentsBuffer = '';
          await this.handleFunctionCall();
          break;
        case 'response.output_item.added':
          if (message.output_item?.content) {
            console.log('Response output item added with content types:', 
              message.output_item.content.map((c: any) => c.type).join(', '));
            this.handleResponseContent(message.output_item.content);
          }
          break;
        case 'response.done':
          console.log('Response completed. Full message:', JSON.stringify(message));
          
          // Handle different response completion scenarios
          if (message.response?.status === 'cancelled' && 
              message.response?.status_details?.reason === 'turn_detected') {
            // Turn detected, just reset state
            this.hasActiveResponse = false;
          } else if (message.response?.status === 'failed' && 
                    message.response?.status_details?.error?.code === 'rate_limit_exceeded') {
            // Rate limit hit, wait before resetting
            setTimeout(() => {
              this.hasActiveResponse = false;
            }, 5000); // Wait 5 seconds before allowing new responses
          } else {
            // Normal completion
            this.hasActiveResponse = false;
          }
          
          this.emit('response_done');
          break;
        default:
          console.log('Received message of type:', message.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      this.emit('error', error);
    }
  }

  private handleResponseContent(content: any[]) {
    if (!Array.isArray(content)) return;

    content.forEach(item => {
      switch (item.type) {
        case 'text':
          this.emit('text', item.text);
          break;
        case 'audio':
          this.playAudioDelta(item.audio);
          break;
        case 'function_call':
          this.functionCall = {
            name: item.function_call.name,
            arguments: item.function_call.arguments
          };
          this.functionCallArgs = item.function_call.arguments;
          this.handleFunctionCall();
          break;
        default:
          console.log('Unhandled content type:', item.type);
      }
    });
  }

  private async handleFunctionCall() {
    if (!this.functionCall || !this.dataChannel) return;

    const functionName = this.functionCall.name;
    console.log(`Executing function: ${functionName} with args: ${this.functionCallArgs}`);

    try {
      const args = this.functionCallArgs ? JSON.parse(this.functionCallArgs) : {};
      
      if (!(functionName in functionMap)) {
        throw new Error(`Unknown function: ${functionName}`);
      }

      let result;
      switch (functionName) {
        case 'get_technician_status':
          result = await functionMap[functionName](args.technician_id);
          break;
        case 'get_work_orders':
          result = await functionMap[functionName](args.technician_id);
          break;
        case 'start_travel':
          result = await functionMap[functionName](args.work_order_id, args.technician_id);
          break;
        case 'end_travel':
          result = await functionMap[functionName](args.work_order_id, args.technician_id);
          break;
        case 'update_work_order_notes':
          result = await functionMap[functionName](args.work_order_id, args.notes, args.alert_office);
          break;
        case 'check_inventory':
          result = await functionMap[functionName](args.truck_id);
          break;
        case 'update_inventory':
          result = await functionMap[functionName](args.truck_id, args.item_id, args.quantity);
          break;
        case 'create_manual_notification':
          result = await functionMap[functionName](args);
          break;
        case 'start_job':
          result = await functionMap[functionName](args.work_order_id, args.technician_id);
          break;
        case 'end_job':
          result = await functionMap[functionName](args.work_order_id, args.technician_id, args.notes);
          break;
        default:
          throw new Error(`Unknown function: ${functionName}`);
      }

      console.log(`Function ${functionName} returned result:`, result);

      // Send function output back to the assistant
      if (this.dataChannel && this.dataChannel.readyState === 'open') {
        this.dataChannel.send(JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "function_call_output",
            call_id: this.functionCall.call_id,
            output: JSON.stringify(result)
          }
        }));

        // Let the current response complete before requesting a new one
        await new Promise(resolve => setTimeout(resolve, 500));
      }

    } catch (error) {
      console.error(`Error executing function ${functionName}:`, error);
      
      if (this.dataChannel && this.dataChannel.readyState === 'open') {
        this.dataChannel.send(JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "function_call_output",
            call_id: this.functionCall.call_id,
            output: JSON.stringify({ 
              error: `Error executing ${functionName}: ${error instanceof Error ? error.message : 'Unknown error'}` 
            })
          }
        }));
      }
    }

    // Reset function call state
    this.functionCall = null;
    this.functionCallArgs = "";
    this.functionCallArgumentsBuffer = "";
  }

  private async playAudioDelta(base64Audio: string) {
    try {
      await this.ensureAudioContext();
      
      if (!this.audioContext) {
        console.error('No audio context available');
        return;
      }

      // Decode base64 to array buffer
      const audioData = atob(base64Audio);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }

      // Create and play audio buffer
      const audioBuffer = await this.audioContext.decodeAudioData(audioArray.buffer);
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);
      source.start();
      console.log('Playing audio chunk, duration:', audioBuffer.duration);
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  }

  private handleDisconnect() {
    console.log('Connection lost, cleaning up...');
    this.isActive = false;
    this.cleanup();
    this.emit('disconnected');
  }

  private cleanup() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
    }
    if (this.dataChannel) {
      this.dataChannel.close();
    }
    if (this.peerConnection) {
      this.peerConnection.close();
    }
    if (this.audioElement) {
      this.audioElement.srcObject = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    this.mediaStream = null;
    this.dataChannel = null;
    this.peerConnection = null;
    this.audioContext = null;
    this.isActive = false;
    this.hasActiveResponse = false;
  }

  public disconnect() {
    console.log('Disconnecting voice agent...');
    this.handleDisconnect();
  }

  public isConnected(): boolean {
    return this.isActive && 
           this.peerConnection?.connectionState === 'connected' &&
           this.dataChannel?.readyState === 'open';
  }

  public async start() {
    if (this.isActive) {
      console.log('Voice agent is already active');
      return;
    }

    try {
      await this.connect();
      console.log('Voice agent started successfully');
    } catch (error) {
      console.error('Error starting voice agent:', error);
      this.cleanup();
      throw error;
    }
  }

  public stop() {
    console.log('Stopping voice agent...');
    this.disconnect();
    console.log('Voice agent stopped');
  }
}

export const voiceAgent = new VoiceAgent(); 