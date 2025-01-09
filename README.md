# Technician Workflow Management System

## Overview
A comprehensive web-based platform for managing field technician workflows, featuring real-time voice interaction, work order management, and automated status tracking. The system consists of two main applications:

1. **Technician Mobile App**: A voice-enabled mobile interface for field technicians
2. **Office Platform**: A management dashboard for office staff

## Key Features

### Voice-Enabled Workflow Management
- Real-time voice interaction using WebRTC
- Natural language processing for hands-free operation
- Automated workflow state tracking
- Contextual responses based on current work status

### Work Order Management
- Real-time work order tracking
- Automated status updates
- Note taking and office notifications
- Customer information management
- Job timing and travel tracking

### Inventory Management
- Real-time truck inventory tracking
- Automated inventory updates
- Low stock notifications
- Inventory transfer between trucks

### Real-time Communication
- Instant notifications between office and field
- Status updates in real-time
- Emergency alerts and priority messaging
- Voice and text-based communication

## Technical Stack

### Frontend
- React with TypeScript
- Material-UI for technician app
- Tailwind CSS for office platform
- WebRTC for real-time voice communication
- Axios for API communication

### Backend
- FastAPI (Python)
- PostgreSQL database
- WebSocket for real-time updates
- JWT authentication
- Real-time voice processing

## Documentation
Extensive documentation is available in the `docs` folder:
- `api_reference.txt`: Complete API endpoint documentation
- `realtime_api_documentation.txt`: Real-time API integration details
- `updated_technician_workflow_with_notifications.txt`: Detailed workflow documentation
- `step4_technician_workflow_implementation.md`: Step-by-step implementation guide
- Additional technical specifications and guides

## Getting Started

### Prerequisites
- Node.js (v16+)
- Python (3.9+)
- PostgreSQL (14+)
- pnpm (recommended) or npm
- OpenAI API key with access to real-time audio models

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd tech-app
```

2. Install frontend dependencies:
```bash
cd src/frontend/technician-app
pnpm install
cd ../office-platform
pnpm install
```

3. Install backend dependencies:
```bash
cd ../../backend
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Create the database
createdb tech_workflow_db

# Run migrations
python migrations.py
```

5. Configure environment variables:
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and update the following required values:
# - OPENAI_API_KEY: Your OpenAI API key
# - DB_PASSWORD: Your secure database password
# - JWT_SECRET: A secure random string for JWT signing
```

The `.env.example` file contains all necessary configuration with dummy values. Required changes are:
- `OPENAI_API_KEY`: Your OpenAI API key with access to real-time audio models
- `DB_PASSWORD`: A secure password for the PostgreSQL database
- `JWT_SECRET`: A secure random string for JWT token signing
- Other values can be left as defaults for local development

### Security Notes
- Never commit your `.env` file or API keys to version control
- The `.gitignore` file is configured to exclude `.env` files
- For production deployment, use secure environment variable management
- Regularly rotate API keys and monitor usage
- Use strong, unique passwords for database access
- Generate a secure random string for JWT_SECRET in production

### Running the Application

#### Option 1: Using the Start Script
The easiest way to start all servers is using the provided script:
```bash
./start-servers.sh
```
This will start the backend server, technician app, and office platform simultaneously.

#### Option 2: Manual Startup
Alternatively, you can start each server individually:

1. Start the backend server:
```bash
cd src/backend
uvicorn main:app --reload
```

2. Start the technician app:
```bash
cd src/frontend/technician-app
pnpm dev
```

3. Start the office platform:
```bash
cd src/frontend/office-platform
pnpm dev
```

## Architecture

### Database Schema
- `technicians`: Technician information and status
- `work_orders`: Work order details and assignments
- `technician_clock_records`: Daily clock-in/out records with workflow states
- `truck_inventory`: Real-time inventory tracking
- `work_order_notes`: Communication and status notes
- `manual_notifications`: Priority alerts and notifications

### API Endpoints
- `/api/technicians/*`: Technician management and status
- `/api/work-orders/*`: Work order operations
- `/api/inventory/*`: Inventory management
- `/ws/*`: WebSocket endpoints for real-time updates

### Voice Agent System
- Real-time audio processing
- Natural language understanding
- Context-aware responses
- Workflow state management
- Function calling system

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- OpenAI for real-time voice processing
- FastAPI team for the excellent framework
- React team for the frontend framework
- All contributors and testers
