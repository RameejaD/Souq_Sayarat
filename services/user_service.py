from repositories.user_repository import UserRepository
from repositories.car_repository import CarRepository
import random
import os

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.car_repository = CarRepository()
    
    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        user = self.user_repository.get_user_by_id(user_id)
        
        if user:
            # Remove sensitive information
            user.pop('password', None)
        
        return user
    
    def get_public_profile(self, user_id):
        """Get a user's public profile"""
        user = self.user_repository.get_public_profile(user_id)
        
        if user:
            # Format the created_at date to show only month and year
            if user.get('created_at'):
                user['created_at'] = user['created_at'].strftime('%B %Y')
            
            # Get user's car listings
            cars, total = self.car_repository.get_cars(
                page=1,
                limit=10,
                filters={'user_id': user_id}
            )
            
            # Add cars to the response
            user['cars'] = cars
            user['total_cars'] = total
        
        return user
    
    def update_user(self, user_id, data=None, **kwargs):
        """Update user details"""
        # Combine data dictionary with kwargs if both are provided
        update_data = data or {}
        update_data.update(kwargs)
        
        # Get current user data
        current_user = self.user_repository.get_user_by_id(user_id)
        if not current_user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Filter out None values and empty strings
        fields_to_update = {k: v for k, v in update_data.items() if v is not None and v != ''}
        
        # Remove phone_number from data if present
        if 'phone_number' in fields_to_update:
            return {
                'success': False,
                'message': 'Phone number can only be updated through the phone verification process'
            }

        # Handle profile picture path
        if 'profile_pic' in fields_to_update:
            profile_pic = fields_to_update['profile_pic']
            # Convert local path to URL path if needed
            if '\\' in profile_pic or '/' in profile_pic:
                # Extract filename from path
                filename = os.path.basename(profile_pic)
                # Create URL path
                fields_to_update['profile_pic'] = f"/static/profile_pics/{filename}"

        # Define allowed fields for each user type
        dealer_fields = [
            # Company information
            'company_name', 'company_address', 'owner_name',
            'company_phone_number', 'company_registration_number',
            'facebook_page', 'instagram_company_profile',
            # Personal information
            'first_name', 'last_name', 'email', 'date_of_birth',
            # Common fields
            'profile_pic', 'is_dealer'
        ]

        # Check if is_dealer is being updated
        is_dealer = fields_to_update.get('is_dealer')
        if is_dealer is not None:
            is_dealer = bool(is_dealer)
            # If is_dealer is False, set all dealer-specific fields to empty string
            if not is_dealer:
                for field in ['company_name', 'company_address', 'owner_name',
                            'company_phone_number', 'company_registration_number',
                            'facebook_page', 'instagram_company_profile']:
                    fields_to_update[field] = ''

        # Always use dealer fields list and filter the fields
        filtered_fields = {k: v for k, v in fields_to_update.items() if k in dealer_fields}
        
        # Debug log for profile picture
        if 'profile_pic' in filtered_fields:
            print(f"Updating profile picture to: {filtered_fields['profile_pic']}")
            
        # Update user details
        success = self.user_repository.update_user(user_id, filtered_fields)
        if not success:
            return {
                'success': False,
                'message': 'No valid fields to update'
            }
            
        # Get updated user
        updated_user = self.user_repository.get_user_by_id(user_id)
        if updated_user:
            # Convert is_dealer to boolean for response
            is_dealer = bool(updated_user.get('is_dealer', 0))
            updated_user['is_dealer'] = is_dealer
            updated_user['flag'] = is_dealer  # Add flag variable based on is_dealer
            
        return {
            'success': True,
            'data': updated_user
        }

    def initiate_phone_update(self, user_id, new_phone_number):
        """Initiate phone number update process"""
        # Generate OTP (6 digits)
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Save OTP
        self.user_repository.save_otp(user_id, otp)
        
        # TODO: Send OTP via SMS
        # For now, we'll just return it in the response
        return {
            'success': True,
            'message': 'OTP sent successfully',
            'otp': otp  # Remove this in production
        }

    def verify_and_update_phone(self, user_id, otp, new_phone_number):
        """Verify OTP and update phone number"""
        # Verify OTP
        if not self.user_repository.verify_otp(user_id, otp):
            return {
                'success': False,
                'message': 'Invalid or expired OTP'
            }
            
        # Update phone number
        self.user_repository.update_phone_number(user_id, new_phone_number)
        
        return {
            'success': True,
            'message': 'Phone number updated successfully'
        }
    
    def get_favorites(self, user_id, page=1, limit=10):
        """Get favorite car listings for a user"""
        print(f"UserService: Getting favorites for user {user_id}")
        
        # Get favorites with pagination
        favorites, total = self.user_repository.get_favorites(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        print(f"UserService: Found {len(favorites)} favorites")
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'favorites': favorites,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }
    
    def add_favorite(self, user_id, car_id):
        """Add a car to favorites"""
        # Check if car exists
        car = self.car_repository.get_car_by_id(car_id)
        
        if not car:
            return {
                'success': False,
                'message': 'Car listing not found'
            }
        
        # Check if already in favorites
        if self.user_repository.is_favorite(user_id, car_id):
            return {
                'success': True,
                'message': 'Car is already in favorites'
            }
        
        # Add to favorites
        if self.user_repository.add_favorite(user_id, car_id):
            # Increment likes count
            self.car_repository.increment_car_likes(car_id)
            return {
                'success': True,
                'message': 'Car added to favorites successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to add car to favorites'
            }
    
    def remove_favorite(self, user_id, car_id):
        """Remove a car from favorites"""
        # Check if in favorites
        if not self.user_repository.is_favorite(user_id, car_id):
            return {
                'success': False,
                'message': 'Car is not in favorites'
            }
        
        # Remove from favorites
        if self.user_repository.remove_favorite(user_id, car_id):
            # Decrement likes count
            self.car_repository.decrement_car_likes(car_id)
            return {
                'success': True,
                'message': 'Car removed from favorites successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to remove car from favorites'
            }
    
    def get_saved_searches(self, user_id, page=1, limit=10):
        """Get saved searches for a user"""
        # Get saved searches with pagination
        searches, total = self.user_repository.get_saved_searches(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'searches': searches,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }
    
    def save_search(self, user_id, search_params, name=None, notification=0):
        """Save a search for a user"""
        # Filter only the required fields
        filtered_params = {
            'make': search_params.get('make'),
            'model': search_params.get('model'),
            'location': search_params.get('location'),
            'body_type': search_params.get('body_type')
        }
        
        # Remove None values
        filtered_params = {k: v for k, v in filtered_params.items() if v is not None}
        
        # Create a name if not provided
        if not name:
            # Extract key parameters for name
            make = filtered_params.get('make', '')
            model = filtered_params.get('model', '')
            
            if make and model:
                name = f"{make} {model}"
            elif make:
                name = make
            else:
                name = "Saved Search"
        
        # Save search with only the filtered parameters
        search_id = self.user_repository.save_search(
            user_id=user_id,
            search_params=filtered_params,
            name=name,
            notification=notification
        )
        
        return {
            'success': True,
            'search_id': search_id
        }

    def update_saved_search_notification(self, user_id, search_id, notification):
        """Update notification status for a saved search"""
        try:
            # Check if search exists
            search = self.user_repository.get_saved_search(search_id)
            
            if not search:
                return {
                    'success': False,
                    'message': 'Saved search not found'
                }
            
            # Ensure notification is 0 or 1
            notification = 1 if notification in [1, '1', True, 'true'] else 0
            
            # Update notification status
            self.user_repository.update_saved_search_notification(search_id, user_id, notification)
            return {
                'success': True,
                'message': 'Notification status updated successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating notification status: {str(e)}'
            }

    def delete_saved_search(self, user_id, search_id):
        """Delete a saved search"""
        try:
            # Check if search exists
            search = self.user_repository.get_saved_search(search_id)
            
            if not search:
                return {
                    'success': False,
                    'message': 'Saved search not found'
                }
            
            # Delete saved search
            self.user_repository.delete_saved_search(search_id, user_id)
            return {
                'success': True,
                'message': 'Saved search deleted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting saved search: {str(e)}'
            }
    
    def register_user(self, first_name, last_name, email, date_of_birth, is_dealer,
                    company_name=None, owner_name=None, company_address=None,
                    company_phone_number=None, company_registration_number=None,
                    facebook_page=None, instagram_company_profile=None,
                    profile_pic=None, phone_number=None):
        """Register a new user"""
        # Convert is_dealer to integer (0 or 1)
        is_dealer_int = 1 if is_dealer else 0
        
        # Create user
        user_id = self.user_repository.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_of_birth=date_of_birth,
            user_type='dealer' if is_dealer else 'individual',
            is_dealer=is_dealer_int,
            company_name=company_name,
            owner_name=owner_name,
            company_address=company_address,
            company_phone_number=company_phone_number,
            company_registration_number=company_registration_number,
            facebook_page=facebook_page,
            instagram_company_profile=instagram_company_profile,
            profile_pic=profile_pic,
            phone_number=phone_number
        )
        
        # Get created user
        user = self.user_repository.get_user_by_id(user_id)
        user.pop('password', None)
        
        # Convert is_dealer back to boolean for response
        user['is_dealer'] = bool(user.get('is_dealer', 0))
        
        return {
            'success': True,
            'user': user,
            'is_dealer': bool(is_dealer),
            'flag': is_dealer_int
        }

    def get_subscription_packages(self):
        """Get subscription packages separated by user type"""
        try:
            # Get packages for dealers
            dealer_packages = self.user_repository.get_subscription_packages('dealer')
            
            # Get packages for individuals
            individual_packages = self.user_repository.get_subscription_packages('individual')
            
            return {
                'success': True,
                'data': {
                    'dealer_packages': dealer_packages,
                    'individual_packages': individual_packages
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting subscription packages: {str(e)}'
            }

    def block_user(self, blocker_id, blocked_id):
        """Block a user"""
        try:
            # Check if user exists
            blocked_user = self.user_repository.get_user_by_id(blocked_id)
            if not blocked_user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Check if already blocked
            if self.user_repository.is_blocked(blocker_id, blocked_id):
                return {
                    'success': False,
                    'message': 'User is already blocked'
                }
            
            # Block user
            self.user_repository.block_user(blocker_id, blocked_id)
            
            return {
                'success': True,
                'message': 'User blocked successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def unblock_user(self, blocker_id, blocked_id):
        """Unblock a user"""
        try:
            # Check if user exists
            blocked_user = self.user_repository.get_user_by_id(blocked_id)
            if not blocked_user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Check if blocked
            if not self.user_repository.is_blocked(blocker_id, blocked_id):
                return {
                    'success': False,
                    'message': 'User is not blocked'
                }
            
            # Unblock user
            self.user_repository.unblock_user(blocker_id, blocked_id)
            
            return {
                'success': True,
                'message': 'User unblocked successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def get_blocked_users(self, user_id):
        """Get list of blocked users"""
        try:
            blocked_users = self.user_repository.get_blocked_users(user_id)
            
            return {
                'success': True,
                'data': blocked_users
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def soft_delete_user(self, user_id):
        """Soft delete a user by setting deleted_at"""
        from datetime import datetime
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        self.user_repository.soft_delete_user(user_id, datetime.now())
        return {'success': True}

    def save_delete_otp(self, user_id, otp):
        """Save a 4-digit OTP for account deletion verification"""
        try:
            self.user_repository.save_delete_otp(user_id, otp)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def verify_and_delete_user(self, user_id, otp):
        """Verify the OTP and soft delete the user if correct"""
        if not self.user_repository.verify_delete_otp(user_id, otp):
            return {'success': False, 'message': 'Invalid or expired OTP'}
        from datetime import datetime
        self.user_repository.soft_delete_user(user_id, datetime.now())
        return {'success': True}

    def get_user_summary(self, user_id):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        # Get listing stats
        stats = self.car_repository.get_user_listing_stats(user_id)
        if user['user_type'] == 'dealer':
            data = {
                "profile_pic": user.get("profile_pic"),
                "company_name": user.get("company_name"),
                "company_logo": user.get("profile_pic"),
                "owner_name": user.get("owner_name"),
                "company_address": user.get("company_address"),
                "company_phone_number": user.get("company_phone_number"),
                "company_registration_number": user.get("company_registration_number"),
                "facebook_page": user.get("facebook_page"),
                "instagram_company_profile": user.get("instagram_company_profile"),
                "uploaded_documents": {
                    "trade_license": user.get("trade_license_doc"),
                    "id": user.get("id_doc")
                },
                "listing_stats": stats,
                "registered_since": user.get("created_at"),
                "is_verified": user.get("is_verified"),
                "is_banned": user.get("is_banned"),
                "ban_reason": user.get("ban_reason"),
            }
        else:
            data = {
                "profile_pic": user.get("profile_pic"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "phone_number": user.get("phone_number"),
                "email": user.get("email"),
                "whatsapp": user.get("whatsapp"),
                "location": user.get("location"),
                "registered_since": user.get("created_at"),
                "listing_stats": stats,
                "is_verified": user.get("is_verified"),
                "is_banned": user.get("is_banned"),
                "ban_reason": user.get("ban_reason"),
            }
        return {'success': True, 'data': data}

    def report_user(self, reporter_user_id, reported_user_id, report_reason):
        """Report a user (insert into reported_users)"""
        return self.user_repository.report_user(reporter_user_id, reported_user_id, report_reason)
