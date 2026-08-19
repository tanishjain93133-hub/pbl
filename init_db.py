import os
import sys
import sqlite3
import pymysql
from werkzeug.security import generate_password_hash
from config import Config

def init_mysql():
    print(f"Connecting to MySQL server at {Config.MYSQL_HOST}:{Config.MYSQL_PORT} as '{Config.MYSQL_USER}'...")
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB};")
            cursor.execute(f"USE {Config.MYSQL_DB};")
            
            schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
            seed_path = os.path.join(os.path.dirname(__file__), 'database', 'seed.sql')
            
            print(f"Applying schema from {schema_path}...")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                # Split commands
                for statement in schema_sql.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
            
            print(f"Applying seed data from {seed_path}...")
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
                for statement in seed_sql.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                        
        conn.close()
        print("[SUCCESS] MySQL database 'smart_parking' initialized and seeded successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] MySQL Initialization failed: {e}")
        return False

def init_sqlite():
    db_path = Config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"Initializing SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        vehicle_number TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        vehicle_model TEXT DEFAULT 'Standard',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_number TEXT UNIQUE NOT NULL,
        section TEXT NOT NULL,
        floor TEXT NOT NULL,
        vehicle_type TEXT NOT NULL DEFAULT 'Car',
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        vehicle_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        booking_date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        booking_status TEXT DEFAULT 'booked',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (slot_id) REFERENCES parking_slots(id) ON DELETE RESTRICT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NULL,
        vehicle_number TEXT NOT NULL,
        slot_number TEXT NOT NULL,
        entry_time DATETIME NULL,
        exit_time DATETIME NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed data
    cursor.execute("DELETE FROM parking_history;")
    cursor.execute("DELETE FROM bookings;")
    cursor.execute("DELETE FROM parking_slots;")
    cursor.execute("DELETE FROM vehicles;")
    cursor.execute("DELETE FROM users;")

    admin_hash = generate_password_hash('Admin@123')
    user_hash = generate_password_hash('User@123')

    cursor.execute("INSERT INTO users (id, name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?, ?);",
                   (1, 'System Administrator', 'admin@smartpark.com', '9876543210', admin_hash, 'admin'))
    cursor.execute("INSERT INTO users (id, name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?, ?);",
                   (2, 'Rahul Sharma', 'rahul.sharma@example.com', '9898012345', user_hash, 'user'))
    cursor.execute("INSERT INTO users (id, name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?, ?);",
                   (3, 'Priya Patel', 'priya.patel@example.com', '9825098765', user_hash, 'user'))

    cursor.execute("INSERT INTO vehicles (id, user_id, vehicle_number, vehicle_type, vehicle_model) VALUES (?, ?, ?, ?, ?);",
                   (1, 2, 'GJ01AB1234', 'Car', 'Honda City (Sedan)'))
    cursor.execute("INSERT INTO vehicles (id, user_id, vehicle_number, vehicle_type, vehicle_model) VALUES (?, ?, ?, ?, ?);",
                   (2, 2, 'GJ01CD5678', 'Bike', 'Royal Enfield Classic 350'))
    cursor.execute("INSERT INTO vehicles (id, user_id, vehicle_number, vehicle_type, vehicle_model) VALUES (?, ?, ?, ?, ?);",
                   (3, 3, 'MH02EF9012', 'Car', 'Hyundai Creta (SUV)'))
    cursor.execute("INSERT INTO vehicles (id, user_id, vehicle_number, vehicle_type, vehicle_model) VALUES (?, ?, ?, ?, ?);",
                   (4, 3, 'MH02GH3456', 'Scooter', 'Honda Activa 6G'))

    slots = [
        (1, 'A01', 'Section A - North Wing', 'Ground Floor', 'Car', 'available'),
        (2, 'A02', 'Section A - North Wing', 'Ground Floor', 'Car', 'occupied'),
        (3, 'A03', 'Section A - North Wing', 'Ground Floor', 'Car', 'available'),
        (4, 'A04', 'Section A - North Wing', 'Ground Floor', 'Car', 'available'),
        (5, 'A05', 'Section A - North Wing', 'Ground Floor', 'Bike', 'available'),
        (6, 'A06', 'Section A - North Wing', 'Ground Floor', 'Bike', 'maintenance'),
        (7, 'B01', 'Section B - Central Block', '1st Floor', 'Car', 'available'),
        (8, 'B02', 'Section B - Central Block', '1st Floor', 'Car', 'occupied'),
        (9, 'B03', 'Section B - Central Block', '1st Floor', 'Car', 'available'),
        (10, 'B04', 'Section B - Central Block', '1st Floor', 'Bike', 'available'),
        (11, 'B05', 'Section B - Central Block', '1st Floor', 'Scooter', 'available'),
        (12, 'B06', 'Section B - Central Block', '1st Floor', 'Car', 'available'),
        (13, 'C01', 'Section C - East Wing', 'Basement', 'Car', 'available'),
        (14, 'C02', 'Section C - East Wing', 'Basement', 'Car', 'maintenance'),
    ]
    cursor.executemany("INSERT INTO parking_slots (id, slot_number, section, floor, vehicle_type, status) VALUES (?, ?, ?, ?, ?, ?);", slots)

    cursor.execute("""
    INSERT INTO bookings (id, user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status) 
    VALUES (1, 2, 1, 2, DATE('now', 'localtime'), '09:00', '18:00', 'active');
    """)
    cursor.execute("""
    INSERT INTO bookings (id, user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status) 
    VALUES (2, 3, 3, 8, DATE('now', 'localtime'), '10:30', '16:00', 'active');
    """)
    cursor.execute("""
    INSERT INTO bookings (id, user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status) 
    VALUES (3, 2, 2, 5, DATE('now', '+1 day', 'localtime'), '11:00', '14:00', 'booked');
    """)
    cursor.execute("""
    INSERT INTO bookings (id, user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status) 
    VALUES (4, 3, 4, 11, DATE('now', '-1 day', 'localtime'), '09:00', '13:00', 'completed');
    """)

    cursor.execute("""
    INSERT INTO parking_history (id, booking_id, vehicle_number, slot_number, entry_time, exit_time, status)
    VALUES (1, 1, 'GJ01AB1234', 'A02', DATETIME('now', '-2 hours', 'localtime'), NULL, 'Active');
    """)
    cursor.execute("""
    INSERT INTO parking_history (id, booking_id, vehicle_number, slot_number, entry_time, exit_time, status)
    VALUES (2, 2, 'MH02EF9012', 'B02', DATETIME('now', '-1 hour', 'localtime'), NULL, 'Active');
    """)
    cursor.execute("""
    INSERT INTO parking_history (id, booking_id, vehicle_number, slot_number, entry_time, exit_time, status)
    VALUES (3, 4, 'MH02GH3456', 'B05', DATETIME('now', '-1 day', 'localtime'), DATETIME('now', '-20 hours', 'localtime'), 'Completed');
    """)
    cursor.execute("""
    INSERT INTO parking_history (id, booking_id, vehicle_number, slot_number, entry_time, exit_time, status)
    VALUES (4, NULL, 'GJ01CD5678', 'A05', DATETIME('now', '-2 day', 'localtime'), DATETIME('now', '-40 hours', 'localtime'), 'Completed');
    """)

    conn.commit()
    conn.close()
    print("[SUCCESS] SQLite database initialized and seeded successfully!")
    return True

if __name__ == '__main__':
    print("=== SmartPark Database Setup Utility ===")
    if Config.DB_TYPE == 'mysql':
        success = init_mysql()
        if not success:
            print("Fallback: Initializing SQLite fallback...")
            init_sqlite()
    else:
        init_sqlite()
