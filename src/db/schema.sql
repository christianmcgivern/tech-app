-- Core Tables
CREATE TABLE trucks (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    name VARCHAR(255) NOT NULL,
    is_office_truck BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE technicians (
    id SERIAL PRIMARY KEY CHECK (id >= 1),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    scheduled_for TIMESTAMP,
    notes TEXT
);

CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    unit VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE truck_inventory (
    id SERIAL PRIMARY KEY,
    truck_id INTEGER REFERENCES trucks(id),
    item_id INTEGER REFERENCES inventory_items(id),
    quantity INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for inventory-related tables
CREATE INDEX idx_truck_inventory_truck_id ON truck_inventory(truck_id);
CREATE INDEX idx_truck_inventory_item_id ON truck_inventory(item_id);
CREATE INDEX idx_inventory_items_category ON inventory_items(category);
CREATE INDEX idx_inventory_items_name ON inventory_items(name);

-- Tracking Tables
CREATE TABLE technician_clock_records (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    truck_id INTEGER REFERENCES trucks(id),
    clock_in_time TIMESTAMP,
    clock_out_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE travel_logs (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    technician_id INTEGER REFERENCES technicians(id),
    travel_start_time TIMESTAMP,
    travel_end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- History Tables
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

CREATE TABLE customer_history (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    notes TEXT,
    created_by_type VARCHAR(50),
    created_by_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Tables
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id),
    notification_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE manual_notifications (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    message TEXT,
    priority VARCHAR(50) DEFAULT 'normal',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Agent Tables
CREATE TABLE voice_agent_sessions (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES technicians(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE voice_agent_interactions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES voice_agent_sessions(id),
    interaction_type VARCHAR(50),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 