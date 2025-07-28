from utils.db import execute_query
from datetime import datetime
import uuid
import requests
from config import PAYMENT_GATEWAY_API_KEY, PAYMENT_GATEWAY_SECRET
import json

class PaymentRepository:
    def get_payment_methods(self):
        """Get all available payment methods"""
        query = """
            SELECT id, name, code, description, is_active
            FROM payment_methods
            WHERE is_active = 1
            ORDER BY name
        """
        return execute_query(query)
    
    def get_payment_method(self, payment_method_id):
        """Get a payment method by ID"""
        query = """
            SELECT id, name, code, description, is_active
            FROM payment_methods
            WHERE id = %s
        """
        results = execute_query(query, (payment_method_id,))
        return results[0] if results else None
    
    def create_checkout(self, user_id, amount, currency, description, payment_method, metadata=None):
        """Create a checkout session for payment"""
        # Generate a unique checkout ID
        checkout_id = str(uuid.uuid4())
        
        # Create payment record
        query = """
            INSERT INTO payments (checkout_id, user_id, amount, currency, description, payment_method, status, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Convert metadata to JSON
        metadata_json = json.dumps(metadata) if metadata else None
        
        payment_id = execute_query(
            query,
            (checkout_id, user_id, amount, currency, description, payment_method, 'pending', metadata_json, datetime.now()),
            fetch=False
        )
        
        # Create checkout session with payment gateway
        # This is a placeholder. Replace with actual payment gateway API call
        try:
            # Simulate payment gateway API call
            # In a real implementation, this would be a call to the payment gateway API
            # response = requests.post(
            #     "https://api.paymentgateway.com/checkout",
            #     json={
            #         "api_key": PAYMENT_GATEWAY_API_KEY,
            #         "amount": amount,
            #         "currency": currency,
            #         "description": description,
            #         "payment_method": payment_method,
            #         "metadata": metadata,
            #         "checkout_id": checkout_id
            #     }
            # )
            # redirect_url = response.json().get("redirect_url")
            
            # Simulate a successful response
            redirect_url = f"https://paymentgateway.com/checkout/{checkout_id}"
            
            return {
                'success': True,
                'checkout_id': checkout_id,
                'redirect_url': redirect_url
            }
        except Exception as e:
            # Log error
            print(f"Payment gateway error: {str(e)}")
            
            # Update payment status to failed
            self.update_payment_status(payment_id, 'failed')
            
            return {
                'success': False,
                'message': 'Failed to create payment checkout'
            }
    
    def update_payment_status(self, payment_id, status):
        """Update a payment's status"""
        query = """
            UPDATE payments
            SET status = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (status, datetime.now(), payment_id), fetch=False)
    
    def get_user_transactions(self, user_id, page=1, limit=10):
        """Get payment transactions for a user"""
        offset = (page - 1) * limit
        
        # Get transactions with pagination
        query = """
            SELECT id, checkout_id, user_id, amount, currency, description, payment_method, status, created_at, updated_at
            FROM payments
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        transactions = execute_query(query, (user_id, limit, offset))
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM payments
            WHERE user_id = %s
        """
        count_result = execute_query(count_query, (user_id,))
        total = count_result[0]['total'] if count_result else 0
        
        return transactions, total
    
    def get_invoice(self, invoice_id):
        """Get a specific invoice"""
        query = """
            SELECT p.id, p.checkout_id, p.user_id, p.amount, p.currency, p.description, p.payment_method,
                   p.status, p.created_at, p.updated_at,
                   u.first_name, u.last_name, u.phone_number
            FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
        """
        results = execute_query(query, (invoice_id,))
        return results[0] if results else None
