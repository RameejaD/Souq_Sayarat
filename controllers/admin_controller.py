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

# Remove admin_session_required and super_admin_required
# Use token_required for all admin endpoints

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
        admin = result['admin']
        response = {
            "access_token": result['session_token'],
            "needs_password_update": admin['needs_password_update'],
            "is_super_admin": admin['is_super_admin'],
            "is_subscription_transaction_manager": admin['is_subscription_transaction_manager'],
            "is_listing_manager": admin['is_listing_manager'],
            "is_user_manager": admin['is_user_manager'],
            "is_support_manager": admin['is_support_manager'],
            "message": result.get('message', 'Login successful')
        }
        return jsonify(response), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

# New endpoint: update password for sub admin when needs_password_update=1
@admin_bp.route('/update-password-initial', methods=['PUT'])
@token_required
def update_admin_password_initial():
    # Patch: set g.admin if not set
    if not hasattr(g, 'admin') or g.admin is None:
        admin = admin_service.admin_repository.get_admin_by_id(g.user_id)
        if not admin:
            return jsonify({"error": "Admin not found in context"}), 403
        g.admin = admin
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
@token_required
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
@token_required
def get_admin_profile():
    # Patch: set g.admin if not set
    if not hasattr(g, 'admin') or g.admin is None:
        admin = admin_service.admin_repository.get_admin_by_id(g.user_id)
        if not admin:
            return jsonify({"error": "Admin not found"}), 404
        g.admin = admin
    return jsonify({
        "admin": g.admin
    }), 200

@admin_bp.route('/update-password', methods=['PUT'])
@token_required
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
@token_required
def create_admin():
    # Patch: set g.admin if not set
    if not hasattr(g, 'admin') or g.admin is None:
        admin = admin_service.admin_repository.get_admin_by_id(g.user_id)
        if not admin:
            return jsonify({"error": "Admin not found in context"}), 403
        g.admin = admin
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
@token_required
def get_all_admins():
    """Get all admins (super admin only)"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    result = admin_service.get_all_admins(page, limit)
    return jsonify(result), result['status_code']

@admin_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@token_required
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
@token_required
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
@token_required
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
@token_required
def get_dashboard():
    """Get admin dashboard data"""
    dashboard = admin_service.get_dashboard()
    return jsonify(dashboard), dashboard['status_code']

@admin_bp.route('/cars/pending', methods=['GET'])
@token_required
def get_pending_cars():
    """Get pending car listings for approval"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get pending cars
    result = admin_service.get_pending_cars(page, limit)
    return jsonify(result), result['status_code']

@admin_bp.route('/cars/<int:car_id>/approve', methods=['PUT'])
@token_required
def approve_car(car_id):
    """Approve a car listing"""
    result = admin_service.approve_car(car_id)
    
    if result['success']:
        return jsonify({
            "message": "Car listing approved successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/cars/<int:car_id>/reject', methods=['PUT'])
@token_required
def reject_car(car_id):
    """Reject a car listing"""
    data = request.json
    
    # Validate required fields
    if 'reason' not in data:
        return jsonify({"error": "Missing required field: reason"}), 400
    
    # Reject car listing
    result = admin_service.reject_car(car_id, data['reason'])
    
    if result['success']:
        return jsonify({
            "message": "Car listing rejected successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/users', methods=['GET'])
@token_required
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

@admin_bp.route('/search-users', methods=['POST'])
@token_required
def search_users():
    """Search users by name, email, or phone number (pagination via query params)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        search_query = data.get('search_query', '').strip()
        if not search_query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        # Get pagination from query params
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        if limit < 1 or limit > 50:
            limit = 10
        if page < 1:
            page = 1
        # Search users
        users, total = admin_service.search_users(search_query, page, limit)
        # Only return required fields
        filtered_users = [
            {
                'id': u['id'],
                'name': f"{u['first_name']} {u['last_name']}",
                'email': u['email'],
                'phone_number': u['phone_number'],
                'user_type': u['user_type'],
                'is_verified': u['is_verified']
            }
            for u in users
        ]
        return jsonify({
            'success': True,
            'message': 'Users found successfully',
            'data': {
                'users': filtered_users,
                'total': total,
                'page': page,
                'limit': limit,
                'search_query': search_query
            }
        }), 200
    except Exception as e:
        print(f"Error in search_users: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching users'
        }), 500

@admin_bp.route('/users/<int:user_id>/verify', methods=['PUT'])
@token_required
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
@token_required
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
@token_required
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
@token_required
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
@token_required
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

@admin_bp.route('/cars/<int:car_id>/feature', methods=['PUT'])
@token_required
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
@token_required
def unfeature_car(car_id):
    """Unfeature a car listing"""
    result = admin_service.unfeature_car(car_id)
    
    if result['success']:
        return jsonify({
            "message": "Car listing unfeatured successfully"
        }), result['status_code']
    else:
        return jsonify({"error": result['message']}), result['status_code']

@admin_bp.route('/contact/subjects', methods=['GET'])
@token_required
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

@admin_bp.route('/reported-users', methods=['GET'])
@token_required
def get_reported_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    result = admin_service.get_reported_users(page, limit)
    return jsonify(result), 200

@admin_bp.route('/reported-users/<int:report_id>/flag', methods=['PUT'])
@token_required
def flag_reported_user(report_id):
    success = admin_service.flag_reported_user(report_id)
    if success:
        return jsonify({'success': True, 'message': 'User flagged successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'Failed to flag user. Invalid report_id or database error.'}), 400

@admin_bp.route('/reported-users/<int:report_id>/ban', methods=['PUT'])
@token_required
def ban_reported_user(report_id):
    data = request.get_json()
    ban_reason = data.get('ban_reason')
    if not ban_reason:
        return jsonify({'success': False, 'message': 'ban_reason is required'}), 400
    admin_service.ban_reported_user(report_id, ban_reason)
    return jsonify({'success': True, 'message': 'User banned successfully'}), 200

@admin_bp.route('/watchlist', methods=['GET'])
@token_required
def get_watchlist():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    result = admin_service.get_watchlist(page, limit)
    return jsonify(result), 200
