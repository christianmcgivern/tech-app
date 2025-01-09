# Step 1a: Database Setup and Schema

## Overview
This document details the PostgreSQL database implementation for the AI-Powered Technician Workflow System. The database serves as the central data store for both the office platform and technician mobile app, with real-time synchronization capabilities.

## Project Structure
```
src/
├── db/
│   ├── schema.sql       # Database schema definitions
│   ├── demo_data.sql    # Sample data for development
│   └── setup_demo.py    # Python script to initialize database
```

## Database Setup

### Installation and Configuration
```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create Database
sudo -u postgres createdb tech_workflow_db

# Create Users with Proper Permissions
sudo -u postgres psql
CREATE USER office_admin WITH PASSWORD 'secure_password';
CREATE USER tech_app WITH PASSWORD 'tech_secure_password';

# Grant Permissions
GRANT ALL PRIVILEGES ON DATABASE tech_workflow_db TO office_admin;
GRANT CONNECT ON DATABASE tech_workflow_db TO tech_app;

# Grant Schema Permissions
sudo -u postgres psql -d tech_workflow_db -c "GRANT ALL ON SCHEMA public TO office_admin;"
```

### Python Dependencies
```bash
pip install psycopg2-binary python-dotenv
```

### Environment Configuration
Create a `.env` file in the project root:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tech_workflow_db
DB_USER=office_admin
DB_PASSWORD=secure_password
```

## Schema Definition

### Core Tables

```sql
-- Trucks
CREATE TABLE trucks (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    name VARCHAR(255) NOT NULL,
    is_office_truck BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technicians
CREATE TABLE technicians (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    is_new_customer BOOLEAN DEFAULT TRUE,
    preferred_schedule_start TIME,
    preferred_schedule_end TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Work Orders
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    customer_id INTEGER REFERENCES customers(id),
    title VARCHAR(255) NOT NULL,
    brief_description VARCHAR(500) NOT NULL,
    full_summary TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_technician_id INTEGER REFERENCES technicians(id),
    created_by_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    scheduled_for TIMESTAMP
);

-- Work Order Notes
CREATE TABLE work_order_notes (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES technicians(id),
    note_text TEXT NOT NULL,
    alert_office BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory Management
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    unit VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE truck_inventory (
    id SERIAL PRIMARY KEY,
    truck_id INTEGER REFERENCES trucks(id),
    item_id INTEGER REFERENCES inventory_items(id),
    quantity INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tracking and History Tables

```sql
-- Technician Clock Records
CREATE TABLE technician_clock_records (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    truck_id INTEGER REFERENCES trucks(id),
    clock_in_time TIMESTAMP,
    clock_out_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Travel Logs
CREATE TABLE travel_logs (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    technician_id INTEGER REFERENCES technicians(id),
    travel_start_time TIMESTAMP,
    travel_end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Order History
CREATE TABLE work_order_history (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    changed_by_type VARCHAR(50),
    changed_by_id INTEGER,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer History
CREATE TABLE customer_history (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    notes TEXT,
    created_by_type VARCHAR(50),
    created_by_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Notification and Voice Agent Tables

```sql
-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    notification_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Manual Notifications
CREATE TABLE manual_notifications (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    message TEXT,
    priority VARCHAR(50) DEFAULT 'normal',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Agent Sessions
CREATE TABLE voice_agent_sessions (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Voice Agent Interactions
CREATE TABLE voice_agent_interactions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES voice_agent_sessions(id),
    interaction_type VARCHAR(50),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Demo Data

The database includes sample data for development and testing:

1. **Trucks (5 total)**:
   - Office Truck (ID: 1)
   - 4 Service Trucks (201-204)

2. **Technicians (4 total)**:
   - Mike Johnson
   - Sarah Williams
   - David Chen
   - Alex Rodriguez

3. **Inventory Items (17 total)**:
   - Cameras (4 types: IP Dome, Bullet, Analog, PTZ)
   - Cables (3 types: Cat6, RG59 Siamese, Shielded Cat6)
   - Connectors (RJ45, BNC)
   - Tools (Crimpers, Testers, Fish Tape, Drill Kit)
   - Power Supplies (12V, PoE Injector, PoE Switch)

4. **Customers (8 total)**:
   - City Bank
   - Retail Mall Corp
   - School District
   - Local Restaurant
   - Office Complex
   - Gas Station Chain
   - Medical Center
   - Apartment Complex

5. **Work Orders (120 total)**:
   - Past week: 56 orders (mostly completed)
   - Current day: 8 orders (in progress/pending)
   - Future week: 56 orders (all scheduled)
   - 2 orders per tech per day
   - Types: New Installation, System Upgrade, Maintenance, Repair

## Database Initialization

### Python Setup Script
The database can be initialized using the provided Python script:

```python
import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    """Set up the database and load demo data"""
    load_dotenv()
    
    db_params = {
        'dbname': os.getenv('DB_NAME', 'tech_workflow_db'),
        'user': os.getenv('DB_USER', 'office_admin'),
        'password': os.getenv('DB_PASSWORD', 'secure_password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create schema
        with open('src/db/schema.sql', 'r') as f:
            schema = f.read()
            cur.execute(schema)
        
        # Load demo data
        with open('src/db/demo_data.sql', 'r') as f:
            demo_data = f.read()
            cur.execute(demo_data)
            
    finally:
        if conn:
            conn.close()
```

### Running the Setup
```bash
# From project root
python src/db/setup_demo.py
```

## Notes and Best Practices

1. **Timestamps**
   - All timestamps are stored in UTC
   - Use `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` for creation times
   - Separate `updated_at` field for tracking modifications

2. **Primary Keys**
   - All tables use SERIAL PRIMARY KEY
   - Most tables enforce ID >= 1
   - Office truck is always ID 1

3. **Foreign Keys**
   - All relationships are properly constrained
   - Cascading deletes are avoided for data integrity

4. **Status Values**
   - Work Orders: 'pending', 'in_progress', 'completed', 'scheduled'
   - Notification Priority: 'normal', 'high', 'urgent'

5. **Work Order Notes**
   - Notes are automatically deleted when parent work order is deleted (CASCADE)
   - Alert office flag for critical updates
   - Timestamps track both creation and updates
   - Linked to both work order and technician for full context

6. **Inventory Management**
   - Each truck maintains its own inventory
   - Office truck (ID 1) excluded from inventory
   - Standard quantities:
     - Cameras: 5 units
     - Cables: 500 feet
     - Connectors: 100 units
     - Tools: 2 units
     - Power Supplies: 10 units

7. **Work Order Scheduling**
   - Two work orders per technician per day
   - Scheduled between 8 AM and 4 PM
   - Travel time logged 30 minutes before scheduled time

8. **Clock Records**
   - Standard work hours: 7 AM - 4 PM (weekdays)
   - Standard work hours: 7 AM - 1 PM (weekends)

## Maintenance

1. **Backup Configuration**
```bash
# Daily backup
pg_dump tech_workflow_db > backup_$(date +%Y%m%d).sql
```

2. **Index Optimization**
```sql
CREATE INDEX idx_work_orders_technician ON work_orders(assigned_technician_id);
CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_notifications_unread ON notifications(is_read) WHERE NOT is_read;
CREATE INDEX idx_work_orders_customer ON work_orders(customer_id);
CREATE INDEX idx_work_orders_scheduled ON work_orders(scheduled_for);
CREATE INDEX idx_technician_clock_records_date ON technician_clock_records(clock_in_time);
CREATE INDEX idx_work_order_notes_work_order ON work_order_notes(work_order_id);
CREATE INDEX idx_work_order_notes_technician ON work_order_notes(technician_id);
```

3. **Regular Maintenance**
```sql
VACUUM ANALYZE;
```

4. **Data Retention**
```sql
-- Archive old records (example)
CREATE TABLE work_orders_archive (LIKE work_orders);
INSERT INTO work_orders_archive 
SELECT * FROM work_orders 
WHERE created_at < NOW() - INTERVAL '1 year';
```

5. **Performance Monitoring**
```sql
-- Monitor long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE pg_stat_activity.query != '<IDLE>' 
AND pg_stat_activity.waiting = true;
``` 