#!/bin/bash

# Start office server
echo "Starting Office Platform Server..."
uvicorn src.backend.office-server.main:app --reload --port 8000 &

# Start technician server
echo "Starting Technician Platform Server..."
uvicorn src.backend.technician-server.main:app --reload --port 8001 &

# Wait for both servers
wait 