import uuid
from datetime import datetime, timedelta
from repositories.auth_repository import AuthRepository
from repositories.user_repository import UserRepository
from utils.auth import generate_token
from utils.sms import send_otp

class AuthService:
    def __init__(self):
        self.auth_repository = AuthRepository()
        self.user_repository = UserRepository()
    
    def register_user(self, first_name, last_name, email, date_of_birth, 
                     is_dealer, company_name, owner_name, company_address,
                     company_phone_number, company_registration_number,
                     facebook_page, instagram_company_profile, profile_pic, phone_number, user_type=None):
        """Register a new user"""
        # Check if phone number already exists
        existing_user = self.user_repository.get_user_by_phone(phone_number)
        if existing_user:
            return {
                'success': False,
                'message': 'Phone number already registered'
            }
        
        # Ensure is_dealer is boolean
        is_dealer = bool(is_dealer)
        
        # Set user_type default if not provided
        if not user_type:
            user_type = 'dealer' if is_dealer else 'individual'
        
        # Create user
        user_id = self.user_repository.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_of_birth=date_of_birth,
            user_type=user_type,
            is_dealer=is_dealer,
            company_name=company_name,
            owner_name=owner_name,
            company_address=company_address,
            company_phone_number=company_phone_number,
            company_registration_number=company_registration_number,
            facebook_page=facebook_page,
            instagram_company_profile=instagram_company_profile,
            profile_pic=profile_pic,
            phone_number=phone_number
        )
        
        # Get user
        user = self.user_repository.get_user_by_id(user_id)
        
        # Convert is_dealer to boolean in the user object
        if user and 'is_dealer' in user:
            user['is_dealer'] = bool(user['is_dealer'])
        
        # Generate token
        token = generate_token(user_id)
        
        return {
            'success': True,
            'user': user,
            'token': token
        }
    
    def initiate_login(self, phone_number, otp):
        """Initiate login process with phone number and OTP"""
        # Check if user exists and is soft deleted
        user = self.user_repository.get_user_by_phone(phone_number)
        if user and user.get('deleted_at'):
            return {
                'success': False,
                'message': 'User does not exist. Please sign up.'
            }
        # Create OTP request
        request_id = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(minutes=5)
        # Save OTP request
        self.auth_repository.save_otp_request(request_id, phone_number, otp, expiry)
        # Send OTP via SMS
        send_otp(phone_number, otp)
        return {
            'success': True,
            'request_id': request_id
        }
    
    def verify_login_otp(self, request_id, otp):
        """Verify OTP for login"""
        # Get OTP request
        otp_request = self.auth_repository.get_otp_request(request_id)
        
        if not otp_request:
            return {
                'success': False,
                'message': 'Invalid request ID'
            }
        
        # Check if OTP is expired
        if datetime.now() > otp_request['expiry']:
            return {
                'success': False,
                'message': 'OTP has expired'
            }
        
        # Check if OTP matches
        if otp != otp_request['otp']:
            return {
                'success': False,
                'message': 'Invalid OTP'
            }
        
        # Get user by phone number
        user = self.user_repository.get_user_by_phone(otp_request['phone_number'])
        
        if not user:
            return {
                'success': True,
                'message': 'User is not registered. Please complete registration first.',
                'is_registered': False,
                'phone_number': otp_request['phone_number']
            }
        
        # Check if user is banned
        if user.get('is_banned'):
            return {
                'success': False,
                'message': 'Your account has been banned'
            }
        
        # Generate token
        token = generate_token(user['id'])
        
        # Delete OTP request
        self.auth_repository.delete_otp_request(request_id)
        
        return {
            'success': True,
            'token': token,
            'user': user,
            'is_registered': True
        }
    
    def verify_otp(self, request_id, otp, first_name, last_name, password):
        """Verify OTP and complete registration"""
        # Get OTP request
        otp_request = self.auth_repository.get_otp_request(request_id)
        
        if not otp_request:
            return {
                'success': False,
                'message': 'Invalid request ID'
            }
        
        # Check if OTP is expired
        if datetime.now() > otp_request['expiry']:
            return {
                'success': False,
                'message': 'OTP has expired'
            }
        
        # Check if OTP matches
        if otp != otp_request['otp']:
            return {
                'success': False,
                'message': 'Invalid OTP'
            }
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = self.user_repository.create_user(
            phone_number=otp_request['phone_number'],
            first_name=first_name,
            last_name=last_name,
            password=hashed_password
        )
        
        # Delete OTP request
        self.auth_repository.delete_otp_request(request_id)
        
        # Get user
        user = self.user_repository.get_user_by_id(user_id)
        
        # Generate token
        token = generate_token(user_id)
        
        return {
            'success': True,
            'token': token,
            'user': user
        }
    
    def login(self, phone_number, password):
        """Login a user"""
        # Get user by phone number
        user = self.user_repository.get_user_by_phone(phone_number)
        
        if not user:
            return {
                'success': False,
                'message': 'Invalid phone number or password'
            }
        
        # Block deleted users
        if user.get('deleted_at'):
            return {
                'success': False,
                'message': 'Account deleted. Please sign up again.'
            }
        
        # Check if user is banned
        if user.get('is_banned'):
            return {
                'success': False,
                'message': 'Your account has been banned'
            }
        
        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {
                'success': False,
                'message': 'Invalid phone number or password'
            }
        
        # Generate token
        token = generate_token(user['id'])
        
        # Remove password from user object
        user.pop('password', None)
        
        return {
            'success': True,
            'token': token,
            'user': user
        }
    
    def forgot_password(self, phone_number, otp):
        """Send OTP for password reset"""
        # Check if phone number exists
        user = self.user_repository.get_user_by_phone(phone_number)
        if not user:
            return {
                'success': False,
                'message': 'Phone number not registered'
            }
        
        # Create OTP request
        request_id = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(minutes=5)
        
        # Save OTP request
        self.auth_repository.save_otp_request(request_id, phone_number, otp, expiry)
        
        # Send OTP via SMS
        send_otp(phone_number, otp)
        
        return {
            'success': True,
            'request_id': request_id
        }
    
    def reset_password(self, request_id, otp, new_password):
        """Reset password with OTP verification"""
        # Get OTP request
        otp_request = self.auth_repository.get_otp_request(request_id)
        
        if not otp_request:
            return {
                'success': False,
                'message': 'Invalid request ID'
            }
        
        # Check if OTP is expired
        if datetime.now() > otp_request['expiry']:
            return {
                'success': False,
                'message': 'OTP has expired'
            }
        
        # Check if OTP matches
        if otp != otp_request['otp']:
            return {
                'success': False,
                'message': 'Invalid OTP'
            }
        
        # Get user by phone number
        user = self.user_repository.get_user_by_phone(otp_request['phone_number'])
        
        if not user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user password
        self.user_repository.update_password(user['id'], hashed_password)
        
        # Delete OTP request
        self.auth_repository.delete_otp_request(request_id)
        
        return {
            'success': True
        }
    
    def change_password(self, user_id, current_password, new_password):
        """Change password for authenticated user"""
        # Get user
        user = self.user_repository.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Check current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
            return {
                'success': False,
                'message': 'Current password is incorrect'
            }
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user password
        self.user_repository.update_password(user_id, hashed_password)
        
        return {
            'success': True
        }
