#!/bin/bash

# Start the backend server
echo "Starting backend server..."
python src/backend/main.py &

# Wait a bit for the backend to start
sleep 2

# Start the frontend development server
echo "Starting frontend server..."
cd src/frontend/office-platform && npm run dev 