from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository

class PaymentService:
    def __init__(self):
        self.payment_repository = PaymentRepository()
        self.subscription_repository = SubscriptionRepository()
    
    def get_payment_methods(self):
        """Get all available payment methods"""
        methods = self.payment_repository.get_payment_methods()
        return methods
    
    def create_checkout(self, user_id, amount, currency, description, payment_method_id, metadata=None):
        """Create a checkout session for payment"""
        # Check if payment method exists
        payment_method = self.payment_repository.get_payment_method(payment_method_id)
        
        if not payment_method:
            return {
                'success': False,
                'message': 'Payment method not found'
            }
        
        # Create checkout session
        result = self.payment_repository.create_checkout(
            user_id=user_id,
            amount=amount,
            currency=currency,
            description=description,
            payment_method=payment_method['code'],
            metadata=metadata or {}
        )
        
        return result
    
    def process_webhook(self, data):
        """Process payment webhook from payment gateway"""
        # Extract payment information from webhook data
        payment_id = data.get('payment_id')
        status = data.get('status')
        metadata = data.get('metadata', {})
        
        if not payment_id or not status:
            return {
                'success': False,
                'message': 'Invalid webhook data'
            }
        
        # Update payment status
        self.payment_repository.update_payment_status(payment_id, status)
        
        # If payment is successful, process the purchase
        if status == 'completed':
            # Check if payment is for a subscription
            if metadata.get('type') == 'subscription':
                package_id = metadata.get('package_id')
                user_id = data.get('user_id')
                
                if package_id and user_id:
                    # Create subscription
                    self.subscription_repository.create_subscription(
                        user_id=user_id,
                        package_id=package_id
                    )
        
        return {
            'success': True
        }
    
    def get_user_transactions(self, user_id, page=1, limit=10):
        """Get payment transactions for a user"""
        # Get transactions with pagination
        transactions, total = self.payment_repository.get_user_transactions(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'transactions': transactions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }
    
    def get_invoice(self, invoice_id, user_id):
        """Get a specific invoice"""
        invoice = self.payment_repository.get_invoice(invoice_id)
        
        if not invoice:
            return None
        
        # Check if invoice belongs to the user
        if invoice['user_id'] != user_id:
            return None
        
        return invoice
