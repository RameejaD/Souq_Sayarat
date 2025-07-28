from utils.db import execute_query
from datetime import datetime
import json
class UserRepository:
    def create_user(self, first_name, last_name, email, date_of_birth, user_type,
                    is_dealer, company_name, owner_name, company_address, company_phone_number,
                    company_registration_number, facebook_page, instagram_company_profile,
                    profile_pic, phone_number):
        
        """Create a new user"""
        # Convert is_dealer to integer (0 or 1)
        is_dealer_int = 1 if is_dealer else 0
        user_type = 'dealer' if is_dealer else 'individual'

        query = """
        INSERT INTO users (
        first_name, last_name, email, date_of_birth, user_type, is_dealer,
        company_name, owner_name, company_address, company_phone_number,
        company_registration_number, facebook_page, instagram_company_profile,
        profile_pic, phone_number, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        user_id = execute_query(
            query,
            (
                first_name, last_name, email, date_of_birth, user_type, is_dealer_int,
                company_name, owner_name, company_address, company_phone_number,
                company_registration_number, facebook_page, instagram_company_profile,
                profile_pic, phone_number, datetime.now()
            ),
            fetch=False
        )
        return user_id

    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        query = """
            SELECT *
            FROM users
            WHERE id = %s
        """
        results = execute_query(query, (user_id,))
        return results[0] if results else None
    
    def get_user_by_phone(self, phone_number):
        """Get a user by phone number"""
        query = """
            SELECT id, first_name, last_name, email, date_of_birth, profile_image, whatsapp,
                   location, user_type, is_verified, is_banned, ban_reason, created_at, updated_at
            FROM users
            WHERE phone_number = %s
        """
        results = execute_query(query, (phone_number,))
        return results[0] if results else None
    
    def get_public_profile(self, user_id):
        """Get a user's public profile"""
        query = """
            SELECT id, first_name, last_name, profile_image, created_at
            FROM users
            WHERE id = %s
        """
        results = execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_user(self, user_id, data):
        """Update user details"""
        # Get current user data
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        # Filter out None values and empty strings
        update_data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        if not update_data:
            return False

        # Check if is_dealer is being updated to 0
        is_dealer = update_data.get('is_dealer')
        if is_dealer is not None:
            is_dealer = bool(is_dealer)
            if not is_dealer:
                # Force update dealer fields to empty strings
                dealer_fields = [
                    'company_name', 'company_address', 'owner_name',
                    'company_phone_number', 'company_registration_number',
                    'facebook_page', 'instagram_company_profile'
                ]
                for field in dealer_fields:
                    update_data[field] = ''
                # Update user_type to individual
                update_data['user_type'] = 'individual'
            else:
                update_data['user_type'] = 'dealer'
            
        # Build update query
        set_clauses = []
        params = []
        
        for field, value in update_data.items():
            if field == 'is_dealer':
                # Convert is_dealer to integer (0 or 1)
                value = 1 if value in [True, 'true', '1', 1, 'yes'] else 0
            set_clauses.append(f"{field} = %s")
            params.append(value)
            
        # Add updated_at
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add user_id to params
        params.append(user_id)
        
        # Debug log for SQL query
        query = f"""
            UPDATE users
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        print(f"Executing SQL query: {query}")  # Debug log
        print(f"With params: {params}")  # Debug log
        
        execute_query(query, params, fetch=False)
        return True

    def update_phone_number(self, user_id, phone_number):
        """Update user's phone number"""
        query = """
            UPDATE users
            SET phone_number = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        execute_query(query, (phone_number, user_id), fetch=False)
        return True

    def update_user_phone_number(self, user_id, new_phone_number):
        """Update user's phone number"""
        query = """
            UPDATE users
            SET phone_number = %s
            WHERE id = %s
        """
        execute_query(query, (new_phone_number, user_id), fetch=False)

    def save_otp(self, user_id, otp):
        """Save OTP for phone verification"""
        query = """
            INSERT INTO phone_verification_otps (user_id, otp, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """
        execute_query(query, (user_id, otp), fetch=False)
        return True

    def verify_otp(self, user_id, otp):
        """Verify OTP for phone number update"""
        query = """
            SELECT id
            FROM phone_verification_otps
            WHERE user_id = %s 
            AND otp = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            AND used = 0
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = execute_query(query, (user_id, otp))
        
        if result:
            # Mark OTP as used
            update_query = """
                UPDATE phone_verification_otps
                SET used = 1
                WHERE id = %s
            """
            execute_query(update_query, (result[0]['id'],), fetch=False)
            return True
            
        return False

    def update_password(self, user_id, password):
        """Update a user's password"""
        query = """
            UPDATE users
            SET password = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (password, datetime.now(), user_id), fetch=False)
    
    def get_favorites(self, user_id, page=1, limit=10):
        """Get favorite car listings for a user"""
        offset = (page - 1) * limit
        
        # Get favorites with pagination
        query = """
            SELECT c.id, c.user_id, c.make, c.model, c.year, c.price, c.description, c.exterior_color as color,
                   c.kilometers as mileage, c.fuel_type, c.transmission_type as transmission, c.body_type, c.`condition`,
                   c.location, c.status, c.created_at, c.updated_at, c.car_image,
                   u.first_name as seller_first_name, u.last_name as seller_last_name,
                   u.profile_pic as seller_profile_image, u.user_type as seller_type,
                   u.is_verified as seller_is_verified,
                   (SELECT JSON_ARRAYAGG(image_url) FROM car_images WHERE car_id = c.id) as images
            FROM favorites f
            LEFT JOIN cars c ON f.car_id = c.id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
        """
        favorites = execute_query(query, (user_id, limit, offset))
        
        # Format image URLs
        for favorite in favorites:
            if favorite.get('car_image'):
                filename = favorite['car_image'].split('/')[-1]
                favorite['car_image'] = f"/static/uploads/{filename}"
            
            if favorite.get('images'):
                try:
                    images = json.loads(favorite['images'])
                    favorite['images'] = [f"/static/uploads/{img.split('/')[-1]}" for img in images]
                except:
                    favorite['images'] = []
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM favorites f
            LEFT JOIN cars c ON f.car_id = c.id
            WHERE f.user_id = %s
        """
        count_result = execute_query(count_query, (user_id,))
        total = count_result[0]['total'] if count_result else 0
        
        return favorites, total
    
    def is_favorite(self, user_id, car_id):
        """Check if a car is in a user's favorites"""
        query = """
            SELECT 1
            FROM favorites
            WHERE user_id = %s AND car_id = %s
        """
        results = execute_query(query, (user_id, car_id))
        return bool(results)
    
    def add_favorite(self, user_id, car_id):
        """Add a car to favorites"""
        query = """
            INSERT INTO favorites (user_id, car_id, created_at)
            VALUES (%s, %s, %s)
        """
        try:
            execute_query(query, (user_id, car_id, datetime.now()), fetch=False)
            return True
        except Exception as e:
            return False
    
    def remove_favorite(self, user_id, car_id):
        """Remove a car from favorites"""
        query = """
            DELETE FROM favorites
            WHERE user_id = %s AND car_id = %s
        """
        try:
            execute_query(query, (user_id, car_id), fetch=False)
            return True
        except Exception as e:
            print(f"Error removing from favorites: {str(e)}")
            return False
    
    def get_saved_searches(self, user_id, page=1, limit=10):
        """Get saved searches for a user"""
        offset = (page - 1) * limit
        
        # Get saved searches with pagination
        query = """
            SELECT id, name, search_params, notification, created_at
            FROM saved_searches
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        searches = execute_query(query, (user_id, limit, offset))
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM saved_searches
            WHERE user_id = %s
        """
        count_result = execute_query(count_query, (user_id,))
        total = count_result[0]['total'] if count_result else 0
        
        return searches, total
    
    def get_saved_search(self, search_id):
        """Get a saved search by ID"""
        query = """
            SELECT id, user_id, name, search_params, notification, created_at
            FROM saved_searches
            WHERE id = %s
        """
        results = execute_query(query, (search_id,))
        
        # Add debug logging
        print(f"Search ID: {search_id}")
        print(f"Query results: {results}")
        
        if not results:
            print("No results found for search_id")
            return None
            
        search = results[0]
        if not search:
            print("Empty result for search_id")
            return None
            
        # Parse search_params JSON if it exists
        if search['search_params']:
            try:
                search['search_params'] = json.loads(search['search_params'])
            except json.JSONDecodeError as e:
                print(f"Error parsing search_params JSON: {e}")
                search['search_params'] = None
                
        print(f"Returning search: {search}")
        return search
    
    def save_search(self, user_id, search_params, name, notification=0):
        """Save a search for a user"""
        try:
            # Filter search_params to only include specified fields
            filtered_params = {
                'make': search_params.get('make'),
                'model': search_params.get('model'),
                'location': search_params.get('location'),
                'body_type': search_params.get('body_type')
            }
            
            # Remove None values and empty strings
            filtered_params = {k: v for k, v in filtered_params.items() if v is not None and v != ''}
            
            # Convert filtered_params to JSON string
            search_params_str = json.dumps(filtered_params, ensure_ascii=False)
            
            # Insert into saved_searches table
            query = """
                INSERT INTO saved_searches (user_id, search_params, name, notification, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (user_id, search_params_str, name, notification, datetime.now())
            
            # Execute query with parameters
            search_id = execute_query(
                query,
                params,
                fetch=False
            )
            
            return search_id
            
        except Exception as e:
            raise e
    
    def delete_saved_search(self, search_id, user_id):
        """Delete a saved search"""
        query = """
            DELETE FROM saved_searches
            WHERE id = %s AND user_id = %s
        """
        execute_query(query, (search_id, user_id), fetch=False)
    
    def get_users(self, page=1, limit=10, filters=None):
        """Get all users with pagination and filtering"""
        offset = (page - 1) * limit
        filters = filters or {}
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if 'search' in filters:
            where_clauses.append("(first_name LIKE %s OR last_name LIKE %s OR phone_number LIKE %s)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])
        
        if 'user_type' in filters:
            where_clauses.append("user_type = %s")
            params.append(filters['user_type'])
        
        # Construct final query
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get users with pagination
        query = f"""
            SELECT id, phone_number, first_name, last_name, profile_image, whatsapp,
                   location, user_type, is_verified, is_banned, ban_reason, created_at, updated_at
            FROM users
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        users = execute_query(query, params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM users
            {where_clause}
        """
        count_result = execute_query(count_query, params[:-2] if params else [])
        total = count_result[0]['total'] if count_result else 0
        
        return users, total
    
    def get_users_count(self, user_type=None):
        """Get the count of users"""
        if user_type:
            query = """
                SELECT COUNT(*) as total
                FROM users
                WHERE user_type = %s
            """
            result = execute_query(query, (user_type,))
        else:
            query = """
                SELECT COUNT(*) as total
                FROM users
            """
            result = execute_query(query)
        
        return result[0]['total'] if result else 0
    
    def get_recent_users(self, limit=5):
        """Get recently registered users"""
        query = """
            SELECT id, phone_number, first_name, last_name, user_type, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (limit,))
    
    def verify_user(self, user_id):
        """Verify a user (for dealers)"""
        query = """
            UPDATE users
            SET is_verified = 1, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), user_id), fetch=False)
    
    def ban_user(self, user_id, reason=None):
        """Ban a user"""
        query = """
            UPDATE users
            SET is_banned = 1, ban_reason = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (reason, datetime.now(), user_id), fetch=False)
    
    def unban_user(self, user_id):
        """Unban a user"""
        query = """
            UPDATE users
            SET is_banned = 0, ban_reason = NULL, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), user_id), fetch=False)

    def update_saved_search_notification(self, search_id, user_id, notification):
        """Update notification status for a saved search"""
        query = """
            UPDATE saved_searches
            SET notification = %s
            WHERE id = %s AND user_id = %s
        """
        execute_query(query, (notification, search_id, user_id), fetch=False)
        return True

    def get_subscription_packages(self, target_user_type=None):
        """Get subscription packages, optionally filtered by user type"""
        query = """
            SELECT id, name, description, price, currency, duration_days, 
                   listing_limit, is_active, created_at, updated_at, target_user_type
            FROM subscription_packages
            WHERE is_active = 1
        """
        params = []
        
        if target_user_type:
            query += " AND target_user_type = %s"
            params.append(target_user_type)
            
        query += " ORDER BY price ASC"
        
        return execute_query(query, params)

    def block_user(self, blocker_id, blocked_id):
        """Block a user"""
        query = """
            INSERT INTO user_blocks (blocker_id, blocked_id, created_at)
            VALUES (%s, %s, NOW())
        """
        execute_query(query, (blocker_id, blocked_id), fetch=False)
        return True

    def unblock_user(self, blocker_id, blocked_id):
        """Unblock a user"""
        query = """
            DELETE FROM user_blocks 
            WHERE blocker_id = %s AND blocked_id = %s
        """
        execute_query(query, (blocker_id, blocked_id), fetch=False)
        return True

    def is_blocked(self, blocker_id, blocked_id):
        """Check if a user is blocked"""
        query = """
            SELECT 1 
            FROM user_blocks 
            WHERE blocker_id = %s AND blocked_id = %s
        """
        result = execute_query(query, (blocker_id, blocked_id))
        return bool(result)

    def get_blocked_users(self, user_id):
        """Get list of users blocked by a user"""
        query = """
            SELECT u.id, u.first_name, u.last_name, u.profile_pic, u.user_type,
                   u.is_dealer, u.company_name, b.created_at as blocked_at
            FROM user_blocks b
            JOIN users u ON b.blocked_id = u.id
            WHERE b.blocker_id = %s
            ORDER BY b.created_at DESC
        """
        return execute_query(query, (user_id,))

    def get_pending_dealer_verifications(self, type='new'):
        # Use is_verified = 'pending' for pending dealer verification, 'resubmission' for resubmissions
        if type == 'new':
            query = """
                SELECT COUNT(*) as count FROM users WHERE user_type = 'dealer' AND is_verified = 'pending'
            """
            result = execute_query(query)
            return result[0]['count'] if result else 0
        else:
            query = """
                SELECT COUNT(*) as count FROM users WHERE user_type = 'dealer' AND is_verified = 'resubmission'
            """
            result = execute_query(query)
            return result[0]['count'] if result else 0

    def get_user_incident_reports_list(self):
        query = "SELECT id, report_user_reason FROM reported_reason"
        return execute_query(query)

    def save_phone_change_otp(self, request_id, phone_number, otp, expiry):
        """Save OTP request"""
        query = """
            INSERT INTO otp_requests (request_id, phone_number, otp, expiry, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        execute_query(query, (request_id, phone_number, otp, expiry), fetch=False)

    def get_phone_change_otp(self, request_id):
        """Get OTP request by ID"""
        query = """
            SELECT request_id, phone_number, otp, expiry
            FROM otp_requests
            WHERE request_id = %s
        """
        result = execute_query(query, (request_id,))
        return result[0] if result else None

    def delete_phone_change_otp(self, request_id):
        """Delete OTP request"""
        query = """
            DELETE FROM otp_requests
            WHERE request_id = %s
        """
        execute_query(query, (request_id,), fetch=False)
