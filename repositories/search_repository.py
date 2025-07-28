from database import get_db_connection

class SearchRepository:
    def basic_search(self, search_params, page=1, limit=10):
        """Basic search with make, model, body_type, and location"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Base query
            base_query = """
                SELECT 
                    c.id,
                    c.ad_title,
                    c.make,
                    c.model,
                    c.year,
                    c.price,
                    c.kilometers,
                    c.fuel_type,
                    c.transmission_type,
                    c.body_type,
                    c.`condition`,
                    c.location,
                    c.car_image,
                    c.created_at,
                    u.id as seller_id,
                    CONCAT(u.first_name, ' ', u.last_name) as seller_name,
                    u.phone_number as seller_phone
                FROM cars c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.status = 'unsold'
            """
            params = []
            
            # Add conditions based on search parameters
            # Only add conditions for non-empty parameters
            if search_params.get('make'):
                base_query += " AND c.make = %s"
                params.append(search_params['make'].strip())
            
            if search_params.get('model'):
                base_query += " AND c.model = %s"
                params.append(search_params['model'].strip())
            
            if search_params.get('body_type'):
                base_query += " AND c.body_type = %s"
                params.append(search_params['body_type'].strip())
            
            if search_params.get('location'):
                base_query += " AND c.location = %s"
                params.append(search_params['location'].strip())
            
            # If no search parameters are provided, return empty result
            if not params:
                return {
                    'cars': [],
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': 0,
                        'total_pages': 0
                    }
                }
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as count_table"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Add pagination to the main query
            base_query += " ORDER BY c.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])
            
            # Execute main query
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # Calculate pagination info
            total_pages = (total + limit - 1) // limit
            
            return {
                'cars': results,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': total_pages
                }
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def advanced_filter(self, filters, page=1, limit=10):
        """Advanced filtering with all parameters"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Base query
            base_query = """
                SELECT 
                    c.id,
                    c.ad_title,
                    c.make,
                    c.model,
                    c.year,
                    c.price,
                    c.kilometers,
                    c.fuel_type,
                    c.transmission_type,
                    c.body_type,
                    c.`condition`,
                    c.location,
                    c.car_image,
                    c.created_at,
                    u.id as seller_id,
                    CONCAT(u.first_name, ' ', u.last_name) as seller_name,
                    u.phone_number as seller_phone
                FROM cars c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.status = 'unsold'
            """
            params = []
            
            # Add conditions based on filters
            if filters.get('make'):
                base_query += " AND c.make = %s"
                params.append(filters['make'].strip())
            
            if filters.get('model'):
                base_query += " AND c.model = %s"
                params.append(filters['model'].strip())
            
            if filters.get('body_type'):
                base_query += " AND c.body_type = %s"
                params.append(filters['body_type'].strip())
            
            if filters.get('location'):
                base_query += " AND c.location = %s"
                params.append(filters['location'].strip())
            
            if filters.get('price_from'):
                base_query += " AND c.price >= %s"
                params.append(float(filters['price_from']))
            
            if filters.get('price_to'):
                base_query += " AND c.price <= %s"
                params.append(float(filters['price_to']))
            
            if filters.get('year_from'):
                base_query += " AND c.year >= %s"
                params.append(int(filters['year_from']))
            
            if filters.get('year_to'):
                base_query += " AND c.year <= %s"
                params.append(int(filters['year_to']))
            
            if filters.get('mileage_from'):
                base_query += " AND c.kilometers >= %s"
                params.append(float(filters['mileage_from']))
            
            if filters.get('mileage_to'):
                base_query += " AND c.kilometers <= %s"
                params.append(float(filters['mileage_to']))
            
            if filters.get('fuel_type'):
                base_query += " AND c.fuel_type = %s"
                params.append(filters['fuel_type'].strip())
            
            if filters.get('transmission_type'):
                base_query += " AND c.transmission_type = %s"
                params.append(filters['transmission_type'].strip())
            
            if filters.get('condition'):
                base_query += " AND c.condition = %s"
                params.append(filters['condition'].strip())
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as count_table"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Add pagination to the main query
            base_query += " ORDER BY c.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])
            
            # Execute main query
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # Calculate pagination info
            total_pages = (total + limit - 1) // limit
            
            return {
                'cars': results,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': total_pages
                }
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_search_suggestions(self, query):
        """Get search suggestions based on partial input"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get makes
            cursor.execute("""
                SELECT DISTINCT make 
                FROM cars 
                WHERE make LIKE %s 
                LIMIT 5
            """, [f"%{query}%"])
            makes = [row['make'] for row in cursor.fetchall()]
            
            # Get models
            cursor.execute("""
                SELECT DISTINCT model 
                FROM cars 
                WHERE model LIKE %s 
                LIMIT 5
            """, [f"%{query}%"])
            models = [row['model'] for row in cursor.fetchall()]
            
            # Get locations
            cursor.execute("""
                SELECT DISTINCT location 
                FROM cars 
                WHERE location LIKE %s 
                LIMIT 5
            """, [f"%{query}%"])
            locations = [row['location'] for row in cursor.fetchall()]
            
            return {
                'makes': makes,
                'models': models,
                'locations': locations
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_makes(self):
        """Get all car makes"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT DISTINCT make FROM cars ORDER BY make")
            return [row['make'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_models(self, make):
        """Get models for a specific make"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT model 
                FROM cars 
                WHERE make = %s 
                ORDER BY model
            """, [make])
            return [row['model'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_years(self):
        """Get available years for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT year 
                FROM cars 
                ORDER BY year DESC
            """)
            return [row['year'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_fuel_types(self):
        """Get available fuel types for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT fuel_type 
                FROM cars 
                ORDER BY fuel_type
            """)
            return [row['fuel_type'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_transmissions(self):
        """Get available transmissions for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT transmission_type 
                FROM cars 
                ORDER BY transmission_type
            """)
            return [row['transmission_type'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_body_types(self):
        """Get available body types for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT body_type 
                FROM cars 
                ORDER BY body_type
            """)
            return [row['body_type'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_conditions(self):
        """Get available conditions for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT `condition` 
                FROM cars 
                ORDER BY `condition`
            """)
            return [row['condition'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_locations(self):
        """Get available locations for filtering"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT location 
                FROM cars 
                ORDER BY location
            """)
            return [row['location'] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close() 