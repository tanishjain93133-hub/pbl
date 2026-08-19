import os
import sqlite3
import pymysql
import pymysql.cursors
from flask import g
from config import Config

_mysql_available = True

def get_db():
    """
    Get a database connection stored in Flask's application context 'g'.
    Attempts MySQL connection if configured. If MySQL server is unreachable,
    gracefully falls back to SQLite so local testing and serverless deployments work seamlessly.
    """
    global _mysql_available
    if 'db' not in g:
        if Config.DB_TYPE == 'mysql' and _mysql_available:
            try:
                g.db = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                    charset='utf8mb4',
                    connect_timeout=1
                )
                g.db_type = 'mysql'
            except Exception as e:
                _mysql_available = False
                print(f"[SmartPark DB Notice] MySQL unreachable ({e}). Using SQLite database engine.")
                g.db = get_sqlite_connection()
                g.db_type = 'sqlite'
        else:
            g.db = get_sqlite_connection()
            g.db_type = 'sqlite'

    return g.db

def get_sqlite_connection():
    db_path = Config.SQLITE_DB_PATH
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys in SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Auto-initialize schema and seed data if database is empty
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        _auto_seed_sqlite(conn)
    cursor.close()
    
    return conn

def _auto_seed_sqlite(conn):
    """Auto-populates SQLite with schema and initial seed data for zero-config deployments."""
    try:
        from werkzeug.security import generate_password_hash
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vehicle_number TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_model TEXT DEFAULT 'Standard',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT UNIQUE NOT NULL,
            section TEXT NOT NULL,
            floor TEXT NOT NULL,
            vehicle_type TEXT NOT NULL DEFAULT 'Car',
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

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
        cursor.close()
    except Exception as e:
        print(f"[SmartPark DB Seed Notice] Auto-seed error: {e}")

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return list of dicts (or single dict if one=True).
    Automatically adapts placeholders for MySQL (%s) vs SQLite (?).
    """
    db = get_db()
    is_sqlite = (getattr(g, 'db_type', 'mysql') == 'sqlite')
    
    if is_sqlite:
        # Translate %s placeholder to ? for sqlite
        sqlite_query = query.replace('%s', '?')
        # Adapt common MySQL functions for SQLite compatibility if needed
        sqlite_query = sqlite_query.replace('CURDATE()', "DATE('now', 'localtime')")
        sqlite_query = sqlite_query.replace('NOW()', "DATETIME('now', 'localtime')")
        cursor = db.cursor()
        cursor.execute(sqlite_query, args)
        rv = cursor.fetchall()
        cursor.close()
        results = [dict(row) for row in rv]
        return (results[0] if results else None) if one else results
    else:
        with db.cursor() as cursor:
            cursor.execute(query, args)
            results = cursor.fetchall()
            return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    """
    Execute an INSERT, UPDATE, DELETE query.
    Returns:
        lastrowid (for INSERT) or rowcount (for UPDATE/DELETE)
    """
    db = get_db()
    is_sqlite = (getattr(g, 'db_type', 'mysql') == 'sqlite')
    
    if is_sqlite:
        sqlite_query = query.replace('%s', '?')
        sqlite_query = sqlite_query.replace('CURDATE()', "DATE('now', 'localtime')")
        sqlite_query = sqlite_query.replace('NOW()', "DATETIME('now', 'localtime')")
        cursor = db.cursor()
        cursor.execute(sqlite_query, args)
        db.commit()
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        cursor.close()
        return last_id if last_id else row_count
    else:
        with db.cursor() as cursor:
            cursor.execute(query, args)
            db.commit()
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            return last_id if last_id else row_count
