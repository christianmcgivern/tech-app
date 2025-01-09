# Step 6: Testing and Debugging

## Overview
This document outlines the testing and debugging process for the AI-Powered Technician Workflow System.

## Tasks

### 1. Unit Testing
- [ ] Develop unit tests for each module.
- [ ] Ensure coverage of all critical functions.

### 2. Integration Testing
- [ ] Test interactions between modules.
- [ ] Validate end-to-end functionality.

### 3. Performance Optimization
- [ ] Identify and resolve performance bottlenecks.
- [ ] Optimize resource usage.

### 4. Edge Case Handling
- [ ] Test and handle edge cases.
- [ ] Ensure robustness and reliability.

### 5. Voice Agent Testing and Debugging

#### Understanding the Logs
1. Server Logs (`logs/` directory):
   - Main API Server: `api-server.log`
   - Office WebSocket: `office-ws.log`
   - Technician WebSocket: `technician-ws.log`
   Each log follows the format:
   ```
   [TIMESTAMP] [LEVEL] [COMPONENT] Message
   ```

2. Voice Agent Console Logs:
   Connection Flow:
   ```
   Connecting to WebRTC...
   Got ephemeral token
   Created peer connection
   Got local media stream
   Adding track to peer connection: audio
   Created data channel
   ```

   Session Events:
   ```
   Session initialized
   Session created successfully
   Session updated successfully
   ```

   Audio Events:
   ```
   Speech started
   Speech stopped
   Audio buffer committed
   ```

   Response Flow:
   ```
   Conversation item created of type: [type]
   Response created with ID: [id]
   Response output item added with content types: [types]
   Response completed
   ```

   Error Messages:
   ```
   Server error: [error message]
   Error executing function [name]: [details]
   ```

3. Common Log Patterns:
   - Successful Flow:
     ```
     WebRTC connected
     Session initialized
     Speech started/stopped
     Response with content
     ```
   
   - Authentication Issues:
     ```
     Server error: Invalid API key
     Server error: Insufficient quota
     ```
   
   - Audio Problems:
     ```
     Error playing audio: [details]
     No audio context available
     ```

4. Debugging with Logs:
   - Check connection sequence in order
   - Verify session initialization
   - Monitor speech detection events
   - Track response generation
   - Identify error patterns

#### Connection Flow
1. Check WebRTC connection establishment:
   - [ ] WebRTC connection creation
   - [ ] ICE candidate gathering
   - [ ] Data channel opening
   - [ ] Audio track addition

2. Monitor session initialization:
   - [ ] Session creation
   - [ ] Session updates
   - [ ] Tool registration

3. Audio handling:
   - [ ] Input audio buffer management
   - [ ] Speech detection events
   - [ ] Audio format compatibility

#### Common Issues and Solutions
1. API Authentication:
   - Check OpenAI API key validity
   - Verify quota and billing status
   - Monitor rate limits

2. WebRTC Issues:
   - ICE connection failures
   - Audio track problems
   - Data channel connectivity

3. Voice Recognition:
   - Speech detection sensitivity
   - Audio quality issues
   - Transcription accuracy

#### Debugging Steps
1. Enable detailed logging:
   ```typescript
   // In voiceAgent.ts
   console.log('Full conversation item:', message.conversation_item);
   console.log('Full response:', message.response);
   console.log('Response completed. Full message:', JSON.stringify(message));
   ```

2. Monitor WebSocket messages:
   - Session events
   - Conversation items
   - Response content
   - Error messages

3. Check audio pipeline:
   - Input device selection
   - Audio format conversion
   - Buffer management
   - Playback issues

4. Tool execution:
   - Function call parsing
   - Argument validation
   - Response handling
   - Error recovery

#### Testing Checklist
- [ ] Test with different audio inputs
- [ ] Verify tool execution flow
- [ ] Check error handling and recovery
- [ ] Validate session management
- [ ] Monitor resource usage
- [ ] Test concurrent connections
- [ ] Verify cleanup on disconnect

## Next Steps
After completing testing and debugging:
1. Prepare for deployment.
2. Finalize documentation and training materials.

## Notes
- Use pytest for testing.
- Implement logging for test results and errors.
- Monitor WebSocket connections in browser dev tools.
- Use browser's audio debugger for media issues.
- Keep track of OpenAI API quotas and usage. 