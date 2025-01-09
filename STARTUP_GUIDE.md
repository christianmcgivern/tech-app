# Server Startup Guide

This document explains how to use the server startup scripts and what they do.

## Overview

The application consists of five different servers:
1. Main API Server (Port 3000)
2. Office WebSocket Server (Port 8000)
3. Technician WebSocket Server (Port 8001)
4. Office Frontend (Port 5173)
5. Technician Frontend (Port 5178)

## Starting All Servers

To start all servers at once:

```bash
./start_all_servers.sh
```

This script will:
1. Clean up any existing server processes
2. Set up the database connection environment
3. Start each server in sequence with appropriate delays
4. Create log files in the `logs/` directory

## Starting Individual Servers

You can start individual servers using their respective scripts in the `startup_scripts/` directory:

```bash
# Start Main API
./startup_scripts/start_main_api.sh

# Start Office WebSocket
./startup_scripts/start_office_ws.sh

# Start Technician WebSocket
./startup_scripts/start_tech_ws.sh

# Start Office Frontend
./startup_scripts/start_office_frontend.sh

# Start Technician Frontend
./startup_scripts/start_tech_frontend.sh
```

## Log Files

All server logs are stored in the `logs/` directory:
- `main_api.log` - Main API server logs
- `office_ws.log` - Office WebSocket server logs
- `tech_ws.log` - Technician WebSocket server logs
- `office_frontend.log` - Office Frontend logs
- `tech_frontend.log` - Technician Frontend logs

## Server URLs

When all servers are running, they can be accessed at:
- Main API: http://localhost:3000
- Office WebSocket: http://localhost:8000
- Technician WebSocket: http://localhost:8001
- Office Frontend: http://localhost:5173
- Technician Frontend: http://localhost:5178

## Stopping Servers

To stop all servers when using `start_all_servers.sh`:
1. Press `Ctrl+C` in the terminal where the script is running
2. The script will automatically clean up all server processes

To stop individual servers:
1. Find the process ID: `lsof -i :<port_number>`
2. Kill the process: `kill -9 <process_id>`

## Troubleshooting

If servers won't start:
1. Check if ports are already in use: `lsof -i :<port_number>`
2. Check the log files in the `logs/` directory for error messages
3. Run the cleanup manually:
   ```bash
   pkill -9 -f "python.*main.py"
   pkill -9 -f "vite"
   pkill -9 -f "uvicorn"
   pkill -9 -f "node.*dev"
   pkill -9 -f "npm.*dev"
   ``` 