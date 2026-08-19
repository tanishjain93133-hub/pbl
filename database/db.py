import os
import sqlite3
import pymysql
import pymysql.cursors
from flask import g
from config import Config

def get_db():
    """
    Get a database connection stored in Flask's application context 'g'.
    Attempts MySQL connection if configured. If MySQL server is unreachable,
    gracefully falls back to SQLite so local testing is seamless without crashing.
    """
    if 'db' not in g:
        if Config.DB_TYPE == 'mysql':
            try:
                g.db = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                    charset='utf8mb4'
                )
                g.db_type = 'mysql'
            except Exception as e:
                print(f"[SmartPark DB Notice] Could not connect to MySQL ({e}). Using SQLite database engine for runtime stability.")
                g.db = get_sqlite_connection()
                g.db_type = 'sqlite'
        else:
            g.db = get_sqlite_connection()
            g.db_type = 'sqlite'

    return g.db

def get_sqlite_connection():
    os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys in SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

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
