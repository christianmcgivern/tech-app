#!/bin/bash

echo "🔄 Cleaning up existing processes..."

# Kill any existing Python/Node processes for our servers
pkill -f "python.*main.py" || true
pkill -f "vite" || true

# Wait a moment for processes to clean up
sleep 2

echo "🗄️ Setting up database connection..."

# Create .env file if it doesn't exist
cat > src/backend/.env << EOL
DB_NAME=tech_workflow_db
DB_USER=office_admin
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
EOL

echo "🚀 Starting backend server..."
cd src/backend
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo "🌐 Starting frontend server..."
cd ../frontend/technician-app
npm run dev &
FRONTEND_PID=$!

echo "✨ Servers started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Backend running on http://localhost:3000"
echo "Frontend running on http://localhost:5178"

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID

# If we get here, one of the processes died
echo "❌ A server process has terminated"
echo "Cleaning up..."

# Kill the remaining process
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true 