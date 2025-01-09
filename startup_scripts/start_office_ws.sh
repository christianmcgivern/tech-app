#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Office WebSocket Server..."

# Change to the backend directory
cd "$(dirname "$0")/../src/backend" || exit 1

# Start the office WebSocket server
uvicorn office-server.main:app --host 0.0.0.0 --port 8000 > ../../logs/office_ws.log 2>&1 