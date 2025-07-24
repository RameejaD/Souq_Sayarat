from functools import wraps
from flask import g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get user_id from token
            g.user_id = get_jwt_identity()
            
            # Debug logging
            logger.debug(f"Token verified successfully. User ID: {g.user_id}")
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Invalid or expired token'}), 401
            
    return decorated 