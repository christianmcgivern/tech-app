#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Main API Server..."

# Change to the backend directory
cd "$(dirname "$0")/../src/backend" || exit 1

# Start the main API server
python main.py > ../../logs/main_api.log 2>&1 