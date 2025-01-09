from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Set
import json
import logging
from contextlib import asynccontextmanager
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def broadcast_to_users(self, message: dict, user_ids: Set[str]):
        for user_id in user_ids:
            if user_id in self.active_connections:
                for connection in self.active_connections[user_id]:
                    await connection.send_json(message)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Office WebSocket server...")
    yield
    # Shutdown
    logger.info("Shutting down Office WebSocket server...")
    # Clean up any active connections
    for client_id in list(manager.active_connections.keys()):
        for connection in list(manager.active_connections[client_id]):
            await connection.close()
        manager.active_connections[client_id].clear()
    manager.active_connections.clear()

app = FastAPI(title="Office Staff Platform API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", 
                  "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", 
                  "http://localhost:5179", "http://localhost:5180"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process received data and broadcast updates
            message = json.loads(data)
            await manager.broadcast_to_users(
                message,
                {client_id}  # Add other relevant user IDs based on message type
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)

@app.get("/")
async def root():
    return {"message": "Office Staff Platform API"}

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Voice agent routes
@app.post("/api/voice/realtime/token")
async def get_ephemeral_token():
    """Generate an ephemeral token for voice agent WebRTC connection"""
    try:
        url = "https://api.openai.com/v1/realtime/sessions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "realtime=v1"
        }
        
        data = {
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "voice": "alloy"
        }
        
        logger.debug(f"Making request to OpenAI: URL={url}, Headers={headers}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            
            logger.debug(f"OpenAI Response: Status={response.status_code}, Body={response.text}")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get ephemeral token: {response.text}"
                )
            
            data = response.json()
            return {
                "token": data["client_secret"]["value"],
                "expires_at": data["client_secret"]["expires_at"]
            }
    except Exception as e:
        logger.error(f"Error in get_ephemeral_token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        reload=False,
        access_log=True
    ) 