import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    """Set up the database and load demo data"""
    load_dotenv()
    
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME', 'tech_workflow_db'),
        'user': os.getenv('DB_USER', 'office_admin'),
        'password': os.getenv('DB_PASSWORD', 'secure_password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Connected to database successfully!")
        
        # Create schema first
        print("Creating database schema...")
        with open('src/db/schema.sql', 'r') as f:
            schema = f.read()
            cur.execute(schema)
        print("Schema created successfully!")
        
        # Load demo data
        print("Loading demo data...")
        with open('src/db/demo_data.sql', 'r') as f:
            demo_data = f.read()
            cur.execute(demo_data)
        print("Demo data loaded successfully!")
        
        # Verify data
        tables = ['trucks', 'technicians', 'inventory_items', 'customers', 'work_orders']
        print("\nData verification:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"Table {table}: {count} records")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database() 