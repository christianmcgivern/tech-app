from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Set
import json
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager for technicians
class TechnicianConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.technician_locations: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, technician_id: str):
        await websocket.accept()
        self.active_connections[technician_id] = websocket

    def disconnect(self, technician_id: str):
        if technician_id in self.active_connections:
            del self.active_connections[technician_id]
        if technician_id in self.technician_locations:
            del self.technician_locations[technician_id]

    async def update_location(self, technician_id: str, location: dict):
        self.technician_locations[technician_id] = location
        # Broadcast location update to relevant parties

    async def send_work_order(self, technician_id: str, work_order: dict):
        if technician_id in self.active_connections:
            await self.active_connections[technician_id].send_json({
                "type": "work_order",
                "data": work_order
            })

manager = TechnicianConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Technician WebSocket server...")
    yield
    # Shutdown
    logger.info("Shutting down Technician WebSocket server...")
    # Clean up any active connections
    for technician_id in list(manager.active_connections.keys()):
        await manager.active_connections[technician_id].close()
    manager.active_connections.clear()
    manager.technician_locations.clear()

app = FastAPI(title="Technician Mobile Platform API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on mobile app requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/technician/{technician_id}")
async def websocket_endpoint(websocket: WebSocket, technician_id: str):
    await manager.connect(websocket, technician_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "location_update":
                await manager.update_location(technician_id, message["data"])
            elif message["type"] == "work_order_update":
                # Process work order update and notify relevant parties
                pass
            elif message["type"] == "voice_data":
                # Process voice data
                pass
    except WebSocketDisconnect:
        manager.disconnect(technician_id)

@app.get("/")
async def root():
    return {"message": "Technician Mobile Platform API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        workers=1,
        log_level="info",
        reload=False,
        access_log=True
    ) 