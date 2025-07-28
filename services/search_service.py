from repositories.search_repository import SearchRepository
from repositories.car_repository import CarRepository

class SearchService:
    def __init__(self):
        self.search_repository = SearchRepository()
        self.car_repository = CarRepository()

    def basic_search(self, search_params):
        """Basic search with make, model, body_type, and location"""
        # Clean parameters
        cleaned_params = {}
        for key, value in search_params.items():
            if value is not None:
                if isinstance(value, str) and value.strip():
                    cleaned_params[key] = value.strip()
                elif not isinstance(value, str):
                    cleaned_params[key] = str(value).strip()
        
        # Get results with default pagination
        result = self.search_repository.basic_search(
            search_params=cleaned_params,
            page=1,
            limit=10
        )
        
        return result

    def get_recommended_cars(self, user_id):
        """Get recommended cars based on user preferences"""
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
        cars = self.car_repository.get_recommended_cars(makes, models, limit=10)
        
        return {
            'cars': cars,
            'pagination': {
                'page': 1,
                'limit': 10,
                'total': len(cars),
                'total_pages': 1
            }
        }

    def get_featured_cars(self):
        """Get featured car listings"""
        cars = self.car_repository.get_featured_cars(limit=10)
        return {
            'cars': cars,
            'pagination': {
                'page': 1,
                'limit': 10,
                'total': len(cars),
                'total_pages': 1
            }
        }

    def advanced_filter(self, filters, page=1, limit=10):
        """Advanced filtering with all parameters"""
        # Clean filters
        cleaned_filters = {}
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str) and value.strip():
                    cleaned_filters[key] = value.strip()
                elif not isinstance(value, str):
                    cleaned_filters[key] = value
        
        # Get filtered results
        result = self.search_repository.advanced_filter(
            filters=cleaned_filters,
            page=page,
            limit=limit
        )
        
        return result

    def get_search_suggestions(self, query):
        """Get search suggestions based on partial input"""
        if not query or len(query.strip()) < 2:
            return {
                'makes': [],
                'models': [],
                'locations': []
            }
        
        return self.search_repository.get_search_suggestions(query.strip())

    def get_makes(self):
        """Get all car makes"""
        return self.search_repository.get_makes()

    def get_models(self, make):
        """Get models for a specific make"""
        return self.search_repository.get_models(make)

    def get_years(self):
        """Get available years for filtering"""
        return self.search_repository.get_years()

    def get_fuel_types(self):
        """Get available fuel types for filtering"""
        return self.search_repository.get_fuel_types()

    def get_transmissions(self):
        """Get available transmissions for filtering"""
        return self.search_repository.get_transmissions()

    def get_body_types(self):
        """Get available body types for filtering"""
        return self.search_repository.get_body_types()

    def get_conditions(self):
        """Get available conditions for filtering"""
        return self.search_repository.get_conditions()

    def get_locations(self):
        """Get available locations for filtering"""
        return self.search_repository.get_locations()
