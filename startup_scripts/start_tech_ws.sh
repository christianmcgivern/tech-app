#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Technician WebSocket Server..."

# Change to the backend directory
cd "$(dirname "$0")/../src/backend" || exit 1

# Start the technician WebSocket server
uvicorn technician-server.main:app --host 0.0.0.0 --port 8001 > ../../logs/tech_ws.log 2>&1 