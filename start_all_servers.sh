#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to cleanup processes on script exit
cleanup() {
    echo "Cleaning up processes..."
    # Kill all related processes and their children
    pkill -9 -f "python.*main.py"
    pkill -9 -f "vite"
    pkill -9 -f "uvicorn"
    pkill -9 -f "node.*dev"
    pkill -9 -f "npm.*dev"
    
    # Kill any processes using our ports
    for port in 3000 8000 8001 5173 5178; do
        pid=$(lsof -t -i:$port)
        if [ ! -z "$pid" ]; then
            echo "Killing process $pid on port $port"
            kill -9 $pid 2>/dev/null || true
        fi
    done
    
    sleep 2
}

# Set up cleanup trap
trap cleanup EXIT

# Kill any existing processes
echo "Killing existing processes..."
cleanup

# Create .env file for database connection
echo "Setting up database connection..."
cat > .env << EOL
DB_NAME=tech_workflow_db
DB_USER=office_admin
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
EOL

# Make all startup scripts executable
chmod +x startup_scripts/*.sh

echo "Starting all servers..."

# Start each server in its own process
startup_scripts/start_main_api.sh &
sleep 5  # Wait for main API to be ready

startup_scripts/start_office_ws.sh &
startup_scripts/start_tech_ws.sh &
sleep 5  # Wait for WebSocket servers to be ready

startup_scripts/start_office_frontend.sh &
startup_scripts/start_tech_frontend.sh &

echo -e "\nServer Information:"
echo "Main API: http://localhost:3000"
echo "Office WebSocket: http://localhost:8000"
echo "Technician WebSocket: http://localhost:8001"
echo "Office Frontend: http://localhost:5173"
echo "Technician Frontend: http://localhost:5178"

echo -e "\nAll servers are starting. Check logs/ directory for detailed server logs."
echo "Press Ctrl+C to stop all servers."

# Wait for any process to exit
wait 