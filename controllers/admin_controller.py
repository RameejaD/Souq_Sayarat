from flask import Blueprint, request, jsonify, g
from services.admin_service import AdminService
from utils.auth import token_required

admin_bp = Blueprint('admin', __name__)
admin_service = AdminService()

# Middleware to check if user is admin
def admin_required(f):
    @token_required
    def decorated(*args, **kwargs):
        # Check if user is admin
        if not admin_service.is_admin(g.user_id):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Middleware to check if user is admin (using session token)
def admin_session_required(f):
    def decorated(*args, **kwargs):
        session_token = request.headers.get('Authorization')
        if not session_token:
            return jsonify({"error": "Authorization header required"}), 401
        
        # Remove 'Bearer ' prefix if present
        if session_token.startswith('Bearer '):
            session_token = session_token[7:]
        
        admin = admin_service.get_admin_by_session(session_token)
        if not admin:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        # Add admin to request context
        g.admin = admin
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Middleware to check if admin is super admin
def super_admin_required(f):
    @admin_session_required
    def decorated(*args, **kwargs):
        if not g.admin['is_super_admin']:
            return jsonify({"error": "Super admin access required"}), 403
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Admin Authentication Endpoints
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login with email and password"""
    data = request.json
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Authenticate admin
    result = admin_service.authenticate_admin(
        email=data['email'],
        password=data['password'],
        request=request
    )
    
    if result['success']:
        response = {
            "access_token": result['session_token'],
            "needs_password_update": result['admin']['needs_password_update'],
            "message": result.get('message', 'Login successful')
        }
        return jsonify(response), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

# New endpoint: update password for sub admin when needs_password_update=1
@admin_bp.route('/update-password-initial', methods=['PUT'])
@admin_session_required
def update_admin_password_initial():
    """Update admin password for first login (when needs_password_update=1)"""
    data = request.json
    # Only require new_password
    if not data or 'new_password' not in data:
        return jsonify({"error": "New password is required"}), 400
    # Only allow if needs_password_update is 1
    if not g.admin or g.admin.get('needs_password_update', 0) != 1:
        return jsonify({"error": "Password update not allowed"}), 403
    result = admin_service.update_admin_password(
        admin_id=g.admin['id'],
        current_password=None,  # Not required for initial update
        new_password=data['new_password'],
        request=request,
        force_update=True
    )
    if result['success']:
        return jsonify({"message": result['message']}), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/logout', methods=['POST'])
@admin_session_required
def admin_logout():
    """Admin logout"""
    session_token = request.headers.get('Authorization')
    if session_token.startswith('Bearer '):
        session_token = session_token[7:]
    
    result = admin_service.logout_admin(session_token, request)
    
    if result['success']:
        return jsonify({"message": result['message']}), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/profile', methods=['GET'])
@admin_session_required
def get_admin_profile():
    """Get admin profile"""
    return jsonify({
        "admin": g.admin
    }), 200

@admin_bp.route('/update-password', methods=['PUT'])
@admin_session_required
def update_admin_password():
    """Update admin password"""
    data = request.json
    
    # Validate required fields
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Current password and new password are required"}), 400
    
    result = admin_service.update_admin_password(
        admin_id=g.admin['id'],
        current_password=data['current_password'],
        new_password=data['new_password'],
        request=request
    )
    
    if result['success']:
        return jsonify({"message": result['message']}), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

# Admin Management Endpoints (Super Admin Only)
@admin_bp.route('/admins', methods=['POST'])
@super_admin_required
def create_admin():
    """Create a new admin (super admin only)"""
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate permissions
    permissions = {
        'is_super_admin': data.get('is_super_admin', False),
        'is_subscription_transaction_manager': data.get('is_subscription_transaction_manager', False),
        'is_listing_manager': data.get('is_listing_manager', False),
        'is_user_manager': data.get('is_user_manager', False),
        'is_support_manager': data.get('is_support_manager', False)
    }
    
    # Create admin
    result = admin_service.create_admin(
        email=data['email'],
        password=data['password'],
        permissions=permissions,
        created_by_admin_id=g.admin['id'],
        request=request
    )
    
    if result['success']:
        return jsonify({
            "message": "Admin created successfully",
            "admin": result['admin']
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/admins', methods=['GET'])
@super_admin_required
def get_all_admins():
    """Get all admins (super admin only)"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    result = admin_service.get_all_admins(page, limit)
    return jsonify(result), result['status_code']

@admin_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@super_admin_required
def update_admin_permissions(admin_id):
    """Update admin permissions (super admin only)"""
    data = request.json
    
    # Validate permissions
    permissions = {
        'is_super_admin': data.get('is_super_admin', False),
        'is_subscription_transaction_manager': data.get('is_subscription_transaction_manager', False),
        'is_listing_manager': data.get('is_listing_manager', False),
        'is_user_manager': data.get('is_user_manager', False),
        'is_support_manager': data.get('is_support_manager', False)
    }
    
    result = admin_service.update_admin_permissions(
        admin_id=admin_id,
        permissions=permissions,
        updated_by_admin_id=g.admin['id'],
        request=request
    )
    
    if result['success']:
        return jsonify({"message": result['message']}), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@super_admin_required
def delete_admin(admin_id):
    """Delete an admin (super admin only)"""
    result = admin_service.delete_admin(
        admin_id=admin_id,
        deleted_by_admin_id=g.admin['id'],
        request=request
    )
    
    if result['success']:
        return jsonify({"message": result['message']}), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/activity-log', methods=['GET'])
@admin_session_required
def get_activity_log():
    """Get admin activity log"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    admin_id = request.args.get('admin_id', type=int)
    
    result = admin_service.get_admin_activity_log(
        admin_id=admin_id,
        page=page,
        limit=limit
    )
    return jsonify(result), result['status_code']

# Existing Admin Dashboard Endpoints (Updated to use session authentication)
@admin_bp.route('/dashboard', methods=['GET'])
@admin_session_required
def get_dashboard():
    """Get admin dashboard data"""
    dashboard = admin_service.get_dashboard()
    return jsonify(dashboard), dashboard['status_code']

@admin_bp.route('/dashboard-statistics', methods=['GET'])
@admin_session_required
def get_dashboard_statistics():
    """Get combined dashboard statistics"""
    result = admin_service.get_dashboard_statistics()
    return jsonify(result), result['status_code']

@admin_bp.route('/cars/pending', methods=['GET'])
@admin_session_required
def get_pending_cars():
    """Get pending car listings for approval"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get pending cars
    result = admin_service.get_pending_cars(page, limit)
    return jsonify(result), result['status_code']

@admin_bp.route('/cars/<int:car_id>/approve', methods=['PUT'])
@admin_session_required
def approve_car(car_id):
    """Approve a car listing"""
    result = admin_service.approve_car(car_id)
    
    if result['success']:
        return jsonify(result), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/cars/<int:car_id>/reject', methods=['PUT'])
@admin_session_required
def reject_car(car_id):
    """Reject a car listing"""
    data = request.json
    
    # Validate required fields
    if 'reason' not in data:
        return jsonify({"error": "Missing required field: reason"}), 400
    # Save admin rejection comment
    admin_rejection_comment = data.get('admin_rejection_comment', '')
    result = admin_service.reject_car(car_id, data['reason'], admin_rejection_comment)
    if result['success']:
        return jsonify(result), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/users', methods=['GET'])
@admin_session_required
def get_users():
    """Get all users with pagination and filtering"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search')
    user_type = request.args.get('user_type')
    
    # Get users
    result = admin_service.get_users(
        page=page,
        limit=limit,
        search=search,
        user_type=user_type
    )
    
    return jsonify(result), result['status_code']

@admin_bp.route('/users/<int:user_id>/verify', methods=['PUT'])
@admin_session_required
def verify_user(user_id):
    """Verify a user (for dealers)"""
    result = admin_service.verify_user(user_id)
    
    if result['success']:
        return jsonify({
            "message": "User verified successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/users/<int:user_id>/ban', methods=['PUT'])
@admin_session_required
def ban_user(user_id):
    """Ban a user"""
    data = request.json
    
    # Ban user
    result = admin_service.ban_user(
        user_id=user_id,
        reason=data.get('reason')
    )
    
    if result['success']:
        return jsonify({
            "message": "User banned successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/users/<int:user_id>/unban', methods=['PUT'])
@admin_session_required
def unban_user(user_id):
    """Unban a user"""
    result = admin_service.unban_user(user_id)
    
    if result['success']:
        return jsonify({
            "message": "User unbanned successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/reports', methods=['GET'])
@admin_session_required
def get_reports():
    """Get user reports with pagination"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    status = request.args.get('status')
    
    # Get reports
    result = admin_service.get_reports(
        page=page,
        limit=limit,
        status=status
    )
    
    return jsonify(result), result['status_code']

@admin_bp.route('/reports/<int:report_id>/resolve', methods=['PUT'])
@admin_session_required
def resolve_report(report_id):
    """Resolve a user report"""
    data = request.json
    
    # Resolve report
    result = admin_service.resolve_report(
        report_id=report_id,
        resolution=data.get('resolution')
    )
    
    if result['success']:
        return jsonify({
            "message": "Report resolved successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/cars/<int:car_id>/feature', methods=['PUT'])
@admin_session_required
def feature_car(car_id):
    """Feature a car listing"""
    result = admin_service.feature_car(car_id)
    
    if result['success']:
        return jsonify({
            "message": "Car listing featured successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/cars/<int:car_id>/unfeature', methods=['PUT'])
@admin_session_required
def unfeature_car(car_id):
    """Unfeature a car listing"""
    result = admin_service.unfeature_car(car_id)
    
    if result['success']:
        return jsonify({
            "message": "Car listing unfeatured successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/cars/<int:car_id>/mark-best-pick/<int:is_best_pick>', methods=['PUT'])
@admin_session_required
def mark_best_pick(car_id, is_best_pick):
    car = admin_service.get_car_by_id(car_id)
    if not car:
        return jsonify({"error": "Car not found."}), 404
    if car.get('approval') != 'approved':
        return jsonify({"error": "Only approved cars can be marked as Best Pick."}), 400
    if is_best_pick == 1:
        admin_service.mark_car_as_best_pick(car_id)
        return jsonify({"message": "Car marked as Best Pick."}), 200
    else:
        admin_service.unmark_car_as_best_pick(car_id)
        return jsonify({"message": "Car unmarked as Best Pick."}), 200



@admin_bp.route('/contact/subjects', methods=['GET'])
def get_subjects():
    """Get all subjects and contact information"""
    result = admin_service.get_subjects()
    
    if result['success']:
        return jsonify(result), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/contact/submit', methods=['POST'])
@token_required
def submit_contact():
    """Submit a contact message"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'subject' not in data or 'message' not in data:
            return jsonify({
                'success': False,
                'message': 'Subject and message are required'
            }), 400
            
        result = admin_service.submit_contact_message(
            user_id=g.user_id,
            subject=data['subject'],
            message=data['message']
        )
        
        if result['success']:
            return jsonify(result), result['status_code']
        else:
            return jsonify({"error": result['message']}), result['status_code']
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



@admin_bp.route('/user-incident-reports-list', methods=['GET'])
@admin_session_required
def user_incident_reports_list():
    result = admin_service.get_user_incident_reports_list()
    return jsonify(result), 200

@admin_bp.route('/dealer-verification-tasks', methods=['GET'])
@admin_session_required
def dealer_verification_tasks():
    result = admin_service.get_dealer_verification_tasks()
    return jsonify(result), 200

@admin_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Please enter your email address to receive a one-time verification code"}), 400
    result = admin_service.send_admin_otp(email)
    if result['success']:
        return jsonify({"message": result['message']}), 200
    else:
        return jsonify({"error": result['message']}), 400

@admin_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400
    result = admin_service.verify_admin_otp(email, otp)
    if result['success']:
        return jsonify({"message": result['message']}), 200
    else:
        return jsonify({"error": result['message']}), 400

@admin_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    
    # Check which fields are missing
    missing_fields = []
    if not email:
        missing_fields.append('email')
    if not new_password:
        missing_fields.append('new_password')
    
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    result = admin_service.reset_admin_password_without_otp(email, new_password)
    if result['success']:
        return jsonify({"message": result['message']}), 200
    else:
        return jsonify({"error": result['message']}), 400

@admin_bp.route('/car-rejection-reasons', methods=['GET'])
@admin_session_required
def get_car_rejection_reasons():
    result = admin_service.get_car_rejection_reasons()
    return jsonify(result), 200
@admin_bp.route('/featured-cars', methods=['GET'])
@token_required
def get_admin_featured_cars():
    """Get featured car listings for admin"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    # Get featured cars
    result = admin_service.get_featured_cars(page, limit)
    return jsonify(result), result['status_code']
