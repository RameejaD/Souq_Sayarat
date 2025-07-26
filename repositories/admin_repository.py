from utils.db import execute_query
from datetime import datetime, timedelta
import bcrypt
import secrets
import hashlib
import os

class AdminRepository:
    def is_admin(self, user_id):
        """Check if a user is an admin"""
        query = """
            SELECT 1
            FROM users
            WHERE id = %s AND user_type = 'admin'
        """
        results = execute_query(query, (user_id,))
        return bool(results)
    
    def authenticate_admin(self, email, password):
        """Authenticate admin with email and password"""
        query = """
            SELECT id, email, password_hash, is_super_admin, is_subscription_transaction_manager, 
                   is_listing_manager, is_user_manager, is_support_manager, needs_password_update
            FROM admins
            WHERE email = %s AND deleted_at IS NULL
        """
        results = execute_query(query, (email,))
        
        if not results:
            return None
        
        admin = results[0]
        
        # Verify password using Argon2 for admin passwords
        if self.verify_admin_password(password, admin['password_hash']):
            return admin
        
        return None
    
    def hash_admin_password(self, password, use_static_salt=False):
        """Hash admin password using bcrypt. Use static salt for super admin, random salt for others."""
        import bcrypt
        if use_static_salt:
            # Use a valid static bcrypt salt (generated with bcrypt.gensalt(12))
            static_salt = b"$2b$12$eImiTXuWVxfM37uY4JANjQ"  # Example valid salt
            hashed = bcrypt.hashpw(password.encode('utf-8'), static_salt)
            return hashed.decode('utf-8')
        else:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
            return hashed.decode('utf-8')
    
    def verify_admin_password(self, password, stored_hash):
        """Verify admin password using static bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return False
    
    def create_admin_session(self, admin_id, session_token, expires_at):
        """Create a new admin session"""
        query = """
            INSERT INTO admin_sessions (admin_id, session_token, expires_at)
            VALUES (%s, %s, %s)
        """
        execute_query(query, (admin_id, session_token, expires_at), fetch=False)
    
    def get_admin_by_session(self, session_token):
        """Get admin by session token"""
        query = """
            SELECT a.id, a.email, a.is_super_admin, a.is_subscription_transaction_manager,
                   a.is_listing_manager, a.is_user_manager, a.is_support_manager, a.needs_password_update
            FROM admins a
            JOIN admin_sessions s ON a.id = s.admin_id
            WHERE s.session_token = %s AND s.expires_at > NOW() AND a.deleted_at IS NULL
        """
        results = execute_query(query, (session_token,))
        return results[0] if results else None
    
    def invalidate_session(self, session_token):
        """Invalidate admin session"""
        query = """
            DELETE FROM admin_sessions
            WHERE session_token = %s
        """
        execute_query(query, (session_token,), fetch=False)
    
    def get_admin_by_id(self, admin_id):
        """Get admin by ID"""
        query = """
            SELECT id, email, is_super_admin, is_subscription_transaction_manager,
                   is_listing_manager, is_user_manager, is_support_manager,
                   created_at, updated_at, needs_password_update
            FROM admins
            WHERE id = %s AND deleted_at IS NULL
        """
        results = execute_query(query, (admin_id,))
        return results[0] if results else None
    
    def create_admin(self, email, password, permissions):
        """Create a new admin"""
        # Use static hash for super admin, random hash for others
        is_super_admin = permissions.get('is_super_admin', False)
        if is_super_admin and email.lower() == 'superadmin@souqsayarat.com':
            hashed_password = self.hash_admin_password(password, use_static_salt=True)
        else:
            hashed_password = self.hash_admin_password(password, use_static_salt=False)
        
        query = """
            INSERT INTO admins (email, password_hash, is_super_admin, is_subscription_transaction_manager,
                              is_listing_manager, is_user_manager, is_support_manager, needs_password_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (
            email, hashed_password,
            is_super_admin,
            permissions.get('is_subscription_transaction_manager', False),
            permissions.get('is_listing_manager', False),
            permissions.get('is_user_manager', False),
            permissions.get('is_support_manager', False),
            1  # needs_password_update = 1 for new sub admins
        ), fetch=False)
        
        # Get the created admin
        return self.get_admin_by_email(email)
    
    def get_admin_by_email(self, email):
        """Get admin by email"""
        query = """
            SELECT id, email, is_super_admin, is_subscription_transaction_manager,
                   is_listing_manager, is_user_manager, is_support_manager,
                   created_at, updated_at, needs_password_update
            FROM admins
            WHERE email = %s AND deleted_at IS NULL
        """
        results = execute_query(query, (email,))
        return results[0] if results else None
    
    def update_admin_permissions(self, admin_id, permissions):
        """Update admin permissions"""
        query = """
            UPDATE admins
            SET is_super_admin = %s, is_subscription_transaction_manager = %s,
                is_listing_manager = %s, is_user_manager = %s, is_support_manager = %s,
                updated_at = NOW()
            WHERE id = %s AND deleted_at IS NULL
        """
        execute_query(query, (
            permissions.get('is_super_admin', False),
            permissions.get('is_subscription_transaction_manager', False),
            permissions.get('is_listing_manager', False),
            permissions.get('is_user_manager', False),
            permissions.get('is_support_manager', False),
            admin_id
        ), fetch=False)
    
    def update_admin_password(self, admin_id, new_password):
        """Update admin password. Use static hash for super admin, random hash for others."""
        # Get admin to check if super admin
        admin = self.get_admin_by_id(admin_id)
        use_static_salt = admin and admin.get('is_super_admin') and admin.get('email', '').lower() == 'superadmin@souqsayarat.com'
        hashed_password = self.hash_admin_password(new_password, use_static_salt=use_static_salt)
        
        query = """
            UPDATE admins
            SET password_hash = %s, needs_password_update = 0, updated_at = NOW()
            WHERE id = %s AND deleted_at IS NULL
        """
        execute_query(query, (hashed_password, admin_id), fetch=False)
    
    def delete_admin(self, admin_id):
        """Soft delete an admin"""
        query = """
            UPDATE admins
            SET deleted_at = NOW()
            WHERE id = %s
        """
        execute_query(query, (admin_id,), fetch=False)
    
    def get_all_admins(self, page=1, limit=10):
        """Get all admins with pagination, excluding super admins"""
        offset = (page - 1) * limit
        
        query = """
            SELECT id, email, is_super_admin, is_subscription_transaction_manager,
                   is_listing_manager, is_user_manager, is_support_manager,
                   created_at, updated_at, needs_password_update
            FROM admins
            WHERE deleted_at IS NULL AND is_super_admin = 0
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        admins = execute_query(query, (limit, offset))
        
        # Get total count (excluding super admins)
        count_query = "SELECT COUNT(*) as total FROM admins WHERE deleted_at IS NULL AND is_super_admin = 0"
        count_result = execute_query(count_query)
        total = count_result[0]['total'] if count_result else 0
        
        return admins, total
    
    def log_admin_activity(self, admin_id, action, description, ip_address=None, user_agent=None):
        """Log admin activity"""
        query = """
            INSERT INTO admin_activity_log (admin_id, action, description, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(query, (admin_id, action, description, ip_address, user_agent), fetch=False)
    
    def get_admin_activity_log(self, admin_id=None, page=1, limit=10):
        """Get admin activity log"""
        offset = (page - 1) * limit
        
        where_clause = ""
        params = []
        
        if admin_id:
            where_clause = "WHERE admin_id = %s"
            params.append(admin_id)
        
        query = f"""
            SELECT al.id, al.admin_id, al.action, al.description, al.ip_address,
                   al.user_agent, al.created_at, a.email as admin_email
            FROM admin_activity_log al
            JOIN admins a ON al.admin_id = a.id
            {where_clause}
            ORDER BY al.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        logs = execute_query(query, params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM admin_activity_log al
            {where_clause}
        """
        count_result = execute_query(count_query, params[:-2] if params else [])
        total = count_result[0]['total'] if count_result else 0
        
        return logs, total

    def get_report(self, report_id):
        """Get a user report by ID"""
        query = """
            SELECT id, reporter_id, reported_user_id, reason, description, status, resolution, created_at, updated_at
            FROM user_reports
            WHERE id = %s
        """
        results = execute_query(query, (report_id,))
        return results[0] if results else None
    
    def get_reports(self, page=1, limit=10, filters=None):
        """Get user reports with pagination"""
        offset = (page - 1) * limit
        filters = filters or {}
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if 'status' in filters:
            where_clauses.append("status = %s")
            params.append(filters['status'])
        
        # Construct final query
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get reports with pagination
        query = f"""
            SELECT r.id, r.reporter_id, r.reported_user_id, r.reason, r.description, r.status, r.resolution,
                   r.created_at, r.updated_at,
                   reporter.first_name as reporter_first_name, reporter.last_name as reporter_last_name,
                   reported.first_name as reported_first_name, reported.last_name as reported_last_name
            FROM user_reports r
            JOIN users reporter ON r.reporter_id = reporter.id
            JOIN users reported ON r.reported_user_id = reported.id
            {where_clause}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        reports = execute_query(query, params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM user_reports
            {where_clause}
        """
        count_result = execute_query(count_query, params[:-2] if params else [])
        total = count_result[0]['total'] if count_result else 0
        
        return reports, total
    
    def resolve_report(self, report_id, resolution=None):
        """Resolve a user report"""
        query = """
            UPDATE user_reports
            SET status = 'resolved', resolution = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (resolution, datetime.now(), report_id), fetch=False)

    def get_subjects(self):
        """Get all subjects from the subjects table"""
        query = """
            SELECT id, subject 
            FROM subjects 
            ORDER BY subject
        """
        return execute_query(query)

    def get_contact_info(self):
        """Get contact information"""
        return {
            "call_us": "9613123123",
            "email_us": "info@souqsayarat.com",
            "whatsapp": "9613123123"
        }

    def save_contact_message(self, user_id, subject, message):
        """Save contact message to database"""
        query = """
            INSERT INTO contact_us (user_id, subject, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """
        execute_query(query, (user_id, subject, message), fetch=False)
        return True

    def search_users(self, search_query, page=1, limit=10):
        """Search users by name, email, or phone number with closest matches and pagination"""
        try:
            search_pattern = f"%{search_query}%"
            offset = (page - 1) * limit
            query = """
                SELECT 
                    id, first_name, last_name, email, phone_number, 
                    user_type, is_verified
                FROM users 
                WHERE deleted_at IS NULL
                AND (
                    first_name LIKE %s 
                    OR last_name LIKE %s 
                    OR CONCAT(first_name, ' ', last_name) LIKE %s
                    OR email LIKE %s 
                    OR phone_number LIKE %s
                )
                ORDER BY 
                    CASE 
                        WHEN first_name LIKE %s OR last_name LIKE %s THEN 1
                        WHEN email LIKE %s THEN 2
                        WHEN phone_number LIKE %s THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT %s OFFSET %s
            """
            params = [
                search_pattern, search_pattern, search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern, search_pattern,
                limit, offset
            ]
            users = execute_query(query, params)
            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM users
                WHERE deleted_at IS NULL
                AND (
                    first_name LIKE %s 
                    OR last_name LIKE %s 
                    OR CONCAT(first_name, ' ', last_name) LIKE %s
                    OR email LIKE %s 
                    OR phone_number LIKE %s
                )
            """
            count_params = [search_pattern]*5
            count_result = execute_query(count_query, count_params)
            total = count_result[0]['total'] if count_result else 0
            return users, total
        except Exception as e:
            print(f"Error in search_users repository: {str(e)}")
            raise e

    def get_reported_users(self, page=1, limit=10):
        offset = (page - 1) * limit
        query = '''
            SELECT r.id as report_id, r.reported_user_id, r.reporter_user_id, r.flag, r.reported_at,
                   u_reported.first_name as reported_first_name, u_reported.last_name as reported_last_name, u_reported.email as reported_email, u_reported.phone_number as reported_phone_number, u_reported.user_type as reported_user_type, u_reported.is_verified as reported_is_verified,
                   u_reporter.id as reporter_id, u_reporter.first_name as reporter_first_name, u_reporter.last_name as reporter_last_name
            FROM reported_users r
            JOIN users u_reported ON r.reported_user_id = u_reported.id
            JOIN users u_reporter ON r.reporter_user_id = u_reporter.id
            ORDER BY r.reported_at DESC
            LIMIT %s OFFSET %s
        '''
        results = execute_query(query, (limit, offset))
        # For each reported_user_id, get the total report count
        count_query = 'SELECT COUNT(*) as total FROM reported_users'
        total = execute_query(count_query)[0]['total']
        # Optionally, add report_count for each reported_user_id
        report_counts = {}
        for row in results:
            uid = row['reported_user_id']
            if uid not in report_counts:
                count = execute_query('SELECT COUNT(*) as cnt FROM reported_users WHERE reported_user_id = %s', (uid,))[0]['cnt']
                report_counts[uid] = count
            row['report_count'] = report_counts[uid]
            # Add reporter_name for convenience
            row['reporter_name'] = f"{row['reporter_first_name']} {row['reporter_last_name']}"
        return {'success': True, 'data': results, 'total': total, 'page': page, 'limit': limit}

    def flag_reported_user(self, reported_user_id):
        # Update flag for all rows with this reported_user_id
        update_query = 'UPDATE reported_users SET flag = 1 WHERE reported_user_id = %s'
        execute_query(update_query, (reported_user_id,), fetch=False)
        # Check if the update was successful
        check_query = 'SELECT COUNT(*) as cnt FROM reported_users WHERE reported_user_id = %s AND flag = 1'
        result = execute_query(check_query, (reported_user_id,))
        if result and result[0]['cnt'] > 0:
            return True
        return False

    def ban_reported_user(self, report_id, ban_reason):
        # Get reported_user_id from report
        get_query = 'SELECT reported_user_id FROM reported_users WHERE id = %s'
        result = execute_query(get_query, (report_id,))
        if not result:
            return False
        user_id = result[0]['reported_user_id']
        # Ban user
        ban_query = 'UPDATE users SET is_banned = 1, ban_reason = %s WHERE id = %s'
        execute_query(ban_query, (ban_reason, user_id), fetch=False)
        return True

    def get_watchlist(self, page=1, limit=10):
        offset = (page - 1) * limit
        query = '''
            SELECT DISTINCT u.id, u.first_name, u.last_name, u.email, u.phone_number, u.user_type, u.is_verified,
                (SELECT COUNT(*) FROM cars WHERE user_id = u.id) as total_listings
            FROM users u
            JOIN reported_users r ON u.id = r.reported_user_id
            WHERE r.flag = 1
            ORDER BY u.id DESC
            LIMIT %s OFFSET %s
        '''
        users = execute_query(query, (limit, offset))
        count_query = '''SELECT COUNT(DISTINCT u.id) as total FROM users u JOIN reported_users r ON u.id = r.reported_user_id WHERE r.flag = 1'''
        total = execute_query(count_query)[0]['total']
        # Optionally, fetch listing details for each user
        for user in users:
            listings_query = 'SELECT id, make, model, year, status, approval FROM cars WHERE user_id = %s'
            user['listings'] = execute_query(listings_query, (user['id'],))
        return {'success': True, 'data': users, 'total': total, 'page': page, 'limit': limit}
