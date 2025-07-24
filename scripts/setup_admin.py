#!/usr/bin/env python3
"""
Admin Setup Script for Souq Sayarat
This script sets up the admin tables and creates the initial super admin.
"""

import sys
import os
import bcrypt
import mysql.connector
from mysql.connector import Error

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection

def create_admin_tables():
    """Create admin tables in the database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                is_super_admin TINYINT(1) NOT NULL DEFAULT 0,
                is_subscription_transaction_manager TINYINT(1) NOT NULL DEFAULT 0,
                is_listing_manager TINYINT(1) NOT NULL DEFAULT 0,
                is_user_manager TINYINT(1) NOT NULL DEFAULT 0,
                is_support_manager TINYINT(1) NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                needs_password_update TINYINT(1) NOT NULL DEFAULT 1,
                deleted_at DATETIME NULL
            )
        """)
        
        # Create admin_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id INT NOT NULL,
                session_token VARCHAR(255) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
            )
        """)
        
        # Create admin_activity_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id INT NOT NULL,
                action VARCHAR(100) NOT NULL,
                description TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
            )
        """)
        
        connection.commit()
        print("✅ Admin tables created successfully")
        
    except Error as e:
        print(f"❌ Error creating admin tables: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def create_super_admin(email, password):
    """Create the initial super admin"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"⚠️  Admin with email {email} already exists")
            return True
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert super admin
        cursor.execute("""
            INSERT INTO admins (
                email, password_hash, is_super_admin, is_subscription_transaction_manager,
                is_listing_manager, is_user_manager, is_support_manager, needs_password_update
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            email, hashed_password.decode('utf-8'),
            True, True, True, True, True, 0  # Super admin doesn't need password update
        ))
        
        connection.commit()
        print(f"✅ Super admin created successfully: {email}")
        
    except Error as e:
        print(f"❌ Error creating super admin: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Admin System for Souq Sayarat")
    print("=" * 50)
    
    # Create admin tables
    if not create_admin_tables():
        print("❌ Failed to create admin tables")
        return
    
    # Get super admin credentials
    print("\n📝 Super Admin Setup")
    print("Enter the credentials for the initial super admin:")
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email is required")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password is required")
        return
    
    # Create super admin
    if create_super_admin(email, password):
        print("\n✅ Admin system setup completed successfully!")
        print(f"Super admin email: {email}")
        print("You can now login to the admin panel using these credentials.")
    else:
        print("\n❌ Failed to create super admin")

if __name__ == "__main__":
    main() 