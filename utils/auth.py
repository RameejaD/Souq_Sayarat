from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def generate_token(user_id):
    """Generate a JWT token for the user"""
    try:
        token = create_access_token(identity=str(user_id))
        logger.debug(f"Token generated for user {user_id}")
        return token
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            g.user_id = get_jwt_identity()
            logger.debug(f"Token verified for user {g.user_id}")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return jsonify({'message': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated
