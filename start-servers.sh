#!/bin/bash

echo "Starting servers..."

# Make scripts executable
chmod +x startup_scripts/*.sh

# Start each server in its own process group
./startup_scripts/start_main_api.sh &
./startup_scripts/start_office_ws.sh &
./startup_scripts/start_tech_ws.sh &
./startup_scripts/start_office_frontend.sh &
./startup_scripts/start_tech_frontend.sh &

echo "All servers started!"
echo "Main API: http://localhost:3000"
echo "Office WebSocket: http://localhost:8000"
echo "Technician WebSocket: http://localhost:8001"
echo "Office Frontend: http://localhost:5173"
echo "Technician Frontend: http://localhost:5178"
echo "Use 'ps aux | grep python' or 'ps aux | grep node' to find and kill processes" 