from flask import Blueprint, request, jsonify, g
import random
import string
from services.auth_service import AuthService
from utils.auth import token_required

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'phone_number']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Register user
    result = auth_service.register_user(
        phone_number=data['phone_number'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        date_of_birth=data['date_of_birth'],
        is_dealer=data.get('is_dealer', False),
        company_name=data.get('company_name'),
        owner_name=data.get('owner_name'),
        company_address=data.get('company_address'),
        company_phone_number=data.get('company_phone_number'),
        company_registration_number=data.get('company_registration_number'),
        facebook_page=data.get('facebook_page'),
        instagram_company_profile=data.get('instagram_company_profile'),
        profile_pic=data.get('profile_pic')
    )
    
    if result['success']:
        # Convert is_dealer to boolean in the user object
        if 'user' in result and 'is_dealer' in result['user']:
            result['user']['is_dealer'] = bool(result['user']['is_dealer'])
        
        return jsonify({
            "message": "Registration successful",
            "token": result['token'],
            "user": result['user']
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP for login"""
    data = request.json
    
    # Validate required fields
    required_fields = ['request_id', 'otp']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Verify OTP for login
    result = auth_service.verify_login_otp(
        data['request_id'],
        data['otp']
    )
    
    if result['success']:
        if not result.get('is_registered', True):
            return jsonify({
                "message": "User is not registered. Please complete registration first.",
                "is_registered": False,
                "phone_number": result['phone_number']
            }), 200
        return jsonify({
            "message": "Verification successful",
            "token": result['token'],
            "user": result['user'],
            "is_registered": True
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user with phone number and send OTP"""
    data = request.json
    
    # Validate required fields
    if 'phone_number' not in data:
        return jsonify({"error": "Missing required field: phone_number"}), 400
    
    # Generate OTP (4 digits)
    otp = ''.join(random.choices(string.digits, k=4))
    
    # Send OTP for login
    result = auth_service.initiate_login(data['phone_number'], otp)
    
    if result['success']:
        return jsonify({
            "message": "OTP sent successfully",
            "request_id": result['request_id'],
            "otp": otp  # Only for development, remove in production
        }), 200
    else:
        return jsonify({"error": result['message']}), 400
