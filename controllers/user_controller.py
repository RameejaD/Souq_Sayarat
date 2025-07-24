from flask import Blueprint, current_app, request, jsonify, g, url_for
from services.user_service import UserService
from utils.auth import token_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.file_upload import save_file
import os
from werkzeug.utils import secure_filename


user_bp = Blueprint('user', __name__)
user_service = UserService()

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get the profile of the authenticated user"""
    user = user_service.get_user_by_id(g.user_id)
    
    if user:
        # return jsonify(), 200
        return jsonify({
            "message": "Profile updated successfully",
            "data": user
        }), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route('/edit-profile', methods=['PUT'])
@token_required
def edit_profile():
    """Edit user profile"""
    try:
        # Use form data instead of JSON
        data = request.form

        # Handle profile image if provided
        profile_image = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_image = file_path

        # Convert is_dealer to boolean correctly
        is_dealer = None
        if 'is_dealer' in data:
            # Handle both string and integer inputs
            is_dealer_value = data.get('is_dealer')
            if isinstance(is_dealer_value, str):
                is_dealer = is_dealer_value.lower() in ['true', '1', 'yes']
            else:
                is_dealer = bool(is_dealer_value)

        # Update user profile with all possible parameters
        result = user_service.update_user(
            user_id=g.user_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            date_of_birth=data.get('date_of_birth'),
            is_dealer=is_dealer,
            company_name=data.get('company_name'),
            owner_name=data.get('owner_name'),
            company_address=data.get('company_address'),
            company_phone_number=data.get('company_phone_number'),
            company_registration_number=data.get('company_registration_number'),
            facebook_page=data.get('facebook_page'),
            instagram_company_profile=data.get('instagram_company_profile'),
            profile_pic=profile_image or data.get('profile_pic'),
            phone_number=data.get('phone_number'),
            whatsapp=data.get('whatsapp'),
            location=data.get('location')
        )

        if not result['success']:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        print(str(e))
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@user_bp.route('/favorites', methods=['GET'])
@token_required
def get_favorites():
    """Get favorite car listings for the authenticated user"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get favorite cars
    result = user_service.get_favorites(
        user_id=g.user_id,
        page=page,
        limit=limit
    )
    
    return jsonify(result), 200

@user_bp.route('/favorites/<int:car_id>', methods=['POST'])
@token_required
def add_favorite(car_id):
    """Add a car to favorites"""
    result = user_service.add_favorite(g.user_id, car_id)
    
    if result['success']:
        return jsonify({
            "message": result['message']
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/favorites/<int:car_id>', methods=['DELETE'])
@token_required
def remove_favorite(car_id):
    """Remove a car from favorites"""
    result = user_service.remove_favorite(g.user_id, car_id)
    
    if result['success']:
        return jsonify({
            "message": result['message']
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/saved-searches', methods=['GET'])
@token_required
def get_saved_searches():
    """Get saved searches for the authenticated user"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get saved searches
    result = user_service.get_saved_searches(
        user_id=g.user_id,
        page=page,
        limit=limit
    )
    
    return jsonify(result), 200

@user_bp.route('/saved-searches', methods=['POST'])
@token_required
def save_search():
    """Save a search"""
    try:
        data = request.get_json()
        search_params = data.get('search_params', {})
        name = data.get('name')
        notification = 1 if data.get('notification', 0) in [1, '1', True, 'true'] else 0
        
        result = user_service.save_search(
            user_id=g.user_id,
            search_params=search_params,
            name=name,
            notification=notification
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/saved-searches/<int:search_id>', methods=['DELETE'])
@token_required
def delete_saved_search(search_id):
    """Delete a saved search"""
    result = user_service.delete_saved_search(g.user_id, search_id)
    
    if result['success']:
        return jsonify({
            "message": "Saved search deleted successfully"
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/saved-searches/<int:search_id>', methods=['PUT'])
@token_required
def update_saved_search_notification(search_id):
    """Toggle notification status for a saved search"""
    try:
        # Get current search to check if it exists and get current notification status
        search = user_service.user_repository.get_saved_search(search_id)
        
        if not search:
            return jsonify({"error": "Saved search not found"}), 404
            
        # Toggle the notification status (0 to 1 or 1 to 0)
        current_status = search.get('notification', 0)
        new_status = 0 if current_status == 1 else 1
        
        result = user_service.update_saved_search_notification(
            user_id=g.user_id,
            search_id=search_id,
            notification=new_status
        )
        
        if result['success']:
            return jsonify({
                "message": result['message'],
                "notification": new_status
            }), 200
        else:
            return jsonify({"error": result['message']}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user's public profile"""
    user = user_service.get_public_profile(user_id)
    
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

@user_bp.route('/details', methods=['GET'])
@token_required
def get_user_details():
    """Get detailed user information with copy option"""
    try:
        user = user_service.get_user_by_id(g.user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Format the response with copy-friendly fields
        response = {
            'success': True,
            'data': {
                'personal_info': {
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'email': user.get('email'),
                    'phone_number': user.get('phone_number'),
                    'whatsapp': user.get('whatsapp'),
                    'location': user.get('location'),
                    'date_of_birth': user.get('date_of_birth'),
                    'is_dealer': bool(user.get('is_dealer', 0))
                }
            }
        }

        # Add dealer information if user is a dealer
        if user.get('is_dealer'):
            response['data']['dealer_info'] = {
                'company_name': user.get('company_name'),
                'owner_name': user.get('owner_name'),
                'company_address': user.get('company_address'),
                'company_phone_number': user.get('company_phone_number'),
                'company_registration_number': user.get('company_registration_number'),
                'facebook_page': user.get('facebook_page'),
                'instagram_company_profile': user.get('instagram_company_profile')
            }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_user():
    """Update user profile"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        print(f"Updating user ID: {user_id}")  # Debug log
        
        # Get form data
        data = request.form.to_dict()
        print(f"Form data received: {data}")  # Debug log
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            print(f"Profile pic file received: {profile_pic.filename}")  # Debug log
            
            if profile_pic and profile_pic.filename:
                # Save the profile picture
                profile_pic_url = save_file(profile_pic, 'profile_pics')
                print(f"Profile pic URL after save: {profile_pic_url}")  # Debug log
                
                if profile_pic_url:
                    # Store only the relative path in the database
                    relative_path = profile_pic_url.split('/static/')[-1]
                    data['profile_pic'] = f"/static/{relative_path}"
                    print(f"Updated data with profile pic URL: {data}")  # Debug log
        else:
            print("No profile pic file in request")  # Debug log
        
        # Convert is_dealer to boolean correctly
        if 'is_dealer' in data:
            is_dealer_value = data.get('is_dealer')
            if isinstance(is_dealer_value, str):
                data['is_dealer'] = is_dealer_value.lower() in ['true', '1', 'yes']
            else:
                data['is_dealer'] = bool(is_dealer_value)
        
        # Update user with keyword arguments
        print(f"Calling service with data: {data}")  # Debug log
        result = user_service.update_user(user_id, **data)
        print(f"Service result: {result}")  # Debug log
        
        if result['success']:
            # Convert the profile_pic path to a full URL in the response
            if 'data' in result and 'profile_pic' in result['data']:
                try:
                    relative_path = result['data']['profile_pic'].split('/static/')[-1]
                    result['data']['profile_pic'] = url_for('static', filename=relative_path, _external=True)
                except Exception as e:
                    print(f"Error generating full URL for response: {str(e)}")
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in update_user: {str(e)}")  # Debug log
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/update-phone/initiate', methods=['POST'])
@jwt_required()
def initiate_phone_update():
    """Initiate phone number update process"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get new phone number
        new_phone_number = request.json.get('phone_number')
        if not new_phone_number:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
            
        # Initiate phone update
        result = user_service.initiate_phone_update(user_id, new_phone_number)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/update-phone/verify', methods=['POST'])
@jwt_required()
def verify_and_update_phone():
    """Verify OTP and update phone number"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get OTP and new phone number
        data = request.json
        otp = data.get('otp')
        new_phone_number = data.get('phone_number')
        
        if not otp or not new_phone_number:
            return jsonify({
                'success': False,
                'message': 'OTP and phone number are required'
            }), 400
            
        # Verify OTP and update phone number
        result = user_service.verify_and_update_phone(user_id, otp, new_phone_number)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/send-change-phone-otp', methods=['POST'])
@jwt_required()
def send_change_phone_otp():
    """Send OTP to new phone number"""
    data = request.json
    if 'phone_number' not in data:
        return jsonify({"success": False, "message": "Phone number is required"}), 400

    user_id = get_jwt_identity()
    response = user_service.send_phone_change_otp(user_id, data['phone_number'])
    return jsonify(response), 200

@user_bp.route('/verify-change-phone-otp', methods=['POST'])
@jwt_required()
def verify_change_phone_otp():
    """Verify OTP and update phone number"""
    data = request.json
    required_fields = ['request_id', 'otp']

    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing field: {field}"}), 400

    user_id = get_jwt_identity()
    response = user_service.verify_phone_change_otp(user_id, data['request_id'], data['otp'])

    if response['success']:
        return jsonify({
            "success": True,
            "message": "Your phone number has been changed",
            "new_phone_number": response['new_phone_number']
        }), 200
    else:
        return jsonify({"success": False, "message": response['message']}), 400

@user_bp.route('/block/<int:user_id>', methods=['POST'])
@token_required
def block_user(user_id):
    """Block a user"""
    result = user_service.block_user(g.user_id, user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/unblock/<int:user_id>', methods=['POST'])
@token_required
def unblock_user(user_id):
    """Unblock a user"""
    result = user_service.unblock_user(g.user_id, user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/blocked-users', methods=['GET'])
@token_required
def get_blocked_users():
    """Get list of blocked users"""
    result = user_service.get_blocked_users(g.user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({"error": result['message']}), 400

@user_bp.route('/user-incident-reports-list', methods=['GET'])
@token_required
def user_incident_reports_list():
    result = user_service.get_user_incident_reports_list()
    return jsonify(result), 200

@user_bp.route('/car-rejection-reasons', methods=['GET'])
def get_car_rejection_reasons():
    result = user_service.get_car_rejection_reasons()
    return jsonify(result), 200
