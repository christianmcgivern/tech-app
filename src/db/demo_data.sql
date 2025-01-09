-- Demo Data for CCTV Company

-- First, let's add the office truck
INSERT INTO trucks (name, is_office_truck, active) VALUES
('Office Truck', TRUE, TRUE);

-- Add 4 service trucks
INSERT INTO trucks (name, active) VALUES
('Service Truck 201', TRUE),
('Service Truck 202', TRUE),
('Service Truck 203', TRUE),
('Service Truck 204', TRUE);

-- Add 4 technicians
INSERT INTO technicians (name, phone, active) VALUES
('Mike Johnson', '555-0101', TRUE),
('Sarah Williams', '555-0102', TRUE),
('David Chen', '555-0103', TRUE),
('Alex Rodriguez', '555-0104', TRUE);

-- Add inventory items
INSERT INTO inventory_items (name, description, category, unit) VALUES
-- Cameras
('4MP IP Dome Camera', 'Indoor/Outdoor IP dome camera with IR', 'Cameras', 'unit'),
('8MP IP Bullet Camera', 'Long-range IR bullet camera', 'Cameras', 'unit'),
('2MP Analog Camera', 'Traditional CCTV analog camera', 'Cameras', 'unit'),
('4MP PTZ Camera', 'Pan-tilt-zoom IP camera', 'Cameras', 'unit'),

-- Cables
('Cat6 Cable', 'Pure copper Cat6 ethernet cable', 'Network', 'feet'),
('RG59 Siamese', 'RG59 with power cable for analog', 'Coax', 'feet'),
('Cat6 Shielded', 'Shielded ethernet for outdoor', 'Network', 'feet'),

-- Connectors
('RJ45 Connector', 'Cat6 rated RJ45 male end', 'Connectors', 'unit'),
('BNC Connector', 'Compression BNC for RG59', 'Connectors', 'unit'),
('BNC Crimp Tool', 'Professional crimping tool', 'Tools', 'unit'),
('RJ45 Crimp Tool', 'Professional RJ45 crimper', 'Tools', 'unit'),

-- Power Supplies
('12V Power Supply', '12V 2A power supply', 'Power', 'unit'),
('24V PoE Injector', 'Single port PoE injector', 'Power', 'unit'),
('PoE Switch 8-Port', '8 port managed PoE switch', 'Network', 'unit'),

-- Tools
('Cable Tester', 'Network and coax tester', 'Tools', 'unit'),
('Fish Tape', '100ft steel fish tape', 'Tools', 'unit'),
('Drill Kit', 'Complete installation drill kit', 'Tools', 'unit');

-- Stock each truck with inventory
INSERT INTO truck_inventory (truck_id, item_id, quantity) 
SELECT t.id, i.id, 
    CASE 
        WHEN i.category = 'Cameras' THEN 5
        WHEN i.unit = 'feet' THEN 500
        WHEN i.category = 'Connectors' THEN 100
        WHEN i.category = 'Tools' THEN 2
        WHEN i.category = 'Power' THEN 10
        ELSE 5
    END
FROM trucks t
CROSS JOIN inventory_items i
WHERE t.id != 1; -- Exclude office truck

-- Add some customers
INSERT INTO customers (name, address, phone, email, is_new_customer) VALUES
('City Bank', '123 Financial Dr', '555-1001', 'security@citybank.com', FALSE),
('Retail Mall Corp', '789 Shopping Center Blvd', '555-1002', 'facilities@retailmall.com', FALSE),
('School District', '456 Education Ave', '555-1003', 'security@schooldist.org', FALSE),
('Local Restaurant', '321 Food Court', '555-1004', 'owner@localfood.com', TRUE),
('Office Complex', '567 Business Park', '555-1005', 'management@officecomplex.com', FALSE),
('Gas Station Chain', '890 Fuel Street', '555-1006', 'security@gaschain.com', TRUE),
('Medical Center', '432 Healthcare Blvd', '555-1007', 'facilities@medcenter.org', FALSE),
('Apartment Complex', '765 Living Space Ave', '555-1008', 'manager@apartments.com', FALSE);

-- Create work orders for the past week (2 per tech per day)
DO $$
DECLARE
    tech_id INTEGER;
    customer_id INTEGER;
    current_date DATE := CURRENT_DATE - INTERVAL '7 days';
    work_types TEXT[] := ARRAY['New Installation', 'System Upgrade', 'Maintenance', 'Repair'];
    work_type TEXT;
    brief_desc TEXT;
    full_sum TEXT;
BEGIN
    FOR d IN 0..7 LOOP
        FOR tech_id IN (SELECT id FROM technicians) LOOP
            FOR i IN 1..2 LOOP
                -- Get random customer
                SELECT id INTO customer_id FROM customers ORDER BY RANDOM() LIMIT 1;
                -- Get random work type
                SELECT work_types[1 + floor(random() * array_length(work_types, 1))] INTO work_type;
                
                -- Create appropriate description based on work type
                CASE work_type
                    WHEN 'New Installation' THEN
                        brief_desc := 'New CCTV system installation';
                        full_sum := 'Complete installation of new surveillance system including cameras, DVR/NVR, and cabling';
                    WHEN 'System Upgrade' THEN
                        brief_desc := 'Upgrade existing cameras to IP system';
                        full_sum := 'Converting analog system to IP cameras, includes new PoE switch and NVR setup';
                    WHEN 'Maintenance' THEN
                        brief_desc := 'Regular system maintenance and cleaning';
                        full_sum := 'Clean all cameras, check connections, update firmware, verify recording';
                    WHEN 'Repair' THEN
                        brief_desc := 'Camera system troubleshooting';
                        full_sum := 'Diagnose and repair issues with cameras not recording/displaying properly';
                END CASE;

                INSERT INTO work_orders (
                    customer_id,
                    title,
                    brief_description,
                    full_summary,
                    status,
                    assigned_technician_id,
                    scheduled_for
                ) VALUES (
                    customer_id,
                    work_type || ' - ' || (SELECT name FROM customers WHERE id = customer_id),
                    brief_desc,
                    full_sum,
                    CASE 
                        WHEN d < 7 THEN 'completed'
                        WHEN d = 7 AND i = 1 THEN 'in_progress'
                        ELSE 'pending'
                    END,
                    tech_id,
                    (current_date + d * INTERVAL '1 day' + (8 + i * 4) * INTERVAL '1 hour')
                );
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- Create future work orders for the next week (2 per tech per day)
DO $$
DECLARE
    tech_id INTEGER;
    customer_id INTEGER;
    future_date DATE := CURRENT_DATE + INTERVAL '1 day';
    work_types TEXT[] := ARRAY['New Installation', 'System Upgrade', 'Maintenance', 'Repair'];
    work_type TEXT;
    brief_desc TEXT;
    full_sum TEXT;
BEGIN
    FOR d IN 0..6 LOOP  -- Next 7 days
        FOR tech_id IN (SELECT id FROM technicians) LOOP
            FOR i IN 1..2 LOOP
                -- Get random customer
                SELECT id INTO customer_id FROM customers ORDER BY RANDOM() LIMIT 1;
                -- Get random work type
                SELECT work_types[1 + floor(random() * array_length(work_types, 1))] INTO work_type;
                
                -- Create appropriate description based on work type
                CASE work_type
                    WHEN 'New Installation' THEN
                        brief_desc := 'New CCTV system installation';
                        full_sum := 'Complete installation of new surveillance system including cameras, DVR/NVR, and cabling';
                    WHEN 'System Upgrade' THEN
                        brief_desc := 'Upgrade existing cameras to IP system';
                        full_sum := 'Converting analog system to IP cameras, includes new PoE switch and NVR setup';
                    WHEN 'Maintenance' THEN
                        brief_desc := 'Regular system maintenance and cleaning';
                        full_sum := 'Clean all cameras, check connections, update firmware, verify recording';
                    WHEN 'Repair' THEN
                        brief_desc := 'Camera system troubleshooting';
                        full_sum := 'Diagnose and repair issues with cameras not recording/displaying properly';
                END CASE;

                INSERT INTO work_orders (
                    customer_id,
                    title,
                    brief_description,
                    full_summary,
                    status,
                    assigned_technician_id,
                    scheduled_for
                ) VALUES (
                    customer_id,
                    work_type || ' - ' || (SELECT name FROM customers WHERE id = customer_id),
                    brief_desc,
                    full_sum,
                    'scheduled',
                    tech_id,
                    (future_date + d * INTERVAL '1 day' + (8 + i * 4) * INTERVAL '1 hour')
                );
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- Add some completed travel logs for past work orders
INSERT INTO travel_logs (work_order_id, technician_id, travel_start_time, travel_end_time)
SELECT 
    wo.id,
    wo.assigned_technician_id,
    wo.scheduled_for - INTERVAL '30 minutes',
    wo.scheduled_for
FROM work_orders wo
WHERE wo.status = 'completed';

-- Add some clock records for technicians
INSERT INTO technician_clock_records (technician_id, truck_id, clock_in_time, clock_out_time)
SELECT 
    t.id as technician_id,
    tr.id as truck_id,
    current_date + INTERVAL '7 hours',
    CASE 
        WHEN EXTRACT(DOW FROM current_date) < 5 THEN current_date + INTERVAL '16 hours'
        ELSE current_date + INTERVAL '13 hours'
    END
FROM technicians t
CROSS JOIN trucks tr
WHERE tr.id != 1
AND t.id = tr.id; 