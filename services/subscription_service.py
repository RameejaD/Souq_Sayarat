from repositories.subscription_repository import SubscriptionRepository
from repositories.payment_repository import PaymentRepository

class SubscriptionService:
    def __init__(self):
        self.subscription_repository = SubscriptionRepository()
        self.payment_repository = PaymentRepository()
    
    def get_packages(self):
        """Get all subscription packages"""
        packages = self.subscription_repository.get_packages()
        return packages
    
    def get_user_subscription(self, user_id):
        """Get the subscription for a user"""
        subscription = self.subscription_repository.get_active_subscription(user_id)
        
        if not subscription:
            # Return free tier info
            return {
                'is_subscribed': False,
                'package': {
                    'name': 'Free',
                    'description': 'Free tier with limited features',
                    'listing_limit': 1,
                    'duration_days': 0,
                    'price': 0
                },
                'listings_used': self.subscription_repository.get_user_listings_count(user_id),
                'listings_remaining': 1 - self.subscription_repository.get_user_listings_count(user_id)
            }
        
        # Get package details
        package = self.subscription_repository.get_package(subscription['package_id'])
        
        # Get listings count
        listings_used = self.subscription_repository.get_user_listings_count(user_id)
        listings_remaining = package['listing_limit'] - listings_used
        
        return {
            'is_subscribed': True,
            'subscription_id': subscription['id'],
            'package': package,
            'start_date': subscription['start_date'],
            'end_date': subscription['end_date'],
            'listings_used': listings_used,
            'listings_remaining': listings_remaining
        }
    
    def subscribe(self, user_id, package_id):
        """Subscribe to a package"""
        # Check if package exists
        package = self.subscription_repository.get_package(package_id)
        
        if not package:
            return {
                'success': False,
                'message': 'Subscription package not found'
            }
        
        # Check if user already has an active subscription
        active_subscription = self.subscription_repository.get_active_subscription(user_id)
        
        if active_subscription:
            return {
                'success': False,
                'message': 'You already have an active subscription. Please cancel it before subscribing to a new package.'
            }
        
        # If package is free, create subscription directly
        if package['price'] == 0:
            subscription_id = self.subscription_repository.create_subscription(
                user_id=user_id,
                package_id=package_id
            )
            
            subscription = self.subscription_repository.get_subscription(subscription_id)
            
            return {
                'success': True,
                'subscription': subscription
            }
        
        # For paid packages, create a payment checkout
        checkout_result = self.payment_repository.create_checkout(
            user_id=user_id,
            amount=package['price'],
            currency='USD',
            description=f"Subscription to {package['name']} package",
            metadata={
                'type': 'subscription',
                'package_id': package_id
            }
        )
        
        if not checkout_result['success']:
            return {
                'success': False,
                'message': 'Failed to create payment checkout'
            }
        
        return {
            'success': True,
            'payment_url': checkout_result['redirect_url']
        }
    
    def cancel_subscription(self, user_id):
        """Cancel the current subscription"""
        # Check if user has an active subscription
        subscription = self.subscription_repository.get_active_subscription(user_id)
        
        if not subscription:
            return {
                'success': False,
                'message': 'You do not have an active subscription'
            }
        
        # Cancel subscription
        self.subscription_repository.cancel_subscription(subscription['id'])
        
        return {
            'success': True
        }
    
    def get_subscription_history(self, user_id, page=1, limit=10):
        """Get subscription history for a user"""
        # Get subscription history with pagination
        subscriptions, total = self.subscription_repository.get_user_subscriptions(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'subscriptions': subscriptions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }
