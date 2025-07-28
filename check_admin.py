#!/usr/bin/env python3
"""
Check Admin Script
This script checks if the admin exists in the database.
"""

import sys
import os
import bcrypt

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def check_admin_exists():
    """Check if admin exists in database"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if admins table exists
        cursor.execute("SHOW TABLES LIKE 'admins'")
        if not cursor.fetchone():
            print("❌ Admins table does not exist!")
            return False
        
        # Check if admin exists
        cursor.execute("SELECT * FROM admins WHERE email = %s", ('superadmin@souqsayarat.com',))
        admin = cursor.fetchone()
        
        if admin:
            print("✅ Admin exists in database:")
            print(f"   ID: {admin['id']}")
            print(f"   Email: {admin['email']}")
            print(f"   Is Super Admin: {admin['is_super_admin']}")
            print(f"   Needs Password Update: {admin['needs_password_update']}")
            print(f"   Deleted At: {admin.get('deleted_at', 'NULL')}")
            
            # Test password
            test_password = "admin123"
            if bcrypt.checkpw(test_password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
                print("✅ Password verification successful!")
                return True
            else:
                print("❌ Password verification failed!")
                return False
        else:
            print("❌ Admin does not exist in database!")
            return False
        
    except Exception as e:
        print(f"❌ Error checking admin: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_admin_manually():
    """Create admin manually"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Hash password
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        
        # Insert super admin
        cursor.execute("""
            INSERT INTO admins (
                email, password_hash, is_super_admin, is_subscription_transaction_manager,
                is_listing_manager, is_user_manager, is_support_manager, needs_password_update
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'superadmin@souqsayarat.com', hashed_password.decode('utf-8'),
            True, True, True, True, True, 0
        ))
        
        connection.commit()
        print("✅ Super admin created manually!")
        
    except Exception as e:
        print(f"❌ Error creating admin manually: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def main():
    """Main function"""
    print("🔍 Checking Admin Database")
    print("=" * 30)
    
    if check_admin_exists():
        print("\n✅ Admin exists and password is correct!")
        print("You should be able to login now.")
    else:
        print("\n❌ Admin does not exist or password is incorrect!")
        print("Creating admin manually...")
        
        if create_admin_manually():
            print("✅ Admin created successfully!")
            print("Try logging in again with:")
            print("Email: superadmin@souqsayarat.com")
            print("Password: admin123")
        else:
            print("❌ Failed to create admin!")

if __name__ == "__main__":
    main() 