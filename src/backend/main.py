from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import traceback
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection parameters
db_params = {
    'dbname': os.getenv('DB_NAME', 'tech_workflow_db'),
    'user': os.getenv('DB_USER', 'office_admin'),
    'password': os.getenv('DB_PASSWORD', 'secure_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

logger.info("Database parameters: %s", {k: v for k, v in db_params.items() if k != 'password'})

# Global connection pool
conn_pool = None

def get_db_connection():
    global conn_pool
    try:
        if conn_pool is None or conn_pool.closed:
            logger.info("Creating new database connection...")
            conn_pool = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
            conn_pool.autocommit = True
        return conn_pool
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    # Initialize database connection
    get_db_connection()
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    global conn_pool
    if conn_pool and not conn_pool.closed:
        logger.info("Closing database connection...")
        conn_pool.close()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Technician(BaseModel):
    id: int
    name: str
    phone: str
    active: bool

class Truck(BaseModel):
    id: int
    name: str
    is_office_truck: bool
    active: bool
    created_at: datetime

class ClockInRequest(BaseModel):
    truck_id: int

@app.get("/api/technicians")
async def get_technicians(active: bool = True):
    print(f"Getting technicians (active={active})")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT * FROM technicians WHERE active = true" if active else "SELECT * FROM technicians"
        print(f"Executing query: {query}")
        cur.execute(query)
        technicians = cur.fetchall()
        print(f"Found {len(technicians)} technicians: {technicians}")
        return technicians
    except Exception as e:
        print(f"Error fetching technicians: {e}")
        print("Traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching technicians: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/api/trucks")
async def get_trucks(available: bool = True):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT * FROM trucks WHERE active = true" if available else "SELECT * FROM trucks"
        print(f"Executing query: {query}")
        cur.execute(query)
        trucks = cur.fetchall()
        print(f"Found {len(trucks)} trucks: {trucks}")
        return trucks
    except Exception as e:
        print(f"Error fetching trucks: {e}")
        print("Traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching trucks: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/api/technicians/{technician_id}/clock-in")
async def clock_in_technician(technician_id: int, clock_in_data: ClockInRequest):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Check if technician exists and is active
        cur.execute("SELECT id FROM technicians WHERE id = %s AND active = true", (technician_id,))
        technician = cur.fetchone()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found or inactive")
        
        # Check if truck exists and is active
        cur.execute("SELECT id FROM trucks WHERE id = %s AND active = true", (clock_in_data.truck_id,))
        truck = cur.fetchone()
        if not truck:
            raise HTTPException(status_code=404, detail="Truck not found or inactive")
        
        # Check if technician has an active clock-in record
        cur.execute("""
            SELECT id FROM technician_clock_records 
            WHERE technician_id = %s 
            AND clock_in_time::date = CURRENT_DATE 
            AND clock_out_time IS NULL
        """, (technician_id,))
        
        existing_record = cur.fetchone()
        if existing_record:
            raise HTTPException(
                status_code=422, 
                detail="Cannot clock in: Technician already has an active clock-in record for today. Must clock out first."
            )
        
        # Create a new clock-in record with truck_id
        cur.execute("""
            INSERT INTO technician_clock_records (technician_id, truck_id, clock_in_time)
            VALUES (%s, %s, NOW())
            RETURNING id, clock_in_time
        """, (technician_id, clock_in_data.truck_id))
        
        record = cur.fetchone()
        conn.commit()
        
        return {
            "id": record['id'],
            "technician_id": technician_id,
            "truck_id": clock_in_data.truck_id,
            "clock_in_time": record['clock_in_time'],
            "message": "Successfully clocked in"
        }
    except Exception as e:
        print(f"Error clocking in: {e}")
        print("Traceback:", traceback.format_exc())
        conn.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error clocking in: {str(e)}")
    finally:
        conn.close()

@app.post("/api/technicians/{technician_id}/clock-out")
async def clock_out_technician(technician_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Find and update the active clock-in record
        cur.execute("""
            UPDATE technician_clock_records
            SET clock_out_time = NOW()
            WHERE technician_id = %s 
            AND clock_out_time IS NULL
            AND clock_in_time::date = CURRENT_DATE
            RETURNING id, clock_in_time, clock_out_time
        """, (technician_id,))
        
        record = cur.fetchone()
        if not record:
            raise HTTPException(
                status_code=404, 
                detail="No active clock-in record found for today"
            )
        
        conn.commit()
        return {
            "id": record['id'],
            "technician_id": technician_id,
            "clock_in_time": record['clock_in_time'],
            "clock_out_time": record['clock_out_time'],
            "message": "Successfully clocked out"
        }
    except Exception as e:
        print(f"Error clocking out: {e}")
        conn.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error clocking out: {str(e)}")
    finally:
        conn.close()

@app.get("/api/technicians/{technician_id}/work-orders")
async def get_technician_work_orders(technician_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT wo.*, 
                   t.name as technician_name,
                   c.name as customer_name,
                   COUNT(wn.id) as notes_count
            FROM work_orders wo
            LEFT JOIN technicians t ON wo.assigned_technician_id = t.id
            LEFT JOIN customers c ON wo.customer_id = c.id
            LEFT JOIN work_order_notes wn ON wo.id = wn.work_order_id
            WHERE wo.assigned_technician_id = %s
            GROUP BY wo.id, t.name, c.name
            ORDER BY wo.scheduled_for DESC
        """, (technician_id,))
        work_orders = cur.fetchall()
        return work_orders
    except Exception as e:
        print(f"Error fetching work orders: {e}")
        raise HTTPException(status_code=500, detail="Error fetching work orders")
    finally:
        conn.close()

@app.get("/api/trucks/{truck_id}/inventory")
async def get_truck_inventory(truck_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT i.*, ti.quantity 
            FROM truck_inventory ti
            JOIN inventory_items i ON ti.item_id = i.id
            WHERE ti.truck_id = %s
        """, (truck_id,))
        inventory = cur.fetchall()
        return inventory
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail="Error fetching inventory")
    finally:
        conn.close()

@app.get("/api/technicians/{technician_id}/activity")
async def get_technician_activity(technician_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                'work_order_completed' as type,
                wo.title as description,
                wo.updated_at as time
            FROM work_orders wo
            WHERE wo.assigned_technician_id = %s 
            AND wo.status = 'completed'
            ORDER BY wo.updated_at DESC
            LIMIT 10
        """, (technician_id,))
        activity = cur.fetchall()
        return activity
    except Exception as e:
        print(f"Error fetching activity: {e}")
        raise HTTPException(status_code=500, detail="Error fetching activity")
    finally:
        conn.close()

@app.get("/api/work-orders")
async def get_work_orders():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT wo.*, 
                   t.name as technician_name,
                   c.name as customer_name,
                   c.address as customer_address,
                   c.phone as customer_phone,
                   c.email as customer_email,
                   COUNT(wn.id) as notes_count
            FROM work_orders wo
            LEFT JOIN technicians t ON wo.assigned_technician_id = t.id
            LEFT JOIN customers c ON wo.customer_id = c.id
            LEFT JOIN work_order_notes wn ON wo.id = wn.work_order_id
            GROUP BY wo.id, t.name, c.name, c.address, c.phone, c.email
            ORDER BY wo.scheduled_for DESC
        """)
        work_orders = cur.fetchall()
        
        # Format the response to include nested technician and customer objects
        formatted_orders = []
        for order in work_orders:
            formatted_order = dict(order)
            if order['technician_name']:
                formatted_order['technician'] = {
                    'id': order['assigned_technician_id'],
                    'name': order['technician_name']
                }
            if order['customer_name']:
                formatted_order['customer'] = {
                    'id': order['customer_id'],
                    'name': order['customer_name'],
                    'address': order['customer_address'],
                    'phone': order['customer_phone'],
                    'email': order['customer_email']
                }
            formatted_orders.append(formatted_order)
        
        return formatted_orders
    except Exception as e:
        print(f"Error fetching work orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching work orders: {str(e)}")
    finally:
        conn.close()

@app.get("/api/technicians/status")
async def get_technician_status():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Get all active technicians with their current clock records and work orders
        cur.execute("""
            WITH current_clock_records AS (
                SELECT DISTINCT ON (technician_id)
                    technician_id,
                    clock_in_time,
                    clock_out_time
                FROM technician_clock_records
                WHERE clock_in_time::date = CURRENT_DATE
                ORDER BY technician_id, clock_in_time DESC
            ),
            current_work_orders AS (
                SELECT DISTINCT ON (assigned_technician_id)
                    assigned_technician_id,
                    id as work_order_id,
                    title,
                    status,
                    scheduled_for
                FROM work_orders
                WHERE status = 'in_progress'
                ORDER BY assigned_technician_id, scheduled_for DESC
            )
            SELECT 
                t.id as technician_id,
                t.name,
                CASE 
                    WHEN ccr.clock_in_time IS NOT NULL AND ccr.clock_out_time IS NULL THEN 'active'
                    ELSE 'inactive'
                END as status,
                ccr.clock_in_time,
                ccr.clock_out_time,
                cwo.work_order_id,
                cwo.title as work_order_title,
                cwo.status as work_order_status,
                cwo.scheduled_for
            FROM technicians t
            LEFT JOIN current_clock_records ccr ON t.id = ccr.technician_id
            LEFT JOIN current_work_orders cwo ON t.id = cwo.assigned_technician_id
            WHERE t.active = true
        """)
        technicians = cur.fetchall()
        
        formatted_technicians = []
        for tech in technicians:
            tech_dict = {
                'technician_id': tech['technician_id'],
                'name': tech['name'],
                'status': tech['status']
            }
            if tech['work_order_id']:
                tech_dict['current_work_order'] = {
                    'id': tech['work_order_id'],
                    'title': tech['work_order_title'],
                    'status': tech['work_order_status'],
                    'scheduled_for': tech['scheduled_for']
                }
            if tech['clock_in_time']:
                tech_dict['last_clock_record'] = {
                    'clock_in_time': tech['clock_in_time'],
                    'clock_out_time': tech['clock_out_time']
                }
            formatted_technicians.append(tech_dict)
        
        return formatted_technicians
    except Exception as e:
        print(f"Error fetching technician status: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching technician status: {str(e)}")
    finally:
        conn.close()

@app.get("/api/stats/dashboard")
async def get_dashboard_stats():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Get active work orders count
        cur.execute("""
            SELECT COUNT(*) as count
            FROM work_orders
            WHERE status = 'in_progress'
        """)
        active_work_orders = cur.fetchone()['count']
        
        # Get completed work orders today
        cur.execute("""
            SELECT COUNT(*) as count
            FROM work_orders
            WHERE status = 'completed'
            AND updated_at::date = CURRENT_DATE
        """)
        completed_today = cur.fetchone()['count']
        
        # Get active technicians count
        cur.execute("""
            SELECT COUNT(DISTINCT technician_id) as count
            FROM technician_clock_records
            WHERE clock_in_time::date = CURRENT_DATE
            AND clock_out_time IS NULL
        """)
        technicians_active = cur.fetchone()['count']
        
        # Get pending work orders count
        cur.execute("""
            SELECT COUNT(*) as count
            FROM work_orders
            WHERE status = 'pending'
        """)
        pending_work_orders = cur.fetchone()['count']
        
        return {
            'active_work_orders': active_work_orders,
            'completed_today': completed_today,
            'technicians_active': technicians_active,
            'pending_work_orders': pending_work_orders
        }
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")
    finally:
        conn.close()

@app.get("/api/customers")
async def get_customers():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.*,
                   CASE WHEN MIN(wo.created_at) > NOW() - INTERVAL '30 days'
                        THEN true ELSE false END as is_new_customer
            FROM customers c
            LEFT JOIN work_orders wo ON c.id = wo.customer_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        customers = cur.fetchall()
        return customers
    except Exception as e:
        print(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")
    finally:
        conn.close()

@app.get("/api/inventory/items")
async def get_all_inventory():
    """Get all inventory items with their quantities across all locations."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # First get all inventory items with their locations in a single query
        # Using indexes on category and name for sorting
        cur.execute("""
            WITH inventory_locations AS (
                SELECT 
                    ti.item_id,
                    jsonb_build_object(
                        'truck_id', t.id,
                        'truck_name', t.name,
                        'quantity', ti.quantity
                    ) as location_info
                FROM truck_inventory ti
                JOIN trucks t ON ti.truck_id = t.id
            )
            SELECT 
                i.id,
                i.name,
                i.description,
                i.category,
                i.unit,
                COALESCE(
                    (
                        SELECT jsonb_agg(il.location_info)
                        FROM inventory_locations il
                        WHERE il.item_id = i.id
                    ),
                    '[]'::jsonb
                ) as locations
            FROM inventory_items i
            ORDER BY i.category, i.name
        """)
        
        inventory = cur.fetchall()
        return inventory
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail="Error fetching inventory")
    finally:
        if conn:
            conn.close()

@app.get("/api/inventory/items/{item_id}")
async def get_inventory_item(item_id: int):
    """Get a specific inventory item with its quantities across all locations."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                i.id,
                i.name,
                i.description,
                i.category,
                i.unit,
                COALESCE(json_agg(json_build_object(
                    'truck_id', t.id,
                    'truck_name', t.name,
                    'quantity', ti.quantity
                )) FILTER (WHERE t.id IS NOT NULL), '[]'::json) as locations
            FROM inventory_items i
            LEFT JOIN truck_inventory ti ON i.id = ti.item_id
            LEFT JOIN trucks t ON ti.truck_id = t.id
            WHERE i.id = %s
            GROUP BY i.id, i.name, i.description, i.category, i.unit
        """, (item_id,))
        
        item = cur.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
            
        cur.close()
        conn.close()
        return item
    except Exception as e:
        print(f"Error fetching inventory item: {e}")
        raise HTTPException(status_code=500, detail="Error fetching inventory item")

@app.get("/api/technicians/{technician_id}")
async def get_technician(technician_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, phone, active
            FROM technicians
            WHERE id = %s
        """, (technician_id,))
        technician = cur.fetchone()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found")
        return technician
    except Exception as e:
        print(f"Error fetching technician: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching technician: {str(e)}")
    finally:
        conn.close()

@app.get("/api/work-orders/{order_id}")
async def get_work_order(order_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Get work order details
        cur.execute("""
            SELECT 
                wo.id,
                wo.title,
                wo.brief_description,
                wo.full_summary,
                wo.status,
                wo.scheduled_for,
                t.name as technician_name,
                c.name as customer_name
            FROM work_orders wo
            LEFT JOIN technicians t ON wo.assigned_technician_id = t.id
            LEFT JOIN customers c ON wo.customer_id = c.id
            WHERE wo.id = %s
        """, (order_id,))
        work_order = cur.fetchone()
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        # Get notes history
        cur.execute("""
            SELECT 
                wn.*,
                t.name as technician_name
            FROM work_order_notes wn
            LEFT JOIN technicians t ON wn.technician_id = t.id
            WHERE wn.work_order_id = %s
            ORDER BY wn.created_at DESC
        """, (order_id,))
        notes = cur.fetchall()
        
        # Add notes to work order response
        work_order['notes'] = notes
        
        return work_order
    except Exception as e:
        print(f"Error fetching work order: {e}")
        raise HTTPException(status_code=500, detail="Error fetching work order")
    finally:
        conn.close()

@app.put("/api/work-orders/{order_id}/notes")
async def update_work_order_notes(order_id: int, notes: dict):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Insert note into work_order_notes table
        cur.execute("""
            INSERT INTO work_order_notes (
                work_order_id,
                technician_id,
                note_text,
                alert_office
            ) VALUES (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id, created_at
        """, (
            order_id,
            notes.get('technician_id'),
            notes['notes'],
            notes.get('alert_office', False)
        ))
        note_record = cur.fetchone()

        # If alert_office is true, create a manual notification
        if notes.get('alert_office'):
            cur.execute("""
                INSERT INTO manual_notifications (
                    technician_id,
                    work_order_id,
                    message,
                    priority,
                    created_at
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    'high',
                    NOW()
                )
            """, (
                notes.get('technician_id'),
                order_id,
                f"Urgent note from technician for Work Order #{order_id}: {notes['notes']}"
            ))

        # Get all notes for this work order
        cur.execute("""
            SELECT 
                wn.*,
                t.name as technician_name
            FROM work_order_notes wn
            LEFT JOIN technicians t ON wn.technician_id = t.id
            WHERE wn.work_order_id = %s
            ORDER BY wn.created_at DESC
        """, (order_id,))
        all_notes = cur.fetchall()

        conn.commit()
        return {
            "id": order_id,
            "notes": all_notes,
            "latest_note": note_record
        }
    except Exception as e:
        print(f"Error updating work order notes: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating work order notes: {str(e)}")
    finally:
        conn.close()

@app.patch("/api/trucks/{truck_id}/inventory/{item_id}")
async def update_truck_inventory(truck_id: str, item_id: int, quantity: dict):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE truck_inventory 
            SET quantity = %s, last_updated = CURRENT_TIMESTAMP
            WHERE truck_id = %s AND item_id = %s
            RETURNING id
        """, (quantity['quantity'], truck_id, item_id))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Inventory item not found for this truck")
            
        conn.commit()
        return {"message": "Inventory updated successfully"}
    except Exception as e:
        conn.rollback()
        print(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Error updating inventory")
    finally:
        conn.close()

@app.get("/api/technicians/{technician_id}/status")
async def get_technician_status(technician_id: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Get technician status with current clock records and work orders
        cur.execute("""
            WITH current_clock_records AS (
                SELECT DISTINCT ON (technician_id)
                    technician_id,
                    truck_id,
                    clock_in_time,
                    clock_out_time
                FROM technician_clock_records
                WHERE clock_in_time::date = CURRENT_DATE
                AND technician_id = %s
                ORDER BY technician_id, clock_in_time DESC
            ),
            current_work_orders AS (
                SELECT 
                    id as work_order_id,
                    title,
                    brief_description,
                    status,
                    scheduled_for
                FROM work_orders
                WHERE assigned_technician_id = %s
                AND status IN ('pending', 'in_progress')
                ORDER BY scheduled_for ASC
            ),
            current_truck AS (
                SELECT 
                    t.id as truck_id,
                    t.name as truck_name,
                    t.is_office_truck
                FROM trucks t
                JOIN current_clock_records ccr ON t.id = ccr.truck_id
                WHERE t.active = true
            )
            SELECT 
                t.id as technician_id,
                t.name,
                t.phone,
                CASE 
                    WHEN ccr.clock_in_time IS NOT NULL AND ccr.clock_out_time IS NULL THEN 'active'
                    ELSE 'inactive'
                END as status,
                ccr.clock_in_time,
                ccr.clock_out_time,
                ct.truck_id,
                ct.truck_name,
                ct.is_office_truck,
                json_agg(
                    json_build_object(
                        'id', cwo.work_order_id,
                        'title', cwo.title,
                        'description', cwo.brief_description,
                        'status', cwo.status,
                        'scheduled_for', cwo.scheduled_for
                    )
                ) FILTER (WHERE cwo.work_order_id IS NOT NULL) as work_orders
            FROM technicians t
            LEFT JOIN current_clock_records ccr ON t.id = ccr.technician_id
            LEFT JOIN current_truck ct ON ccr.truck_id = ct.truck_id
            LEFT JOIN current_work_orders cwo ON true
            WHERE t.id = %s AND t.active = true
            GROUP BY 
                t.id, t.name, t.phone, 
                ccr.clock_in_time, ccr.clock_out_time,
                ct.truck_id, ct.truck_name, ct.is_office_truck
        """, (technician_id, technician_id, technician_id))
        
        technician = cur.fetchone()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found or inactive")
        
        return {
            'technician_id': technician['technician_id'],
            'name': technician['name'],
            'phone': technician['phone'],
            'status': technician['status'],
            'clock_record': {
                'clock_in_time': technician['clock_in_time'],
                'clock_out_time': technician['clock_out_time']
            } if technician['clock_in_time'] else None,
            'truck': {
                'id': technician['truck_id'],
                'name': technician['truck_name'],
                'is_office_truck': technician['is_office_truck']
            } if technician['truck_id'] else None,
            'work_orders': technician['work_orders'] or []
        }
    except Exception as e:
        print(f"Error fetching technician status: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching technician status: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    # Use uvicorn's built-in worker management and signal handling
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        workers=1,
        log_level="info",
        reload=False,
        access_log=True
    ) 