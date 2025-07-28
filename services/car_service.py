from repositories.car_repository import CarRepository
from repositories.user_repository import UserRepository
from repositories.subscription_repository import SubscriptionRepository
from flask import request
import json

class CarService:
    def __init__(self):
        self.car_repository = CarRepository()
        self.user_repository = UserRepository()
        self.subscription_repository = SubscriptionRepository()
        # Update all car image paths to use uploads directory
        self.car_repository.update_car_image_paths()
    
    def get_cars(self, page=1, limit=10, make=None, model=None, year_from=None, year_to=None, price_from=None, price_to=None, status=None, is_featured=None, user_id=None):
        """Get all cars with pagination and filtering"""
        # Build filter conditions
        filters = {}
        if make:
            filters['make'] = make
        if model:
            filters['model'] = model
        if year_from:
            filters['year_from'] = year_from
        if year_to:
            filters['year_to'] = year_to
        if price_from:
            filters['price_from'] = price_from
        if price_to:
            filters['price_to'] = price_to
        if status:
            filters['status'] = status
        if is_featured is not None:
            filters['is_featured'] = is_featured
        if user_id:
            filters['user_id'] = user_id
            print(f"get_cars service - user_id: {user_id}, type: {type(user_id)}")  # Debug print
        
        # Get cars with pagination
        cars, total = self.car_repository.get_cars(
            page=page,
            limit=limit,
            filters=filters
        )
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'cars': cars,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }
    
    def get_car_by_id(self, car_id):
        """Get a car by ID"""
        car = self.car_repository.get_car_by_id(car_id)
        
        if car:
            # Get user details
            user = self.user_repository.get_user_by_id(car['user_id'])
            if user:
                # Format user details with only required fields
                seller_info = {
                    'id': str(user.get('id', '')),  # Convert to string to avoid null
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'profile_pic': user.get('profile_pic', ''),
                    'member_since': user.get('created_at').strftime('%B %Y') if user.get('created_at') else '',
                    'is_dealer': bool(user.get('is_dealer', 0)),
                    'company_name': user.get('company_name', '')
                }
                
                car['seller'] = seller_info
            
            # Remove user_id from car details
            car.pop('user_id', None)
            
            # Get car images
            images = self.car_repository.get_car_images(car_id)
            car['images'] = images if images else []
            
            # Get similar cars - ensure make and model are not None
            make = car.get('make', '')
            model = car.get('model', '')
            if make and model:  # Only get similar cars if both make and model exist
                similar_cars = self.car_repository.get_similar_cars(
                    make=make,
                    model=model,
                    car_id=car_id,
                    limit=5
                )
                car['similar_cars'] = similar_cars if similar_cars else []
            else:
                # If no make or model, get any available cars
                similar_cars = self.car_repository.get_similar_cars(
                    make='',
                    model='',
                    car_id=car_id,
                    limit=5
                )
                car['similar_cars'] = similar_cars if similar_cars else []
            
            # Replace None values with empty strings for all fields
            for key, value in car.items():
                if value is None:   
                    car[key] = ''
                elif isinstance(value, (int, float)):
                    car[key] = str(value)  # Convert numbers to strings
                elif isinstance(value, bool):
                    car[key] = value  # Keep booleans as is
                elif isinstance(value, list):
                    car[key] = value if value else []  # Keep empty lists as is
                elif isinstance(value, dict):
                    # Recursively handle nested dictionaries
                    for k, v in value.items():
                        if v is None:
                            value[k] = ''
                        elif isinstance(v, (int, float)):
                            value[k] = str(v)
                    car[key] = value
        
        return car if car else {}
    
    def create_car(self, user_id, ad_title, description, car_information, exterior_color, trim, regional_specs,
                  body_type, condition, badges, kilometers, location, year, warranty_date,
                  accident_history, number_of_seats, number_of_doors, fuel_type, transmission_type,
                  drive_type, engine_cc, make, model, price, extra_features, car_image, status='available',
                  draft=False, consumption='0', no_of_cylinders='0', interior='', payment_option=''):
        """Create a new car listing"""
        # Only validate required fields if not a draft
        if not draft:
            required_fields = {
                'user_id': user_id,
                'ad_title': ad_title,
                'description': description,
                'car_information': car_information,
                'exterior_color': exterior_color,
                'interior': interior,
                'trim': trim,
                'regional_specs': regional_specs,
                'body_type': body_type,
                'condition': condition,
                'badges': badges,
                'kilometers': kilometers,
                'location': location,
                'year': year,
                'warranty_date': warranty_date,
                'accident_history': accident_history,
                'number_of_seats': number_of_seats,
                'number_of_doors': number_of_doors,
                'fuel_type': fuel_type,
                'transmission_type': transmission_type,
                'drive_type': drive_type,
                'engine_cc': engine_cc,
                'make': make,
                'model': model,
                'price': price,
                'extra_features': extra_features,
                'car_image': car_image,
                'payment_option': payment_option
            }

            # Check for condition field if condition is not provided
            if not condition and 'car_condition' in request.form:
                condition = request.form['car_condition']

            for field, value in required_fields.items():
                if not value:
                    raise ValueError(f"{field} is required")

        # Create car listing with default status and approval
        car_id = self.car_repository.create_car(
            user_id=user_id,
            ad_title=ad_title,
            description=description,
            car_information=car_information,
            exterior_color=exterior_color,
            interior=interior,
            trim=trim,
            regional_specs=regional_specs,
            body_type=body_type,
            car_condition=condition,
            badges=badges,
            kilometers=kilometers,
            location=location,
            year=year,
            warranty_date=warranty_date,
            accident_history=accident_history,
            number_of_seats=number_of_seats,
            number_of_doors=number_of_doors,
            fuel_type=fuel_type,
            transmission_type=transmission_type,
            drive_type=drive_type,
            engine_cc=engine_cc,
            make=make,
            model=model,
            price=price,
            extra_features=extra_features,
            car_image=car_image,
            status=status,
            approval='pending',
            draft=draft,
            consumption=consumption,
            no_of_cylinders=no_of_cylinders,
            payment_option=payment_option
        )

        return car_id
    
    def update_car(self, car_id, user_id, ad_title=None, description=None, car_information=None, exterior_color=None, interior=None, trim=None, regional_specs=None, body_type=None, condition=None, badges=None, kilometers=None, location=None, year=None, warranty_date=None, accident_history=None, number_of_seats=None, number_of_doors=None, fuel_type=None, transmission_type=None, drive_type=None, engine_cc=None, make=None, model=None, price=None, extra_features=None, car_image=None, draft=None, consumption=None, no_of_cylinders=None, payment_option=None):
        """Update a car listing"""
        try:
            # Get the car
            car = self.car_repository.get_car_by_id(car_id)
            if not car:
                return {'success': False, 'message': 'Car not found'}
            
            # Check if user owns the car
            if str(car['user_id']) != str(user_id):
                return {'success': False, 'message': 'You are not authorized to update this car'}
            
            # Check if car is in a state that allows updates
            if car['status'] == 'sold':
                return {'success': False, 'message': 'Cannot update a sold car'}
            
            # Update the car
            success = self.car_repository.update_car(
                car_id=car_id,
                make=make,
                model=model,
                year=year,
                price=price,
                description=description,
                kilometers=kilometers,
                fuel_type=fuel_type,
                transmission=transmission_type,
                body_type=body_type,
                condition=condition,
                features=extra_features,
                location=location,
                ad_title=ad_title,
                car_information=car_information,
                trim=trim,
                regional_specs=regional_specs,
                badges=badges,
                warranty_date=warranty_date,
                accident_history=accident_history,
                number_of_seats=number_of_seats,
                number_of_doors=number_of_doors,
                drive_type=drive_type,
                engine_cc=engine_cc,
                exterior_color=exterior_color,
                interior=interior,
                draft=draft,
                consumption=consumption,
                no_of_cylinders=no_of_cylinders,
                payment_option=payment_option,
                car_image=car_image
            )
            
            if success:
                return {'success': True, 'message': 'Car updated successfully'}
            else:
                return {'success': False, 'message': 'Failed to update car'}
                
        except Exception as e:
            print(f"Error updating car: {str(e)}")
            return {'success': False, 'message': f'An error occurred while updating the car: {str(e)}'}
    
    def delete_car(self, car_id):
        """Delete a car listing"""
        try:
            # Delete the car
            success, message = self.car_repository.delete_car(car_id)
            return success, message
            
        except Exception as e:
            print(f"Error in delete_car service: {str(e)}")
            return False, str(e)
    
    def mark_as_sold(self, car_id, user_id):
        """Mark a car listing as sold"""
        try:
            # Check if car exists
            car = self.car_repository.get_car_by_id(car_id)
            
            if not car:
                return {
                    'success': False,
                    'message': 'Car listing not found'
                }
            
            # Check if the car belongs to the user
            if str(car['user_id']) != str(user_id):
                return {
                    'success': False,
                    'message': 'You do not have permission to update this car listing'
                }
            
            # Mark car as sold
            self.car_repository.update_car_status(car_id, 'sold')
            
            return {
                'success': True,
                'message': 'Car listing marked as sold successfully'
            }
        except Exception as e:
            print(f"Error in mark_as_sold: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_featured_cars(self):
        """Get featured car listings"""
        cars = self.car_repository.get_featured_cars()
        return {
            'cars': cars,
            'pagination': {
                'page': 1,
                'limit': len(cars),
                'total': len(cars),
                'total_pages': 1
            }
        }
    
    def get_recommended_cars(self, user_id, limit=10):
        """Get recommended car listings based on user preferences"""
        if not user_id:
            # Return featured cars if no user ID provided
            return self.get_featured_cars()
        
        # Get user's search history
        search_history = self.car_repository.get_user_search_history(user_id, limit=5)
        
        if not search_history:
            # Return featured cars if no search history
            return self.get_featured_cars()
        
        # Extract search parameters
        makes = [search.get('make') for search in search_history if search.get('make')]
        models = [search.get('model') for search in search_history if search.get('model')]
        
        # Get recommended cars based on search history
        cars = self.car_repository.get_recommended_cars(makes, models, limit)
        
        return cars
    
    def get_user_cars(self, user_id, page=1, limit=10):
        """Get user's cars separated by status and draft state"""
        try:
            # Get cars from repository
            cars = self.car_repository.get_user_cars(user_id, page, limit)
            
            # Add views to draft cars only
            for car in cars['draft']:
                car['views'] = car.get('views', 0)
            
            return {
                'success': True,
                'data': {
                    'approved_pending': cars['approved_pending'],
                    'sold': cars['sold'],
                    'draft': cars['draft']
                }
            }
        except Exception as e:
            print(f"Error in get_user_cars: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to fetch user cars',
                'error': str(e)
            }

    def get_all_makes(self):
        """Get all car makes with their images"""
        try:
            makes = self.car_repository.get_all_makes()
            
            # Format the response to ensure consistent structure
            formatted_makes = []
            for make in makes:
                # Ensure image path uses static/uploads/ instead of api/uploads/
                image = make.get('image', '')
                if image:
                    image = image.replace('api/uploads/', 'static/uploads/')
                    
                formatted_make = {
                    'id': str(make.get('id', '')),
                    'name': make.get('name', ''),
                    'image': image
                }
                formatted_makes.append(formatted_make)
            
            return formatted_makes
        except Exception as e:
            print(f"Error in get_all_makes: {str(e)}")
            raise e

    def get_models_by_make(self, make_name):
        """Get all models for a specific make"""
        return self.car_repository.get_models_by_make(make_name)

    def get_years_by_make_model(self, make_name, model_name):
        """Get all years for a specific make and model"""
        return self.car_repository.get_years_by_make_model(make_name, model_name)

    def get_trims_by_make_model_year(self, make_name, model_name):
        """Get all trims for a specific make, model"""
        return self.car_repository.get_trims_by_make_model_year(make_name, model_name)

    def get_all_body_types(self):
        """Get all body types"""
        return self.car_repository.get_all_body_types()

    def get_all_locations(self):
        """Get all locations"""
        return self.car_repository.get_all_locations()

    def get_all_colors(self):
        """Get all colors"""
        return self.car_repository.get_all_colors()

    def get_regional_specs(self):
        """Get all regional specs"""
        return self.car_repository.get_regional_specs()

    def get_extra_features(self):
        """Get all extra features"""
        return self.car_repository.get_extra_features()

    def get_interiors(self):
        """Get all interiors"""
        return self.car_repository.get_interiors()

    def get_accident_histories(self):
        """Get all accident histories"""
        return self.car_repository.get_accident_histories()

    def get_car_conditions(self):
        """Get all car conditions"""
        return self.car_repository.get_car_conditions()

    def get_badges(self):
        """Get all badges"""
        return self.car_repository.get_badges()

    def get_number_of_seats(self):
        """Get all number of seats"""
        return self.car_repository.get_number_of_seats()

    def get_number_of_doors(self):
        """Get all number of doors"""
        return self.car_repository.get_number_of_doors()

    def get_fuel_types(self):
        """Get all fuel types"""
        return self.car_repository.get_fuel_types()

    def get_transmission_types(self):
        """Get all transmission types"""
        return self.car_repository.get_transmission_types()

    def get_drive_types(self):
        """Get all drive types"""
        return self.car_repository.get_drive_types()

    def get_user_details_with_cars(self, user_id, page=1, limit=10, status=None):
        """Get user details and their listed cars"""
        # Get user details
        user = self.user_repository.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Remove sensitive information
        user.pop('password', None)
        
        # Get user's cars
        cars_result = self.get_user_cars(
            user_id=user_id,
            page=page,
            limit=limit,
            status=status
        )
        
        # Format response
        return {
            'user': {
                'id': str(user.get('id', '')),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'email': user.get('email', ''),
                'phone_number': user.get('phone_number', ''),
                'profile_pic': user.get('profile_pic', ''),
                'user_type': user.get('user_type', ''),
                'is_dealer': bool(user.get('is_dealer', 0)),
                'company_name': user.get('company_name', ''),
                'company_address': user.get('company_address', ''),
                'company_phone_number': user.get('company_phone_number', ''),
                'company_registration_number': user.get('company_registration_number', ''),
                'facebook_page': user.get('facebook_page', ''),
                'instagram_company_profile': user.get('instagram_company_profile', ''),
                'member_since': user.get('created_at').strftime('%B %Y') if user.get('created_at') else '',
                'listings_count': cars_result['pagination']['total']
            },
            'cars': cars_result['cars'],
            'pagination': cars_result['pagination']
        }

    def get_car_upload_option_details(self):
        """Get all car upload option details from various tables"""
        try:
            # Get data from all required tables
            colours = self.car_repository.get_all_colors()
            car_conditions = self.car_repository.get_all_car_conditions()
            locations = self.car_repository.get_all_locations()
            body_types = self.car_repository.get_all_body_types()
            badges = self.car_repository.get_all_badges()
            regional_specs = self.car_repository.get_all_regional_specs()
            accident_histories = self.car_repository.get_all_accident_histories()
            number_of_seats = self.car_repository.get_all_number_of_seats()
            number_of_doors = self.car_repository.get_all_number_of_doors()
            number_of_cylinders = self.car_repository.get_all_number_of_cylinders()
            fuel_types = self.car_repository.get_all_fuel_types()
            transmission_types = self.car_repository.get_all_transmission_types()
            drive_types = self.car_repository.get_all_drive_types()
            extra_features = self.car_repository.get_all_extra_features()
            interiors = self.car_repository.get_all_interiors()
            payment_options = self.car_repository.get_payment_options()
            
            # Combine all data into a single response
            return {
                'colours': colours,
                'car_conditions': car_conditions,
                'locations': locations,
                'body_types': body_types,
                'badges': badges,
                'regional_specs': regional_specs,
                'accident_histories': accident_histories,
                'number_of_seats': number_of_seats,
                'number_of_doors': number_of_doors,
                'number_of_cylinders': number_of_cylinders,
                'fuel_types': fuel_types,
                'transmission_types': transmission_types,
                'drive_types': drive_types,
                'extra_features': extra_features,
                'interiors': interiors,
                'payment_options': payment_options
            }
            
        except Exception as e:
            raise Exception(f"Failed to get car upload option details: {str(e)}")

    def increment_car_views(self, car_id):
        """Increment the views count for a car"""
        try:
            self.car_repository.increment_car_views(car_id)
            return True
        except Exception as e:
            print(f"Error incrementing car views: {str(e)}")
            return False

    def increment_car_likes(self, car_id):
        """Increment the likes count for a car"""
        try:
            self.car_repository.increment_car_likes(car_id)
            return True
        except Exception as e:
            print(f"Error incrementing car likes: {str(e)}")
            return False
