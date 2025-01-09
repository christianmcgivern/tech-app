# Step 7: Deployment Guide

## Overview
This document details the deployment process for the CCTV Technician Workflow System, including both the office platform and technician mobile app.

## Current System Status
- **Database**: ✅ ACTIVE
  - PostgreSQL 15+ running on localhost:5432
  - Database name: tech_workflow_db
  - Current user: office_admin
  - Contains active data including:
    - Technician records
    - Work orders
    - Inventory tracking
    - Customer data

- **Backend Services**:
  - Main API Server: Port 3000 (FastAPI)
  - Office WebSocket Server: Port 8000
  - Technician WebSocket Server: Port 8001

Note: The database is currently active and populated with demo data. Any deployment steps below are for reference or additional instances.

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 15+
- Nginx
- PM2 (for process management)
- Domain name (for production)
- SSL certificate

## Database Setup

### PostgreSQL Installation
```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create Database and Users
sudo -u postgres createdb tech_workflow_db
sudo -u postgres psql

# In PostgreSQL prompt
CREATE USER office_admin WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tech_workflow_db TO office_admin;
```

### Initial Data
```bash
# Load schema and demo data
python src/db/setup_demo.py
```

The demo data includes:
- 5 trucks (1 office + 4 service)
- 4 technicians
- 8 sample customers
- Complete inventory catalog
- Historical work orders
- Future scheduled work

## Backend Deployment

### 1. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file in project root:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tech_workflow_db
DB_USER=office_admin
DB_PASSWORD=secure_password

# API Configuration
OPENAI_API_KEY=your_api_key_here
```

### 3. Server Setup

#### Main API Server (Port 3000)
```bash
cd src/backend
uvicorn main:app --host 0.0.0.0 --port 3000 --workers 1 --log-level info
```

#### Office WebSocket Server (Port 8000)
```bash
cd src/backend
uvicorn office-server.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
```

#### Technician WebSocket Server (Port 8001)
```bash
cd src/backend
uvicorn technician-server.main:app --host 0.0.0.0 --port 8001 --workers 1 --log-level info
```

## Frontend Deployment

### 1. Office Platform (React)

#### Dependencies Installation
```bash
cd src/frontend/office-platform
npm install
```

#### Build Configuration
Update `vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      },
      '/ws': {
        target: 'http://localhost:8000',
        ws: true
      }
    }
  }
})
```

#### Production Build
```bash
npm run build
```

### 2. Technician App (Progressive Web App)

#### Dependencies Installation
```bash
cd src/frontend/technician-app
npm install
```

#### Build Configuration
Update `app.config.js`:
```javascript
export default {
  name: 'TechnicianApp',
  version: '1.0.0',
  extra: {
    apiUrl: process.env.API_URL || 'http://localhost:3000',
    wsUrl: process.env.WS_URL || 'ws://localhost:8001'
  }
}
```

## Nginx Configuration

```nginx
# Office Platform
server {
    listen 443 ssl;
    server_name office.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    root /path/to/office-platform/dist;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Main API proxy
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Office WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Technician App
server {
    listen 443 ssl;
    server_name tech.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    root /path/to/technician-app/dist;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Main API proxy
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Technician WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Development Server Setup

### Starting All Services
The system consists of multiple servers that need to run concurrently:
1. Main API Server (port 3000)
2. Office WebSocket Server (port 8000)
3. Technician WebSocket Server (port 8001)
4. Office Frontend (port 5173)
5. Technician Frontend (port 5178)

To start all services in the correct order, use the provided startup script:

```bash
# Make the script executable (first time only)
chmod +x start_all_servers.sh

# Start all servers
./start_all_servers.sh
```

The script will:
1. Kill any existing server processes
2. Configure the database connection
3. Start all servers with automatic monitoring
4. Display all server URLs and process IDs
5. Automatically restart any failed services
6. Provide detailed logging for troubleshooting

### Server URLs and Monitoring
- Main API: http://localhost:3000
- Office WebSocket: http://localhost:8000
- Technician WebSocket: http://localhost:8001
- Office Frontend: http://localhost:5173
- Technician Frontend: http://localhost:5178

Each server's status is monitored continuously, with automatic restart capability if any service fails. Logs are stored in the `logs/` directory:
- `logs/main_api.log`
- `logs/office_ws.log`
- `logs/tech_ws.log`
- `logs/office_frontend.log`
- `logs/tech_frontend.log`

### Process Management
The startup script provides:
- Individual process monitoring
- Automatic process recovery
- Graceful shutdown with Ctrl+C
- Detailed status logging
- Clear error reporting

### Troubleshooting Server Startup

1. **Check Server Logs**
```bash
# View specific server log
tail -f logs/main_api.log    # Main API server
tail -f logs/office_ws.log   # Office WebSocket
tail -f logs/tech_ws.log     # Tech WebSocket
tail -f logs/office_frontend.log  # Office Frontend
tail -f logs/tech_frontend.log    # Tech Frontend
```

2. **Port Conflicts**
```bash
# Check processes using specific ports
sudo lsof -i :3000  # Main API
sudo lsof -i :8000  # Office WebSocket
sudo lsof -i :8001  # Tech WebSocket
sudo lsof -i :5173  # Office Frontend
sudo lsof -i :5178  # Tech Frontend

# Kill specific process
kill -9 <PID>
```

3. **Manual Process Cleanup**
```bash
# Kill all related processes
pkill -f "python.*main.py"
pkill -f "vite"
pkill -f "uvicorn"
```

4. **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database user permissions
sudo -u postgres psql -c "\du" | grep office_admin

# Test database connection
psql -U office_admin -d tech_workflow_db -c "SELECT 1"
```

## Security Considerations

1. **Database Security**
   - Regular security updates
   - Strong passwords
   - Limited network access
   - Regular backups
   - Access control for different user types

2. **API Security**
   - Rate limiting
   - JWT authentication
   - HTTPS only
   - Input validation
   - CORS configuration

3. **WebSocket Security**
   - Secure WebSocket (wss://)
   - Client authentication
   - Message validation
   - Connection monitoring
   - Rate limiting

## Monitoring and Maintenance

1. **Process Monitoring**
```bash
# View all server logs
tail -f logs/*.log

# Check server status
ps aux | grep "python.*main.py"
ps aux | grep "vite"
```

2. **Database Maintenance**
```bash
# Regular vacuum
psql -U office_admin -d tech_workflow_db -c "VACUUM ANALYZE;"

# Backup database
pg_dump -U office_admin tech_workflow_db > backup_$(date +%Y%m%d).sql
```

3. **Log Rotation**
```nginx
# /etc/logrotate.d/tech-workflow
/var/log/tech-workflow/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        /usr/sbin/service nginx reload > /dev/null
    endscript
}
```