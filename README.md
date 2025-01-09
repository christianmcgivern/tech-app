# Tech Workflow Application

A full-stack application for managing technician workflows, inventory, and work orders with voice command capabilities.

## Demo Access

After setup, you'll have access to:

1. **Technician Mobile Interface**
   - URL: http://localhost:5174
   - Demo Accounts:
     - Mike Johnson (ID: 1)
     - Sarah Williams (ID: 2)
     - David Chen (ID: 3)
     - Alex Rodriguez (ID: 4)
   - Features:
     - Voice commands for hands-free operation
     - Work order management
     - Inventory tracking
     - Status updates

2. **Office Management Dashboard**
   - URL: http://localhost:5173
   - Features:
     - Real-time technician tracking
     - Work order assignment
     - Inventory management
     - Analytics dashboard

## Demo Data

The database comes pre-populated with demo data including:
- 4 active technicians
- 5 service trucks (including an office truck)
- Sample work orders
- Inventory items
- Customer records

This demo data allows you to test all features immediately after setup.

## Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd tech-app
```

2. **Set up the Backend**
```bash
# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows

# Install Python dependencies
cd src/backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database configuration (default values should work)
```

3. **Set up the Frontend**
```bash
# Install Node.js dependencies
cd src/frontend/technician-app
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and add your OpenAI API key
```

4. **Set up the Database**
```bash
# Create PostgreSQL database and tables
cd src/db
python setup_demo.py
```

5. **Start the Application**
```bash
# Start the backend server (in src/backend directory)
python main.py

# In a new terminal, start the frontend (in src/frontend/technician-app directory)
npm run dev
```

The application should now be running at:
- Frontend: http://localhost:5174
- Backend API: http://localhost:8001/api

## Required Environment Variables

### Backend (.env)
- Database configuration (default values provided)
  - `DB_NAME=tech_workflow_db`
  - `DB_USER=office_admin`
  - `DB_PASSWORD=secure_password`
  - `DB_HOST=localhost`
  - `DB_PORT=5432`

### Frontend (.env.local)
- `VITE_OPENAI_API_KEY`: Your OpenAI API key (required for voice commands)

## Features
- Technician management and tracking
- Work order processing
- Inventory management
- Voice command interface
- Real-time updates
- Dashboard analytics

## Development

### Project Structure
```
tech-app/
├── src/
│   ├── backend/          # FastAPI backend
│   ├── frontend/         # React frontend
│   │   └── technician-app/
│   └── db/              # Database scripts
├── docs/                # Documentation
└── README.md
```

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- OpenAI API key

## Troubleshooting

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :3000  # or whatever port
   # Kill the process
   kill -9 <PID>
   ```

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in .env
   - Ensure database and tables are created

3. **Voice Commands Not Working**
   - Verify OpenAI API key is set correctly
   - Check browser microphone permissions
   - Ensure you're using a supported browser (Chrome recommended)

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[License Type]
