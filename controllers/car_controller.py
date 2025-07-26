from flask import Blueprint, request, jsonify
from config import ALLOWED_EXTENSIONS
from services.car_service import CarService
from utils.auth import token_required
from utils.file_upload import save_file
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
import json
import os
from werkzeug.utils import secure_filename
import pandas as pd

car_bp = Blueprint('car', __name__)
car_service = CarService()

@car_bp.route('/list', methods=['GET'])
@jwt_required(optional=True)  # Make JWT optional but still verify if present
def get_cars():
    """Get all cars with pagination and filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        make = request.args.get('make')
        model = request.args.get('model')
        year_from = request.args.get('year_from', type=int)
        year_to = request.args.get('year_to', type=int)
        price_from = request.args.get('price_from', type=float)
        price_to = request.args.get('price_to', type=float)
        status = request.args.get('status')
        is_featured = request.args.get('is_featured', type=bool)
        
        # Get user ID from JWT token if available
        user_id = get_jwt_identity()
        print(f"get_cars - user_id from token: {user_id}")  # Debug print
        
        # Get cars
        result = car_service.get_cars(
            page=page,
            limit=limit,
            make=make,
            model=model,
            year_from=year_from,
            year_to=year_to,
            price_from=price_from,
            price_to=price_to,
            status=status,
            is_featured=is_featured,
            user_id=user_id  # Pass user_id to service
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/details/<int:car_id>', methods=['GET'])
def get_car_details(car_id):
    """Get a car by ID"""
    try:
        # Increment views for the car
        car_service.increment_car_views(car_id)
        
        car = car_service.get_car_by_id(car_id)
        print("carDetaile in controller", car)
        
        if car:
            # Add consumption and no_of_cylinders to the response
            car['consumption'] = car.get('consumption', '0')
            car['no_of_cylinders'] = car.get('no_of_cylinders', '0')
            
            return jsonify({
                'success': True,
                'data': car
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Car not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/add', methods=['POST'])
@jwt_required()
def add_car():
    """Create a new car listing"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get form data
        data = request.form
        
        # Get car image
        if 'car_image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Car image is required'
            }), 400
        
        car_image = request.files['car_image']
        
        # Save car image
        try:
            image_url = save_file(car_image, 'car_images')
            if not image_url:
                return jsonify({
                    'success': False,
                    'message': 'Invalid file type. Allowed types are: ' + ', '.join(ALLOWED_EXTENSIONS)
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to save car image: {str(e)}'
            }), 400
        
        # Clean and convert numeric fields
        try:
            kilometers = str(data.get('kilometers', '0')).strip().replace('"', '')
            year = str(data.get('year', '0')).strip().replace('"', '')
            number_of_seats = str(data.get('number_of_seats', '0')).strip().replace('"', '')
            number_of_doors = str(data.get('number_of_doors', '0')).strip().replace('"', '')
            engine_cc = str(data.get('engine_cc', '0')).strip().replace('"', '')
            price = str(data.get('price', '0')).strip().replace('"', '')
            consumption = str(data.get('consumption', '0')).strip().replace('"', '')
            no_of_cylinders = str(data.get('no_of_cylinders', '0')).strip().replace('"', '')
            
            # Clean warranty date
            warranty_date = str(data.get('warranty_date', '')).strip().replace('"', '')
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Invalid numeric value: {str(e)}'
            }), 400
        
        # Get draft status
        draft = data.get('draft', 'false').lower() == 'true'
        
        # Always set status to 'unsold' when adding a new car
        status = 'unsold'
        
        # Clean string fields
        string_fields = {
            'ad_title': data.get('ad_title', ''),
            'description': data.get('description', ''),
            'car_information': data.get('car_information', ''),
            'exterior_color': data.get('exterior_color', ''),
            'interior': data.get('interior', ''),
            'trim': data.get('trim', ''),
            'regional_specs': data.get('regional_specs', ''),
            'body_type': data.get('body_type', ''),
            'condition': data.get('condition', '') or data.get('car_condition', ''),
            'badges': data.get('badges', ''),
            'location': data.get('location', ''),
            'accident_history': data.get('accident_history', ''),
            'fuel_type': data.get('fuel_type', ''),
            'transmission_type': data.get('transmission_type', ''),
            'drive_type': data.get('drive_type', ''),
            'make': data.get('make', ''),
            'model': data.get('model', ''),
            'extra_features': data.get('extra_features', ''),
            'payment_option': data.get('payment_option', '')
        }
        
        # Clean each string field
        for field, value in string_fields.items():
            if value is not None:
                string_fields[field] = str(value).strip()
            else:   
                string_fields[field] = ""
        
        # Handle extra_features specifically
        extra_features = string_fields['extra_features']
        if extra_features:
            try:
                # Remove any extra quotes and clean the string
                extra_features = extra_features.replace('\\"', '"').replace('""', '"')
                # If it's already a JSON string, parse and re-stringify to ensure proper format
                if extra_features.startswith('[') and extra_features.endswith(']'):
                    features_list = json.loads(extra_features)
                    extra_features = json.dumps(features_list)
                else:
                    # If it's a comma-separated string, convert to JSON array
                    features_list = [f.strip().strip('"') for f in extra_features.split(',')]
                    extra_features = json.dumps(features_list)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as comma-separated string
                features_list = [f.strip().strip('"') for f in extra_features.split(',')]
                extra_features = json.dumps(features_list)
        else:
            extra_features = '[]'
        
        # Create car listing
        car_id = car_service.create_car(
            user_id=user_id,
            ad_title=string_fields['ad_title'],
            description=string_fields['description'],
            car_information=string_fields['car_information'],
            exterior_color=string_fields['exterior_color'],
            interior=string_fields['interior'],
            trim=string_fields['trim'],
            regional_specs=string_fields['regional_specs'],
            body_type=string_fields['body_type'],
            condition=string_fields['condition'],
            badges=string_fields['badges'],
            kilometers=kilometers,
            location=string_fields['location'],
            year=year,
            warranty_date=warranty_date,
            accident_history=string_fields['accident_history'],
            number_of_seats=number_of_seats,
            number_of_doors=number_of_doors,
            fuel_type=string_fields['fuel_type'],
            transmission_type=string_fields['transmission_type'],
            drive_type=string_fields['drive_type'],
            engine_cc=engine_cc,
            make=string_fields['make'],
            model=string_fields['model'],
            price=price,
            extra_features=extra_features,
            car_image=image_url,
            status=status,
            draft=draft,
            consumption=consumption,
            no_of_cylinders=no_of_cylinders,
            payment_option=string_fields['payment_option']
        )
        
        return jsonify({
            'success': True,
            'car_id': car_id
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/update/<int:car_id>', methods=['PUT'])
@jwt_required()
def update_car(car_id):
    """Update a car listing"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get form data
        data = request.form
        
        # Get car image if provided
        car_image = None
        if 'car_image' in request.files:
            car_image = request.files['car_image']
        
        # Convert numeric fields if provided
        try:
            kilometers = int(data['kilometers']) if 'kilometers' in data else None
            year = int(data['year']) if 'year' in data else None
            number_of_seats = int(data['number_of_seats']) if 'number_of_seats' in data else None
            number_of_doors = int(data['number_of_doors']) if 'number_of_doors' in data else None
            engine_cc = int(data['engine_cc']) if 'engine_cc' in data else None
            price = float(data['price']) if 'price' in data else None
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Invalid numeric value: {str(e)}'  
            }), 400
        
        # Get draft status if provided
        draft = None
        if 'draft' in data:
            draft = data['draft'].lower() == 'true'
        
        # Get condition from either condition or car_condition field
        condition = data.get('condition') or data.get('car_condition')
        
        # Update car listing
        result = car_service.update_car(
            car_id=car_id,
            user_id=user_id,
            ad_title=data.get('ad_title'),
            description=data.get('description'),
            car_information=data.get('car_information'),
            exterior_color=data.get('exterior_color'),
            trim=data.get('trim'),
            regional_specs=data.get('regional_specs'),
            body_type=data.get('body_type'),
            condition=condition,  # Pass the condition parameter
            badges=data.get('badges'),
            kilometers=kilometers,
            location=data.get('location'),
            year=year,
            warranty_date=data.get('warranty_date'),
            accident_history=data.get('accident_history'),
            number_of_seats=number_of_seats,
            number_of_doors=number_of_doors,
            fuel_type=data.get('fuel_type'),
            transmission_type=data.get('transmission_type'),
            drive_type=data.get('drive_type'),
            engine_cc=engine_cc,
            make=data.get('make'),
            model=data.get('model'),
            price=price,
            extra_features=data.get('extra_features'),
            car_image=car_image,
            draft=draft
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/delete/<int:car_id>', methods=['DELETE'])
@jwt_required()
def delete_car(car_id):
    """Delete a car listing"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        # Get car details to check ownership
        car = car_service.get_car_by_id_delete(car_id)
        # print("car_user_id=",car['user_id'])
        if not car:
            return jsonify({
                'status': 'error',
                'message': 'Car not found'
            }), 404
            
        # Check if user owns the car
        
        if car['user_id'] != int(current_user_id):   
         return jsonify({
                'status': 'error',
                'message': 'You are not authorized to delete this car'
         }), 403
            
        # Delete the car
        success, message = car_service.delete_car(car_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
        return jsonify({
            'status': 'success',
            'message': 'Car successfully deleted'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_car: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the car'
        }), 500

@car_bp.route('/recommended', methods=['GET'])
@jwt_required()
def get_recommended_cars():
    """Get recommended car listings based on user preferences"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Get recommended cars
        cars = car_service.get_recommended_cars(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': cars
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/my-listings', methods=['GET'])
@jwt_required()
def get_my_listings():
    """Get car listings for the authenticated user"""
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        filter_param = request.args.get('filter')  # Can be 'approved', 'pending', etc.

        # Get user's car listings from service
        result = car_service.get_user_cars(
            user_id=user_id,
            page=page,
            limit=limit,
            filter=filter_param
        )

        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Failed to fetch user cars'),
                'error': result.get('error')
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500
@car_bp.route('/unfeature/<int:car_id>', methods=['PUT'])
@jwt_required()
def unfeature_car(car_id):
    """Unfeature a car listing"""
    try:
        result = car_service.unfeature_car(car_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Car listing unfeatured successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/makes', methods=['GET'])
def get_makes():
    """Get all car makes with their images"""
    try:
        car_service = CarService()
        makes = car_service.get_all_makes()
        
        return jsonify({
            'success': True,
            'data': makes
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/models', methods=['GET'])
def get_models():
    """Get all models for a specific make"""
    make_name = request.args.get('make_name')
    if not make_name:
        return jsonify({
            'success': False,
            'message': 'make_name parameter is required'
        }), 400
        
    car_service = CarService()
    models = car_service.get_models_by_make(make_name)
    
    return jsonify({
        'success': True,
        'data': models
    })

@car_bp.route('/years', methods=['GET'])
def get_years():
    make_name = request.args.get('make_name')
    model_name = request.args.get('model_name')
    
    if not make_name or not model_name:
        return jsonify({
            'success': False,
            'message': 'Both make_name and model_name parameters are required'
        }), 400
    
    car_service = CarService()
    years = car_service.get_years_by_make_model(make_name, model_name)
    
    return jsonify({
        'success': True,
        'data': years
    })

@car_bp.route('/trims', methods=['GET'])
def get_trims():
    make_name = request.args.get('make_name')
    model_name = request.args.get('model_name')
    #year = request.args.get('year')
    
    if not make_name or not model_name :
        return jsonify({
            'success': False,
            'message': 'make_name, model_name parameters are required'
        }), 400
    
    car_service = CarService()
    trims = car_service.get_trims_by_make_model_year(make_name, model_name)
    
    return jsonify({
        'success': True,
        'data': trims
    })

@car_bp.route('/body-types', methods=['GET'])
def get_body_types():
    """Get all body types"""
    car_service = CarService()
    body_types = car_service.get_all_body_types()
    
    return jsonify({
        'success': True,
        'data': body_types
    })

@car_bp.route('/regions', methods=['GET'])
def get_regions():
    """Get all locations/regions"""
    car_service = CarService()
    locations = car_service.get_all_locations()
    
    return jsonify({
        'success': True,
        'data': locations
    })

@car_bp.route('/colours', methods=['GET'])
def get_colours():
    """Get all colors"""
    car_service = CarService()
    colors = car_service.get_all_colors()
    
    return jsonify({
        'success': True,
        'data': colors
    })

@car_bp.route('/regional-specs', methods=['GET'])
def get_regional_specs():
    """Get all regional specs"""
    specs = car_service.get_regional_specs()
    return jsonify(specs), 200

@car_bp.route('/extra-features', methods=['GET'])
def get_extra_features():
    """Get all extra features"""
    features = car_service.get_extra_features()
    return jsonify({
        'success': True,
        'data': features
    }), 200

@car_bp.route('/interiors', methods=['GET'])
def get_interiors():
    """Get all interiors"""
    interiors = car_service.get_interiors()
    return jsonify({
        'success': True,
        'data': interiors
    }), 200

@car_bp.route('/accident-histories', methods=['GET'])
def get_accident_histories():
    """Get all accident histories"""
    histories = car_service.get_accident_histories()
    return jsonify({
        'success': True,
        'data': histories
    }), 200

@car_bp.route('/car-conditions', methods=['GET'])
def get_car_conditions():
    """Get all car conditions"""
    conditions = car_service.get_car_conditions()
    return jsonify({
        'success': True,
        'data': conditions
    }), 200

@car_bp.route('/badges', methods=['GET'])
def get_badges():
    """Get all badges"""
    badges = car_service.get_badges()
    return jsonify({
        'success': True,
        'data': badges
    }), 200

@car_bp.route('/number-of-seats', methods=['GET'])
def get_number_of_seats():
    """Get all number of seats"""
    seats = car_service.get_number_of_seats()
    return jsonify({
        'success': True,
        'data': seats
    }), 200

@car_bp.route('/number-of-doors', methods=['GET'])
def get_number_of_doors():
    """Get all number of doors"""
    doors = car_service.get_number_of_doors()
    return jsonify(doors), 200

@car_bp.route('/fuel-types', methods=['GET'])
def get_fuel_types():
    """Get all fuel types"""
    fuel_types = car_service.get_fuel_types()
    return jsonify({
        'success': True,
        'data': fuel_types
    }), 200

@car_bp.route('/transmission-types', methods=['GET'])
def get_transmission_types():
    """Get all transmission types"""
    transmission_types = car_service.get_transmission_types()
    return jsonify(transmission_types), 200

@car_bp.route('/drive-types', methods=['GET'])
def get_drive_types():
    """Get all drive types"""
    drive_types = car_service.get_drive_types()
    return jsonify(drive_types), 200

@car_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_cars(user_id):
    """Get user details and their listed cars"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        status = request.args.get('status')
        
        # Get user details and their cars
        result = car_service.get_user_details_with_cars(
            user_id=user_id,
            page=page,
            limit=limit,
            status=status
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/upload-option-details', methods=['GET'])
def get_car_upload_option_details():
    """Get all car upload option details from various tables"""
    try:
        # Get all the required data from service
        result = car_service.get_car_upload_option_details()
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/favorites/<int:car_id>', methods=['POST'])
@jwt_required()
def add_to_favorites(car_id):
    """Add a car to favorites and increment likes"""
    try:
        # Increment likes for the car
        success = car_service.increment_car_likes(car_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Car added to favorites successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add car to favorites'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/draft', methods=['POST'])
@jwt_required()
def create_draft_car():
    """Create a draft car listing"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        
        # Get data from request
        data = request.form.to_dict()
        
        # Handle car image if provided
        car_image = None
        if 'car_image' in request.files:
            file = request.files['car_image']
            if file and file.filename:
                # Save the file and get its path
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads', filename)
                file.save(file_path)
                car_image = f"/static/uploads/{filename}"
        
        # Create car listing as draft
        car_id = car_service.create_car(
            user_id=current_user_id,
            ad_title=data.get('ad_title', ''),
            description=data.get('description', ''),
            car_information=data.get('car_information', ''),
            exterior_color=data.get('exterior_color', ''),
            interior=data.get('interior', ''),
            trim=data.get('trim', ''),
            regional_specs=data.get('regional_specs', ''),
            body_type=data.get('body_type', ''),
            condition=data.get('condition', ''),
            badges=data.get('badges', ''),
            kilometers=data.get('kilometers', ''),
            location=data.get('location', ''),
            year=data.get('year', ''),
            warranty_date=data.get('warranty_date', ''),
            accident_history=data.get('accident_history', ''),
            number_of_seats=data.get('number_of_seats', ''),
            number_of_doors=data.get('number_of_doors', ''),
            fuel_type=data.get('fuel_type', ''),
            transmission_type=data.get('transmission_type', ''),
            drive_type=data.get('drive_type', ''),
            engine_cc=data.get('engine_cc', ''),
            make=data.get('make', ''),
            model=data.get('model', ''),
            price=data.get('price', ''),
            extra_features=data.get('extra_features', ''),
            car_image=car_image,
            status='unsold',
            draft=True,
            consumption=data.get('consumption', '0'),
            no_of_cylinders=data.get('no_of_cylinders', '0'),
            payment_option=data.get('payment_option', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Draft car listing created successfully',
            'car_id': car_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/edit-draft/<int:car_id>', methods=['PUT'])
@jwt_required()
def edit_draft_car(car_id):
    """Edit a draft car listing"""
    try:
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        print(f"Debug - Current User ID from JWT: {current_user_id}, Type: {type(current_user_id)}")
        
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': 'User not authenticated'
            }), 401
        
        # Get data from request
        data = request.form.to_dict()
        
        # First verify if the car exists and is a draft by getting it directly from repository
        car = car_service.car_repository.get_car_by_id(car_id)
        print(f"Debug - Car Data from Repository: {car}")
        
        if not car:
            return jsonify({
                'success': False,
                'message': 'Car not found'
            }), 404
            
        # Check if user owns the car
        car_user_id = str(car.get('user_id', ''))
        current_user_id_str = str(current_user_id)
        
        print(f"Debug - Car User ID: {car_user_id}, Type: {type(car_user_id)}")
        print(f"Debug - Current User ID: {current_user_id_str}, Type: {type(current_user_id_str)}")
        
        # Compare user IDs after ensuring they're both strings
        if car_user_id != current_user_id_str:
            return jsonify({
                'success': False,
                'message': f'You are not authorized to edit this car. Car User ID: {car_user_id}, Your ID: {current_user_id_str}'
            }), 403
            
        # Check if car is a draft
        if not car.get('draft'):
            return jsonify({
                'success': False,
                'message': 'Only draft cars can be edited using this endpoint'
            }), 400
        
        # Handle car image if provided
        car_image = None
        if 'car_image' in request.files:
            file = request.files['car_image']
            if file and file.filename:
                # Save the file and get its path
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads', filename)
                file.save(file_path)
                car_image = f"/static/uploads/{filename}"
        
        # Update car listing with only the provided fields
        result = car_service.update_car(
            car_id=car_id,
            user_id=current_user_id,
            ad_title=data.get('ad_title'),
            description=data.get('description'),
            car_information=data.get('car_information'),
            exterior_color=data.get('exterior_color'),
            interior=data.get('interior'),
            trim=data.get('trim'),
            regional_specs=data.get('regional_specs'),
            body_type=data.get('body_type'),
            condition=data.get('condition'),
            badges=data.get('badges'),
            kilometers=data.get('kilometers'),
            location=data.get('location'),
            year=data.get('year'),
            warranty_date=data.get('warranty_date'),
            accident_history=data.get('accident_history'),
            number_of_seats=data.get('number_of_seats'),
            number_of_doors=data.get('number_of_doors'),
            fuel_type=data.get('fuel_type'),
            transmission_type=data.get('transmission_type'),
            drive_type=data.get('drive_type'),
            engine_cc=data.get('engine_cc'),
            make=data.get('make'),
            model=data.get('model'),
            price=data.get('price'),
            extra_features=data.get('extra_features'),
            car_image=car_image,
            draft=True,  # Keep it as draft
            consumption=data.get('consumption', '0'),
            no_of_cylinders=data.get('no_of_cylinders', '0'),
            payment_option=data.get('payment_option')
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Draft car listing updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error in edit_draft_car: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@car_bp.route('/upload-cars-xlsx', methods=['POST'])
@jwt_required()
def upload_cars_xlsx():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    try:
        # Read Excel file using pandas
        df = pd.read_excel(file)
        car_ids = []
        user_id = get_jwt_identity()  # Get user_id from JWT token
        allowed_status = ['available', 'unsold', 'sold']

        for _, row in df.iterrows():
            status_value = str(row.get('status', '')).strip().lower()
            if status_value not in allowed_status:
                status_value = 'unsold'
            car_id = car_service.create_car(
                user_id=user_id,
                ad_title=row.get('ad_title', ''),
                description=row.get('description', ''),
                car_information=row.get('car_information', ''),
                exterior_color=row.get('exterior_color', ''),
                interior=row.get('interior', ''),
                trim=row.get('trim', ''),
                regional_specs=row.get('regional_specs', ''),
                body_type=row.get('body_type', ''),
                condition=row.get('condition', ''),
                badges=row.get('badges', ''),
                kilometers=row.get('kilometers', ''),
                location=row.get('location', ''),
                year=row.get('year', ''),
                warranty_date=row.get('warranty_date', ''),
                accident_history=row.get('accident_history', ''),
                number_of_seats=row.get('number_of_seats', ''),
                number_of_doors=row.get('number_of_doors', ''),
                fuel_type=row.get('fuel_type', ''),
                transmission_type=row.get('transmission_type', ''),
                drive_type=row.get('drive_type', ''),
                engine_cc=row.get('engine_cc', ''),
                make=row.get('make', ''),
                model=row.get('model', ''),
                price=row.get('price', ''),
                extra_features=row.get('extra_features', ''),
                car_image='',
                consumption=row.get('consumption', ''),
                no_of_cylinders=row.get('no_of_cylinders', ''),
                payment_option=row.get('payment_option', ''),
                draft=(str(row.get('draft', 'false')).lower() in ['true', '1']),
                skip_required_check=True,
                status=status_value
            )
            car_ids.append(car_id)

        return jsonify({'message': 'Cars uploaded successfully', 'success': True}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
