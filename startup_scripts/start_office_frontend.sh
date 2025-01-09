#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Office Frontend..."

# Change to the office frontend directory
cd "$(dirname "$0")/../src/frontend/office-platform" || exit 1

# Start the office frontend
npm run dev > ../../../logs/office_frontend.log 2>&1 