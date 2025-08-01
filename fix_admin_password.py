#!/usr/bin/env python3
"""
Fix Admin Password Script
This script fixes the admin password hash for the given email and password.
"""

import sys
import os
import bcrypt

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def fix_admin_password(email, password):
    """Fix admin password hash"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Update admin password
        cursor.execute("""
            UPDATE admins 
            SET password_hash = %s, needs_password_update = 0, updated_at = NOW()
            WHERE email = %s
        """, (hashed_password.decode('utf-8'), email))
        
        if cursor.rowcount == 0:
            print(f"❌ No admin found with email: {email}")
            return False
        
        connection.commit()
        print(f"✅ Admin password updated successfully for: {email}")
        print(f"   Password: {password}")
        print(f"   Hash: {hashed_password.decode('utf-8')}")
        
        # Verify the update
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Admin verified:")
            print(f"   Email: {admin[1]}")
            print(f"   Is Super Admin: {admin[3]}")
            print(f"   Needs Password Update: {admin[8]}")
        
    except Exception as e:
        print(f"❌ Error fixing admin password: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def create_admin_if_not_exists(email, password, is_super_admin=False):
    """Create admin if it doesn't exist"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"⚠️  Admin with email {email} already exists")
            return True
        
        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert admin
        cursor.execute("""
            INSERT INTO admins (
                email, password_hash, is_super_admin, is_subscription_transaction_manager,
                is_listing_manager, is_user_manager, is_support_manager, needs_password_update
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            email, hashed_password.decode('utf-8'),
            is_super_admin, True, True, True, True, 0
        ))
        
        connection.commit()
        print(f"✅ Admin created successfully: {email}")
        print(f"   Password: {password}")
        print(f"   Hash: {hashed_password.decode('utf-8')}")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def main():
    """Main function"""
    print("🔧 Fixing Admin Password")
    print("=" * 30)
    
    # Fix the specific admin
    email = "user_manager1@example.com"
    password = "user_manager1"
    
    print(f"Fixing admin: {email}")
    print(f"Password: {password}")
    
    # Try to fix existing admin first
    if fix_admin_password(email, password):
        print("\n✅ Admin password fixed successfully!")
        print("You can now login with:")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        print(f"\n⚠️  Admin {email} not found, creating new admin...")
        
        if create_admin_if_not_exists(email, password, is_super_admin=False):
            print("\n✅ Admin created successfully!")
            print("You can now login with:")
            print(f"Email: {email}")
            print(f"Password: {password}")
        else:
            print("\n❌ Failed to create admin!")

if __name__ == "__main__":
    main() 