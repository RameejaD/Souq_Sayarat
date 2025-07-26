#!/usr/bin/env python3
"""
Fix Admin Script
This script fixes the admin password and needs_password_update field.
"""

import sys
import os
import bcrypt

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def fix_admin():
    """Fix admin password and needs_password_update"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Hash password
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        
        # Update admin
        cursor.execute("""
            UPDATE admins 
            SET password_hash = %s, needs_password_update = 0, updated_at = NOW()
            WHERE email = %s
        """, (hashed_password.decode('utf-8'), 'superadmin@souqsayarat.com'))
        
        connection.commit()
        print("✅ Admin password and needs_password_update fixed!")
        
        # Verify the update
        cursor.execute("SELECT * FROM admins WHERE email = %s", ('superadmin@souqsayarat.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Admin updated successfully:")
            print(f"   Email: {admin[1]}")
            print(f"   Is Super Admin: {admin[3]}")
            print(f"   Needs Password Update: {admin[8]}")
        
    except Exception as e:
        print(f"❌ Error fixing admin: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def main():
    """Main function"""
    print("🔧 Fixing Admin")
    print("=" * 20)
    
    if fix_admin():
        print("\n✅ Admin fixed successfully!")
        print("You can now login with:")
        print("Email: superadmin@souqsayarat.com")
        print("Password: admin123")
    else:
        print("\n❌ Failed to fix admin!")

if __name__ == "__main__":
    main() 