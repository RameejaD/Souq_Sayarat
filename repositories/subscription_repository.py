from utils.db import execute_query
from datetime import datetime, timedelta

class SubscriptionRepository:
    def get_packages(self):
        """Get all subscription packages"""
        query = """
            SELECT id, name, description, price, currency, duration_days, listing_limit, is_active
            FROM subscription_packages
            WHERE is_active = 1
            ORDER BY price
        """
        return execute_query(query)
    
    def get_package(self, package_id):
        """Get a subscription package by ID"""
        query = """
            SELECT id, name, description, price, currency, duration_days, listing_limit, is_active
            FROM subscription_packages
            WHERE id = %s
        """
        results = execute_query(query, (package_id,))
        return results[0] if results else None
    
    def create_subscription(self, user_id, package_id):
        """Create a new subscription"""
        # Get package details
        package = self.get_package(package_id)
        
        if not package:
            return None
        
        # Calculate end date
        start_date = datetime.now()
        end_date = start_date + timedelta(days=package['duration_days'])
        
        # Create subscription
        query = """
            INSERT INTO subscriptions (user_id, package_id, start_date, end_date, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        subscription_id = execute_query(
            query,
            (user_id, package_id, start_date, end_date, 1, start_date),
            fetch=False
        )
        
        return subscription_id
    
    def get_subscription(self, subscription_id):
        """Get a subscription by ID"""
        query = """
            SELECT s.id, s.user_id, s.package_id, s.start_date, s.end_date, s.is_active, s.created_at,
                   p.name as package_name, p.description as package_description, p.price, p.currency,
                   p.duration_days, p.listing_limit
            FROM subscriptions s
            JOIN subscription_packages p ON s.package_id = p.id
            WHERE s.id = %s
        """
        results = execute_query(query, (subscription_id,))
        return results[0] if results else None
    
    def get_active_subscription(self, user_id):
        """Get the active subscription for a user"""
        query = """
            SELECT s.id, s.user_id, s.package_id, s.start_date, s.end_date, s.is_active, s.created_at
            FROM subscriptions s
            WHERE s.user_id = %s AND s.is_active = 1 AND s.end_date > %s
            ORDER BY s.end_date DESC
            LIMIT 1
        """
        results = execute_query(query, (user_id, datetime.now()))
        return results[0] if results else None
    
    def cancel_subscription(self, subscription_id):
        """Cancel a subscription"""
        query = """
            UPDATE subscriptions
            SET is_active = 0, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), subscription_id), fetch=False)
    
    def get_user_subscriptions(self, user_id, page=1, limit=10):
        """Get subscription history for a user"""
        offset = (page - 1) * limit
        
        # Get subscriptions with pagination
        query = """
            SELECT s.id, s.user_id, s.package_id, s.start_date, s.end_date, s.is_active, s.created_at,
                   p.name as package_name, p.description as package_description, p.price, p.currency,
                   p.duration_days, p.listing_limit
            FROM subscriptions s
            JOIN subscription_packages p ON s.package_id = p.id
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
        """
        subscriptions = execute_query(query, (user_id, limit, offset))
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM subscriptions
            WHERE user_id = %s
        """
        count_result = execute_query(count_query, (user_id,))
        total = count_result[0]['total'] if count_result else 0
        
        return subscriptions, total
    
    def get_user_listings_count(self, user_id):
        """Get the count of active listings for a user"""
        query = """
            SELECT COUNT(*) as total
            FROM cars
            WHERE user_id = %s AND status IN ('approved', 'pending')
        """
        result = execute_query(query, (user_id,))
        return result[0]['total'] if result else 0
