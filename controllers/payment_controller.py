from flask import Blueprint, request, jsonify, g
from services.payment_service import PaymentService
from utils.auth import token_required

payment_bp = Blueprint('payment', __name__)
payment_service = PaymentService()

@payment_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """Get all available payment methods"""
    methods = payment_service.get_payment_methods()
    return jsonify(methods), 200

@payment_bp.route('/checkout', methods=['POST'])
@token_required
def create_checkout():
    """Create a checkout session for payment"""
    data = request.json
    
    # Validate required fields
    required_fields = ['amount', 'currency', 'description', 'payment_method_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Create checkout session
    result = payment_service.create_checkout(
        user_id=g.user_id,
        amount=data['amount'],
        currency=data['currency'],
        description=data['description'],
        payment_method_id=data['payment_method_id'],
        metadata=data.get('metadata', {})
    )
    
    if result['success']:
        return jsonify({
            "message": "Checkout session created successfully",
            "checkout_id": result['checkout_id'],
            "redirect_url": result['redirect_url']
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle payment webhook from payment gateway"""
    # Get the webhook data
    data = request.json
    
    # Process the webhook
    result = payment_service.process_webhook(data)
    
    if result['success']:
        return jsonify({
            "message": "Webhook processed successfully"
        }), 200
    else:
        return jsonify({"error": result['message']}), 400

@payment_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    """Get payment transactions for the authenticated user"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get transactions
    result = payment_service.get_user_transactions(
        user_id=g.user_id,
        page=page,
        limit=limit
    )
    
    return jsonify(result), 200

@payment_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
def get_invoice(invoice_id):
    """Get a specific invoice"""
    invoice = payment_service.get_invoice(invoice_id, g.user_id)
    
    if invoice:
        return jsonify(invoice), 200
    else:
        return jsonify({"error": "Invoice not found"}), 404
