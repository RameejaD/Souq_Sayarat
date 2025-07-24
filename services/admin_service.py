from repositories.admin_repository import AdminRepository
from repositories.car_repository import CarRepository
from repositories.user_repository import UserRepository
from datetime import datetime, timedelta
from utils.db import execute_query
import secrets
import hashlib
import os
import random
import string

class AdminService:
    def __init__(self):
        self.admin_repository = AdminRepository()
        self.car_repository = CarRepository()
        self.user_repository = UserRepository()
    
    def generate_admin_token(self):
        """Generate a 256-bit token for admin sessions"""
        # Generate 32 bytes (256 bits) of random data
        random_bytes = secrets.token_bytes(32)
        # Convert to hex string for storage
        token = random_bytes.hex()
        return token
    
    def authenticate_admin(self, email, password, request):
        """Authenticate admin and create session"""
        admin = self.admin_repository.authenticate_admin(email, password)
        
        if not admin:
            return {
                'success': False,
                'message': 'Invalid email or password',
                'status_code': 401
            }
        
        # Create session token (256 bits)
        session_token = self.generate_admin_token()
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
        
        # Create session
        self.admin_repository.create_admin_session(admin['id'], session_token, expires_at)
        
        # Log activity
        self.admin_repository.log_admin_activity(
            admin['id'],
            'login',
            f'Admin logged in from {request.remote_addr}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        # If needs_password_update is 1, return special message
        if admin.get('needs_password_update', 0) == 1:
            return {
                'success': True,
                'session_token': session_token,
                'admin': {
                    'id': admin['id'],
                    'email': admin['email'],
                    'is_super_admin': admin['is_super_admin'],
                    'is_subscription_transaction_manager': admin['is_subscription_transaction_manager'],
                    'is_listing_manager': admin['is_listing_manager'],
                    'is_user_manager': admin['is_user_manager'],
                    'is_support_manager': admin['is_support_manager'],
                    'needs_password_update': 1
                },
                'message': 'Please update the password',
                'status_code': 200
            }
        
        return {
            'success': True,
            'session_token': session_token,
            'admin': {
                'id': admin['id'],
                'email': admin['email'],
                'is_super_admin': admin['is_super_admin'],
                'is_subscription_transaction_manager': admin['is_subscription_transaction_manager'],
                'is_listing_manager': admin['is_listing_manager'],
                'is_user_manager': admin['is_user_manager'],
                'is_support_manager': admin['is_support_manager'],
                'needs_password_update': admin['needs_password_update']
            },
            'message': 'Login successful',
            'status_code': 200
        }
    
    def logout_admin(self, session_token, request):
        """Logout admin and invalidate session"""
        admin = self.admin_repository.get_admin_by_session(session_token)
        
        if admin:
            # Log activity
            self.admin_repository.log_admin_activity(
                admin['id'],
                'logout',
                f'Admin logged out from {request.remote_addr}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )
        
        # Invalidate session
        self.admin_repository.invalidate_session(session_token)
        
        return {
            'success': True,
            'message': 'Logged out successfully',
            'status_code': 200
        }
    
    def get_admin_by_session(self, session_token):
        """Get admin by session token"""
        return self.admin_repository.get_admin_by_session(session_token)
    
    def update_admin_password(self, admin_id, current_password, new_password, request, force_update=False):
        """Update admin password. If force_update is True, skip current password check (for initial password update)."""
        # Get admin details
        admin = self.admin_repository.get_admin_by_id(admin_id)
        if not admin:
            return {
                'success': False,
                'message': 'Admin not found',
                'status_code': 404
            }
        if not force_update:
            # Verify current password using the new repository method
            if not self.admin_repository.verify_admin_password(admin_id, current_password):
                return {
                    'success': False,
                    'message': 'Please enter your current password to proceed with changing your password',
                    'status_code': 401
                }
        # Update password
        self.admin_repository.update_admin_password(admin_id, new_password)
        # Log activity
        self.admin_repository.log_admin_activity(
            admin_id,
            'password_update',
            'Admin updated password',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        return {
            'success': True,
            'message': 'Password updated successfully',
            'status_code': 200
        }
    
    def create_admin(self, email, password, permissions, created_by_admin_id, request):
        """Create a new admin (only super admin can do this)"""
        # Check if admin exists
        existing_admin = self.admin_repository.get_admin_by_email(email)
        if existing_admin:
            return {
                'success': False,
                'message': 'Admin with this email already exists',
                'status_code': 409
            }
        
        # Create admin
        admin = self.admin_repository.create_admin(email, password, permissions)
        
        # Log activity
        self.admin_repository.log_admin_activity(
            created_by_admin_id,
            'create_admin',
            f'Created new admin: {email}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return {
            'success': True,
            'admin': admin,
            'status_code': 201
        }
    
    def update_admin_permissions(self, admin_id, permissions, updated_by_admin_id, request):
        """Update admin permissions"""
        # Check if admin exists
        admin = self.admin_repository.get_admin_by_id(admin_id)
        if not admin:
            return {
                'success': False,
                'message': 'Admin not found',
                'status_code': 404
            }
        
        # Update permissions
        self.admin_repository.update_admin_permissions(admin_id, permissions)
        
        # Log activity
        self.admin_repository.log_admin_activity(
            updated_by_admin_id,
            'update_admin_permissions',
            f'Updated permissions for admin ID: {admin_id}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return {
            'success': True,
            'message': 'Admin permissions updated successfully',
            'status_code': 200
        }
    
    def delete_admin(self, admin_id, deleted_by_admin_id, request):
        """Delete an admin"""
        # Check if admin exists
        admin = self.admin_repository.get_admin_by_id(admin_id)
        if not admin:
            return {
                'success': False,
                'message': 'Admin not found',
                'status_code': 404
            }
        
        # Prevent deleting self
        if admin_id == deleted_by_admin_id:
            return {
                'success': False,
                'message': 'Cannot delete your own account',
                'status_code': 400
            }
        
        # Delete admin
        self.admin_repository.delete_admin(admin_id)
        
        # Log activity
        self.admin_repository.log_admin_activity(
            deleted_by_admin_id,
            'delete_admin',
            f'Deleted admin: {admin["email"]}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return {
            'success': True,
            'message': 'Admin deleted successfully',
            'status_code': 200
        }
    
    def get_all_admins(self, page=1, limit=10):
        """Get all admins with pagination"""
        admins, total = self.admin_repository.get_all_admins(page, limit)
        
        return {
            'admins': admins,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            },
            'status_code': 200
        }
    
    def get_admin_activity_log(self, admin_id=None, page=1, limit=10):
        """Get admin activity log"""
        logs, total = self.admin_repository.get_admin_activity_log(admin_id, page, limit)
        
        return {
            'logs': logs,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            },
            'status_code': 200
        }
    
    def is_admin(self, user_id):
        """Check if a user is an admin"""
        return self.admin_repository.is_admin(user_id)
    
    def get_dashboard(self):
        """Get admin dashboard data"""
        # Get counts
        cars_count = self.car_repository.get_cars_count()
        pending_cars_count = self.car_repository.get_cars_count(status='pending')
        sold_cars_count = self.car_repository.get_cars_count(status='sold')
        users_count = self.user_repository.get_users_count()
        dealers_count = self.user_repository.get_users_count(user_type='dealer')
        
        # Get recent activity
        recent_cars = self.car_repository.get_recent_cars(limit=5)
        recent_users = self.user_repository.get_recent_users(limit=5)
        
        return {
            'counts': {
                'cars': cars_count,
                'pending_cars': pending_cars_count,
                'sold_cars': sold_cars_count,
                'users': users_count,
                'dealers': dealers_count
            },
            'recent_activity': {
                'cars': recent_cars,
                'users': recent_users
            },
            'status_code': 200
        }
    
    def get_pending_cars(self, page=1, limit=10):
        """Get pending car listings for approval"""
        # Get pending cars with pagination
        cars, total = self.car_repository.get_cars(
            page=page,
            limit=limit,
            filters={'approval': 'pending'}
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'cars': cars,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            },
            'status_code': 200
        }
    
    def approve_car(self, car_id):
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found',
                'status_code': 404
            }
        # Check if car is pending approval
        if car['approval'] != 'pending':
            return {
                'success': False,
                'message': 'Car listing is not pending approval',
                'status_code': 400
            }
        # Approve car - update approval to approved and status to unsold
        query = """
            UPDATE cars
            SET approval = 'approved', status = 'unsold', sold_at = NULL, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), car_id), fetch=False)
        # Fetch user info
        user_id = car.get('user_id')
        user = self.user_repository.get_user_by_id(user_id) if user_id else None
        return {
            'message': 'Car listing approved successfully',
            'userId': user_id,
            'first_name': user.get('first_name') if user else None,
            'last_name': user.get('last_name') if user else None,
            'phone_number': user.get('phone_number') if user else None,
            'email': user.get('email') if user else None,
            'success': True,
            'status_code': 200
        }
    
    def reject_car(self, car_id, reason, admin_rejection_comment=None):
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found',
                'status_code': 404
            }
        # Check if car is pending approval
        if car['approval'] != 'pending':
            return {
                'success': False,
                'message': 'Car listing is not pending approval',
                'status_code': 400
            }
        # Reject car - update approval to rejected, add rejection reason and admin comment
        self.car_repository.reject_car(car_id, reason, admin_rejection_comment)
        # Fetch user info
        user_id = car.get('user_id')
        user = self.user_repository.get_user_by_id(user_id) if user_id else None
        return {
            'success': True,
            'userId': user_id,
            'first_name': user.get('first_name') if user else None,
            'last_name': user.get('last_name') if user else None,
            'phone_number': user.get('phone_number') if user else None,
            'email': user.get('email') if user else None,
            'rejection_reason': reason,
            'status_code': 200
        }
    
    def mark_as_sold(self, car_id):
        """Mark a car as sold"""
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found',
                'status_code': 404
            }
        
        # Check if car is available
        if car['status'] != 'available':
            return {
                'success': False,
                'message': 'Car listing is not available',
                'status_code': 400
            }
        
        # Mark as sold
        query = """
            UPDATE cars
            SET status = 'sold', sold_at = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), datetime.now(), car_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def get_users(self, page=1, limit=10, search=None, user_type=None):
        """Get all users with pagination and filtering"""
        # Get users with filters
        users, total = self.user_repository.get_users(
            page=page,
            limit=limit,
            search=search,
            user_type=user_type
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'users': users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            },
            'status_code': 200
        }
    
    def verify_user(self, user_id):
        """Verify a user (for dealers)"""
        # Check if user exists
        user = self.user_repository.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }
        
        # Check if user is already verified
        if user['is_verified']:
            return {
                'success': False,
                'message': 'User is already verified',
                'status_code': 400
            }
        
        # Verify user
        query = """
            UPDATE users
            SET is_verified = 1, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), user_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def ban_user(self, user_id, reason=None):
        """Ban a user"""
        # Check if user exists
        user = self.user_repository.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }
        
        # Check if user is already banned
        if user['is_banned']:
            return {
                'success': False,
                'message': 'User is already banned',
                'status_code': 400
            }
        
        # Ban user
        query = """
            UPDATE users
            SET is_banned = 1, ban_reason = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (reason, datetime.now(), user_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def unban_user(self, user_id):
        """Unban a user"""
        # Check if user exists
        user = self.user_repository.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'User not found',
                'status_code': 404
            }
        
        # Check if user is not banned
        if not user['is_banned']:
            return {
                'success': False,
                'message': 'User is not banned',
                'status_code': 400
            }
        
        # Unban user
        query = """
            UPDATE users
            SET is_banned = 0, ban_reason = NULL, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), user_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def get_reports(self, page=1, limit=10, status=None):
        """Get user reports with pagination"""
        filters = {}
        if status:
            filters['status'] = status
        
        reports, total = self.admin_repository.get_reports(page, limit, filters)
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'reports': reports,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            },
            'status_code': 200
        }
    
    def resolve_report(self, report_id, resolution=None):
        """Resolve a user report"""
        # Check if report exists
        report = self.admin_repository.get_report(report_id)
        
        if not report:
            return {
                'success': False,
                'message': 'Report not found',
                'status_code': 404
            }
        
        # Check if report is already resolved
        if report['status'] == 'resolved':
            return {
                'success': False,
                'message': 'Report is already resolved',
                'status_code': 400
            }
        
        # Resolve report
        self.admin_repository.resolve_report(report_id, resolution)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def get_featured_cars(self, page=1, limit=10):
        """Get featured car listings for admin"""
        # Get featured cars with pagination
        cars, total = self.car_repository.get_cars(
            page=page,
            limit=limit,
            filters={'is_featured': True}
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'cars': cars,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            },
            'status_code': 200
        }
    
    def feature_car(self, car_id):
        """Feature a car listing"""
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found',
                'status_code': 404
            }
        
        # Check if car is already featured
        if car['is_featured']:
            return {
                'success': False,
                'message': 'Car listing is already featured',
                'status_code': 400
            }
        
        # Feature car
        query = """
            UPDATE cars
            SET is_featured = 1, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), car_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def unfeature_car(self, car_id):
        """Unfeature a car listing"""
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found',
                'status_code': 404
            }
        
        # Check if car is not featured
        if not car['is_featured']:
            return {
                'success': False,
                'message': 'Car listing is not featured',
                'status_code': 400
            }
        
        # Unfeature car
        query = """
            UPDATE cars
            SET is_featured = 0, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), car_id), fetch=False)
        
        return {
            'success': True,
            'status_code': 200
        }
    
    def get_subjects(self):
        """Get all subjects and contact information"""
        try:
            subjects = self.admin_repository.get_subjects()
            contact_info = self.admin_repository.get_contact_info()
            
            return {
                'success': True,
                'subjects': subjects,
                'contact_info': contact_info,
                'status_code': 200
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'status_code': 500
            }
    
    def submit_contact_message(self, user_id, subject, message):
        """Submit a contact message"""
        try:
            self.admin_repository.save_contact_message(user_id, subject, message)
            return {
                'success': True,
                'message': 'Contact message submitted successfully',
                'status_code': 200
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'status_code': 500
            }

    def get_car_by_id(self, car_id):
        return self.car_repository.get_car_by_id(car_id)

    def get_cars_listed_this_week(self):
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=7)
        # Get all cars listed in the last 7 days
        cars = self.car_repository.get_cars_listed_since(since)
        # Count by seller type
        individuals = 0
        dealers = 0
        for car in cars:
            user = self.user_repository.get_user_by_id(car['user_id'])
            if user and user.get('user_type') == 'dealer':
                dealers += 1
            else:
                individuals += 1
        return {
            'total': len(cars),
            'individuals': individuals,
            'dealers': dealers
        }

    def get_cars_sold_this_week(self):
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=7)
        count = self.car_repository.get_cars_sold_since(since)
        return {"sold_this_week": count}

    def get_listings_pending_approval(self):
        count = self.car_repository.get_pending_approval_count()
        return {"pending_approval": count}

    def get_user_incident_reports(self):
        count = self.admin_repository.get_user_incident_reports_count()
        return {"incident_reports": count}

    def get_user_incident_reports_list(self):
        reports = self.admin_repository.get_user_incident_reports_list()
        return {"reports": reports}

    def get_dealer_verification_tasks(self):
        # Assume user_repository has methods to get counts for new and resubmissions
        new = self.user_repository.get_pending_dealer_verifications(type='new')
        resubmissions = self.user_repository.get_pending_dealer_verifications(type='resubmission')
        return {
            "pending_verification": new + resubmissions,
            "new_applications": new,
            "resubmissions": resubmissions
        }

    def send_admin_otp(self, email):
        admin = self.admin_repository.get_admin_by_email(email)
        if not admin:
            return {"success": False, "message": "Email does not exist"}
        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now() + timedelta(minutes=10)
        self.admin_repository.save_admin_otp(email, otp, expires_at)
        # TODO: Implement actual email sending here
        print(f"Send OTP {otp} to {email}")
        return {"success": True, "message": "A verification code has been sent to your email"}

    def verify_admin_otp(self, email, otp):
        record = self.admin_repository.get_admin_otp(email, otp)
        if not record or record['expires_at'] < datetime.now() or record['verified']:
            return {"success": False, "message": "Invalid or expired verification code"}
        self.admin_repository.mark_admin_otp_verified(record['id'])
        return {"success": True, "message": "OTP verified. You may now reset your password."}

    def reset_admin_password(self, email, otp, new_password):
        record = self.admin_repository.get_admin_otp(email, otp)
        if not record or record['expires_at'] < datetime.now() or not record['verified']:
            return {"success": False, "message": "Invalid or expired verification code"}
        self.admin_repository.update_admin_password_by_email(email, new_password)
        return {"success": True, "message": "Your password has been updated successfully."}

    def get_car_rejection_reasons(self):
        reasons = self.admin_repository.get_car_rejection_reasons()
        return {"rejection_reasons": reasons}

    def mark_car_as_best_pick(self, car_id):
        self.car_repository.mark_as_best_pick(car_id)
        return True

    def unmark_car_as_best_pick(self, car_id):
        self.car_repository.unmark_as_best_pick(car_id)
        return True
