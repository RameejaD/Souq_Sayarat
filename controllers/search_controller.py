from flask import Blueprint, request, jsonify, g
from services.search_service import SearchService
from services.user_service import UserService
from decorators.auth import token_required
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

search_bp = Blueprint('search', __name__)
search_service = SearchService()
user_service = UserService()

@search_bp.route('/search', methods=['GET', 'POST'])
def basic_search():
    """Basic search with make, model, body_type, and location"""
    try:
        # Get search type from query params
        search_type = request.args.get('type', 'all')
        
        # Get parameters from JSON body for POST or query params for GET
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json'
                }), 400
            data = request.get_json()
            search_params = {
                'make': data.get('make'),
                'model': data.get('model'),
                'body_type': data.get('body_type'),
                'location': data.get('location'),
                'price_from': data.get('price_from'),
                'price_to': data.get('price_to'),
                'year_from': data.get('year_from'),
                'year_to': data.get('year_to'),
                'mileage_from': data.get('mileage_from'),
                'mileage_to': data.get('mileage_to'),
                'fuel_type': data.get('fuel_type'),
                'transmission_type': data.get('transmission_type'),
                'condition': data.get('condition')
            }
        else:
            search_params = {
                'make': request.args.get('make'),
                'model': request.args.get('model'),
                'body_type': request.args.get('body_type'),
                'location': request.args.get('location'),
                'price_from': request.args.get('price_from', type=float),
                'price_to': request.args.get('price_to', type=float),
                'year_from': request.args.get('year_from', type=int),
                'year_to': request.args.get('year_to', type=int),
                'mileage_from': request.args.get('mileage_from', type=int),
                'mileage_to': request.args.get('mileage_to', type=int),
                'fuel_type': request.args.get('fuel_type'),
                'transmission_type': request.args.get('transmission_type'),
                'condition': request.args.get('condition')
            }
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        # Search cars based on type
        if search_type == 'recommended':
            # Get user ID from JWT token if available
            user_id = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    verify_jwt_in_request()
                    user_id = get_jwt_identity()
                except Exception as e:
                    print(f"Error getting user ID: {str(e)}")
            
            result = search_service.get_recommended_cars(user_id)
        elif search_type == 'featured':
            result = search_service.get_featured_cars()
        else:  # 'all' or any other value
            # Use advanced filter for 'all' type to include all search parameters
            result = search_service.advanced_filter(
                filters=search_params,
                page=request.args.get('page', 1, type=int),
                limit=request.args.get('limit', 10, type=int)
            )
            
            # Save search for authenticated users
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    verify_jwt_in_request()
                    user_id = get_jwt_identity()
                    
                    # Create a name for the saved search
                    make = search_params.get('make', '')
                    model = search_params.get('model', '')
                    name = f"{make} {model}".strip() if make or model else "Saved Search"
                    
                    # Save the search for authenticated user
                    save_result = user_service.save_search(
                        user_id=user_id,
                        search_params=search_params,
                        name=name
                    )
                    print(f"Search saved successfully for user {user_id}: {save_result}")  # Debug log
                except Exception as e:
                    print(f"Error saving search: {str(e)}")  # Debug log
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@search_bp.route('/filter', methods=['GET', 'POST'])
def advanced_filter():
    """Advanced filtering with all parameters"""
    try:
        # Get parameters from JSON body for POST or query params for GET
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json'
                }), 400
            data = request.get_json()
            filters = {
                'price_from': data.get('price_from'),
                'price_to': data.get('price_to'),
                'year_from': data.get('year_from'),
                'year_to': data.get('year_to'),
                'mileage_from': data.get('mileage_from'),
                'mileage_to': data.get('mileage_to'),
                'location': data.get('location'),
                'fuel_type': data.get('fuel_type'),
                'transmission_type': data.get('transmission_type'),
                'condition': data.get('condition')
            }
            page = data.get('page', 1)
            limit = data.get('limit', 10)
        else:
            filters = {
                'price_from': request.args.get('price_from', type=float),
                'price_to': request.args.get('price_to', type=float),
                'year_from': request.args.get('year_from', type=int),
                'year_to': request.args.get('year_to', type=int),
                'mileage_from': request.args.get('mileage_from', type=int),
                'mileage_to': request.args.get('mileage_to', type=int),
                'location': request.args.get('location'),
                'fuel_type': request.args.get('fuel_type'),
                'transmission_type': request.args.get('transmission_type'),
                'condition': request.args.get('condition')
            }
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Apply filters
        result = search_service.advanced_filter(
            filters=filters,
            page=page,
            limit=limit
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

@search_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Get search suggestions based on partial input"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({
                'success': True,
                'data': {
                    'makes': [],
                    'models': [],
                    'locations': []
                }
            }), 200
        
        # Get suggestions
        suggestions = search_service.get_search_suggestions(query)
        
        return jsonify({
            'success': True,
            'data': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@search_bp.route('/makes', methods=['GET'])
def get_makes():
    """Get all car makes"""
    makes = search_service.get_makes()
    return jsonify(makes), 200

@search_bp.route('/models', methods=['GET'])
def get_models():
    """Get models for a specific make"""
    make = request.args.get('make')
    if not make:
        return jsonify({"error": "Missing required parameter: make"}), 400
    
    models = search_service.get_models(make)
    return jsonify(models), 200

@search_bp.route('/years', methods=['GET'])
def get_years():
    """Get available years for filtering"""
    years = search_service.get_years()
    return jsonify(years), 200

@search_bp.route('/fuel-types', methods=['GET'])
def get_fuel_types():
    """Get available fuel types for filtering"""
    fuel_types = search_service.get_fuel_types()
    return jsonify(fuel_types), 200

@search_bp.route('/transmissions', methods=['GET'])
def get_transmissions():
    """Get available transmissions for filtering"""
    transmissions = search_service.get_transmissions()
    return jsonify(transmissions), 200

@search_bp.route('/body-types', methods=['GET'])
def get_body_types():
    """Get available body types for filtering"""
    body_types = search_service.get_body_types()
    return jsonify(body_types), 200

@search_bp.route('/conditions', methods=['GET'])
def get_conditions():
    """Get available conditions for filtering"""
    conditions = search_service.get_conditions()
    return jsonify(conditions), 200

@search_bp.route('/locations', methods=['GET'])
def get_locations():
    """Get available locations for filtering"""
    locations = search_service.get_locations()
    return jsonify(locations), 200
