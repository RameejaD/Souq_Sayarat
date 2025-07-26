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
        query = "SELECT * FROM admins WHERE email = %s"
        result = execute_query(query, (email,))
        if not result:
            return None
        admin = result[0]
        stored_hash = admin['password_hash']
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
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
    
    def verify_admin_password(self, admin_id, current_password):
        query = "SELECT password_hash FROM admins WHERE id = %s"
        result = execute_query(query, (admin_id,))
        if not result:
            return False
        stored_hash = result[0]['password_hash']
        return bcrypt.checkpw(current_password.encode(), stored_hash.encode())

    def update_admin_password(self, admin_id, new_password):
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        query = "UPDATE admins SET password_hash = %s, updated_at = NOW() WHERE id = %s"
        execute_query(query, (new_hash, admin_id), fetch=False)
        return True
    
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
        query = "SELECT * FROM admins WHERE email = %s"
        result = execute_query(query, (email,))
        return result[0] if result else None

    def save_admin_otp(self, email, otp, expires_at):
        query = """
            INSERT INTO admin_otp (email, otp, expires_at, verified)
            VALUES (%s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE otp=%s, expires_at=%s, verified=0, updated_at=NOW()
        """
        execute_query(query, (email, otp, expires_at, otp, expires_at), fetch=False)

    def get_admin_otp(self, email, otp):
        query = "SELECT * FROM admin_otp WHERE email = %s AND otp = %s"
        result = execute_query(query, (email, otp))
        return result[0] if result else None

    def get_verified_otp_by_email(self, email):
        """Get verified OTP record for an email"""
        query = "SELECT * FROM admin_otp WHERE email = %s AND verified = 1 ORDER BY created_at DESC LIMIT 1"
        result = execute_query(query, (email,))
        return result[0] if result else None

    def mark_admin_otp_verified(self, otp_id):
        query = "UPDATE admin_otp SET verified = 1 WHERE id = %s"
        execute_query(query, (otp_id,), fetch=False)

    def update_admin_password_by_email(self, email, new_password):
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        query = "UPDATE admins SET password_hash = %s, updated_at = NOW() WHERE email = %s"
        execute_query(query, (new_hash, email), fetch=False)
    
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

    def get_user_incident_reports_count(self):
        query = "SELECT COUNT(*) as count FROM reported_users"
        result = execute_query(query)
        return result[0]['count'] if result else 0

    def get_user_incident_reports_list(self):
        query = "SELECT id, reporter_user_id, reported_user_id, reported_reason, reported_at, flag FROM reported_users ORDER BY reported_at DESC"
        return execute_query(query)

    def get_car_rejection_reasons(self):
        query = "SELECT id, rejected_reason FROM car_rejection_reason"
        return execute_query(query)
