from flask import Blueprint, request, jsonify, g
from services.subscription_service import SubscriptionService
from utils.auth import token_required
from services.user_service import UserService

subscription_bp = Blueprint('subscription', __name__)
subscription_service = SubscriptionService()
user_service = UserService()

@subscription_bp.route('/packages', methods=['GET'])
def get_subscription_packages():
    """Get subscription packages separated by user type"""
    result = user_service.get_subscription_packages()
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({"error": result['message']}), 400

@subscription_bp.route('/my-subscription', methods=['GET'])
@token_required
def get_my_subscription():
    """Get the subscription for the authenticated user"""
    subscription = subscription_service.get_user_subscription(g.user_id)
    return jsonify(subscription), 200

@subscription_bp.route('/subscribe', methods=['POST'])
@token_required
def subscribe():
    """Subscribe to a package"""
    data = request.json
    
    # Validate required fields
    if 'package_id' not in data:
        return jsonify({"error": "Missing required field: package_id"}), 400
    
    # Subscribe to package
    result = subscription_service.subscribe(
        user_id=g.user_id,
        package_id=data['package_id']
    )
    
    if result['success']:
        return jsonify({
            "message": "Subscription successful",
            "subscription": result['subscription'],
            "payment_url": result.get('payment_url')
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@subscription_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_subscription():
    """Cancel the current subscription"""
    result = subscription_service.cancel_subscription(g.user_id)
    
    if result['success']:
        return jsonify({
            "message": "Subscription cancelled successfully"
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@subscription_bp.route('/history', methods=['GET'])
@token_required
def get_subscription_history():
    """Get subscription history for the authenticated user"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get subscription history
    result = subscription_service.get_subscription_history(
        user_id=g.user_id,
        page=page,
        limit=limit
    )
    
    return jsonify(result), 200
