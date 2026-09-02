import sqlite3
import json
import os
from datetime import datetime

DB_NAME = 'equipment.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'super',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Equipment data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_data (
            asset_number TEXT PRIMARY KEY,
            asset_desc TEXT NOT NULL,
            manufacturer TEXT,
            parent_asset TEXT,
            asset_owner TEXT,
            serial_no TEXT,
            location TEXT,
            po_number TEXT,
            acceptance_date TEXT,
            calibration_date TEXT,
            current_detail TEXT,
            photos TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Equipment status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equip_status (
            equipment_key TEXT PRIMARY KEY,
            status TEXT DEFAULT 'IN',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # History records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_time TEXT NOT NULL,
            status TEXT NOT NULL,
            job_type TEXT NOT NULL,
            purpose TEXT,
            et TEXT,
            set_person TEXT,
            physicist TEXT,
            others TEXT,
            remarks TEXT,
            signature TEXT,
            record_status TEXT DEFAULT 'Verified',
            edit_history TEXT DEFAULT '[]',
            equipment_details TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # DB logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS db_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            record_id TEXT,
            details TEXT,
            user_name TEXT,
            reason TEXT,
            user_role TEXT,
            ip_address TEXT,
            browser TEXT,
            device_type TEXT,
            user_agent TEXT,
            additional_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pokes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            purpose TEXT,
            from_user TEXT,
            to_user TEXT,
            to_role TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Site passwords table (for the password protection)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_passwords (
            id INTEGER PRIMARY KEY DEFAULT 0,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    
    # Insert default site password hash (for "DRws24685868#")
    cursor.execute("SELECT * FROM site_passwords WHERE id = 0")
    if not cursor.fetchone():
        # This is a SHA-256 hash placeholder - you should use the correct hash
        cursor.execute("INSERT INTO site_passwords (id, password_hash) VALUES (0, '6a5c1b5f6e8c9a7b3d4e2f1a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c')")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# Run initialization
if __name__ == '__main__':
    init_database()
