from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity, get_jwt
import logging
import os

logger = logging.getLogger(__name__)

def admin_token_required(f):
    """Decorator to protect admin routes with JWT authentication for all admin roles"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            g.admin_id = get_jwt_identity()
            # Optionally, you can check admin role here if needed
        except Exception as e:
            logger.error(f"Admin token verification failed: {str(e)}")
            return jsonify({'message': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

# Ensure JWT tokens are at least 128 characters long by adding entropy to the payload
def generate_token(user_id):
    """Generate a JWT token for the user with extra entropy to ensure length >= 128 chars"""
    try:
        # Add extra entropy to the payload
        extra_entropy = os.urandom(48).hex()  # 96 hex chars
        token = create_access_token(identity=str(user_id), additional_claims={"entropy": extra_entropy})
        logger.debug(f"Token generated for user {user_id}")
        if len(token) < 128:
            logger.warning(f"JWT token length is less than 128 characters: {len(token)}")
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
