#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Technician Frontend..."

# Change to the technician frontend directory
cd "$(dirname "$0")/../src/frontend/technician-app" || exit 1

# Start the technician frontend
npm run dev > ../../../logs/tech_frontend.log 2>&1 