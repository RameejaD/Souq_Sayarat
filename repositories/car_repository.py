from utils.db import execute_query, execute_many
from datetime import datetime
import json

class CarRepository:
    def create_car(self, user_id, ad_title, description, car_information, exterior_color, trim, regional_specs,
                  body_type, car_condition, badges, kilometers, location, year, warranty_date,
                  accident_history, number_of_seats, number_of_doors, fuel_type, transmission_type,
                  drive_type, engine_cc, make, model, price, extra_features, car_image, status,
                  approval='pending', draft=False, consumption='0', no_of_cylinders='0', interior='', payment_option=''):
        """Create a new car listing"""
        # Clean and validate status value
        if status:
            status = str(status).strip().lower() 
        
        # Clean and validate approval value
        valid_approvals = ['pending', 'approved', 'rejected']
        if approval:
            approval = str(approval).strip().lower().replace('"', '').replace("'", '')
        if approval not in valid_approvals:
            approval = 'pending'  # Default to pending if invalid approval

        # Format car image path if it exists
        if car_image:
            # Extract filename from path
            filename = car_image.split('/')[-1]
            # Ensure path is in uploads directory
            car_image = f"/static/uploads/{filename}"

        # Clean and format extra_features
        if extra_features:
            if isinstance(extra_features, str):
                # Handle comma-separated string
                if ',' in extra_features:
                    features_list = [feature.strip() for feature in extra_features.split(',')]
                    extra_features = json.dumps(features_list)
                else:
                    # Try to parse as JSON
                    try:
                        parsed_features = json.loads(extra_features)
                        if isinstance(parsed_features, list):
                            extra_features = json.dumps(parsed_features)
                        else:
                            extra_features = json.dumps([parsed_features])
                    except json.JSONDecodeError:
                        # If not valid JSON, wrap in array
                        extra_features = json.dumps([extra_features.strip()])
            elif isinstance(extra_features, list):
                extra_features = json.dumps(extra_features)
            else:
                extra_features = json.dumps([])
        else:
            extra_features = json.dumps([])

        # Convert and clean numeric fields
        # Handle kilometers - set to 0 if empty or None
        if kilometers:
            try:
                kilometers = str(int(float(str(kilometers).strip())))
            except (ValueError, TypeError):
                kilometers = "0"
        else:
            kilometers = "0"  # Set default kilometers to 0 for drafts

        # Handle engine_cc - set to 0 if empty or None
        if engine_cc:
            try:
                engine_cc = str(int(float(str(engine_cc).strip())))
            except (ValueError, TypeError):
                engine_cc = "0"
        else:
            engine_cc = "0"  # Set default engine_cc to 0 for drafts

        # Handle price - set to 0 if empty or None
        if price:
            try:
                price = str(float(str(price).strip()))
            except (ValueError, TypeError):
                price = "0"
        else:
            price = "0"  # Set default price to 0 for drafts

        # Clean string fields
        string_fields = {
            'ad_title': ad_title,
            'description': description,
            'car_information': car_information,
            'exterior_color': exterior_color,
            'interior': interior,
            'trim': trim,
            'regional_specs': regional_specs,
            'body_type': body_type,
            'car_condition': car_condition,
            'badges': badges,
            'location': location,
            'year': year,  # We'll handle this separately
            'warranty_date': warranty_date,  # We'll handle this separately
            'accident_history': accident_history,
            'number_of_seats': number_of_seats,
            'number_of_doors': number_of_doors,
            'fuel_type': fuel_type,
            'transmission_type': transmission_type,
            'drive_type': drive_type,
            'make': make,
            'model': model,
            'consumption': consumption,
            'no_of_cylinders': no_of_cylinders,
            'payment_option': payment_option
        }

        # Clean each string field
        for field, value in string_fields.items():
            if value is not None:
                string_fields[field] = str(value).strip()
            else:
                string_fields[field] = ""

        # Handle year separately - set to 0 if empty or None
        if string_fields['year']:
            try:
                string_fields['year'] = str(int(float(string_fields['year'])))
            except (ValueError, TypeError):
                string_fields['year'] = "0"
        else:
            string_fields['year'] = "0"  # Set default year to 0 for drafts

        # Handle warranty_date separately - set to NULL if empty or None
        if string_fields['warranty_date']:
            try:
                # Validate the date format
                datetime.strptime(string_fields['warranty_date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                string_fields['warranty_date'] = None
        else:
            string_fields['warranty_date'] = None  # Set default warranty_date to NULL for drafts

        # Handle number_of_seats separately - store as string as-is if not empty, else '0'
        if string_fields['number_of_seats']:
            string_fields['number_of_seats'] = str(string_fields['number_of_seats']).strip()
        else:
            string_fields['number_of_seats'] = "0"  # Set default number_of_seats to 0 for drafts

        # Handle number_of_doors separately - store as string as-is if not empty, else '0'
        if string_fields['number_of_doors']:
            string_fields['number_of_doors'] = str(string_fields['number_of_doors']).strip()
        else:
            string_fields['number_of_doors'] = "0"  # Set default number_of_doors to 0 for drafts

        query = """
            INSERT INTO cars (
                id, user_id, make, model, year, price, description, fuel_type, body_type, 
                `condition`, location, status, rejection_reason, is_featured, created_at, 
                updated_at, ad_title, car_information, exterior_color, trim, regional_specs, 
                badges, kilometers, warranty_date, accident_history, number_of_seats, 
                number_of_doors, transmission_type, drive_type, engine_cc, extra_features, 
                car_image, approval, draft, sold_at, consumption, no_of_cylinders, views, 
                likes, interior, payment_option
            )
            VALUES (
                NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s, 0, 0, %s, %s
            )
        """
        
        car_id = execute_query(
            query,
            (user_id, string_fields['make'], string_fields['model'], string_fields['year'],
             price, string_fields['description'], string_fields['fuel_type'], string_fields['body_type'],
             string_fields['car_condition'], string_fields['location'], status, False,  # is_featured defaults to False
             string_fields['ad_title'], string_fields['car_information'], string_fields['exterior_color'],
             string_fields['trim'], string_fields['regional_specs'], string_fields['badges'],
             kilometers, string_fields['warranty_date'], string_fields['accident_history'],
             string_fields['number_of_seats'], string_fields['number_of_doors'],
             string_fields['transmission_type'], string_fields['drive_type'], engine_cc,
             extra_features, car_image, approval, draft,
             string_fields['consumption'], string_fields['no_of_cylinders'],
             string_fields['interior'], string_fields['payment_option']),
            fetch=False
        )
        return car_id
    
    def update_car(self, car_id, make=None, model=None, year=None, price=None, description=None, color=None, kilometers=None, fuel_type=None, transmission=None, body_type=None, condition=None, features=None, location=None, approval=None, ad_title=None, car_information=None, trim=None, regional_specs=None, badges=None, warranty_date=None, accident_history=None, number_of_seats=None, number_of_doors=None, drive_type=None, engine_cc=None, exterior_color=None, interior=None, draft=None, consumption=None, no_of_cylinders=None, payment_option=None, car_image=None):
        """Update a car listing"""
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if ad_title is not None:
            update_fields.append("ad_title = %s")
            params.append(ad_title)
            
        if make is not None:
            update_fields.append("make = %s")
            params.append(make)
        
        if model is not None:
            update_fields.append("model = %s")
            params.append(model)
        
        if year is not None:
            update_fields.append("year = %s")
            params.append(year)
        
        if price is not None:
            update_fields.append("price = %s")
            params.append(price)
        
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
            
        if car_information is not None:
            update_fields.append("car_information = %s")
            params.append(car_information)
            
        if exterior_color is not None:
            update_fields.append("exterior_color = %s")
            params.append(exterior_color)
            
        if interior is not None:
            update_fields.append("interior = %s")
            params.append(interior)
            
        if trim is not None:
            update_fields.append("trim = %s")
            params.append(trim)
            
        if regional_specs is not None:
            update_fields.append("regional_specs = %s")
            params.append(regional_specs)
        
        if kilometers is not None:
            update_fields.append("kilometers = %s")
            params.append(kilometers)
        
        if fuel_type is not None:
            update_fields.append("fuel_type = %s")
            params.append(fuel_type)
        
        if transmission is not None:
            update_fields.append("transmission_type = %s")
            params.append(transmission)
        
        if body_type is not None:
            update_fields.append("body_type = %s")
            params.append(body_type)
        
        if condition is not None:
            update_fields.append("`condition` = %s")
            params.append(condition)
        
        if features is not None:
            update_fields.append("extra_features = %s")
            params.append(features)
        
        if location is not None:
            update_fields.append("location = %s")
            params.append(location)
            
        if approval is not None:
            update_fields.append("approval = %s")
            params.append(approval)
            
        if badges is not None:
            update_fields.append("badges = %s")
            params.append(badges)
            
        if warranty_date is not None:
            update_fields.append("warranty_date = %s")
            params.append(warranty_date)
            
        if accident_history is not None:
            update_fields.append("accident_history = %s")
            params.append(accident_history)
            
        if number_of_seats is not None:
            # Store as string as-is if not empty, else '0'
            value = str(number_of_seats).strip()
            if value:
                update_fields.append("number_of_seats = %s")
                params.append(value)
            else:
                update_fields.append("number_of_seats = %s")
                params.append("0")

        if number_of_doors is not None:
            # Store as string as-is if not empty, else '0'
            value = str(number_of_doors).strip()
            if value:
                update_fields.append("number_of_doors = %s")
                params.append(value)
            else:
                update_fields.append("number_of_doors = %s")
                params.append("0")
            
        if drive_type is not None:
            update_fields.append("drive_type = %s")
            params.append(drive_type)
            
        if engine_cc is not None:
            update_fields.append("engine_cc = %s")
            params.append(engine_cc)
            
        if draft is not None:
            update_fields.append("draft = %s")
            params.append(draft)
            
        if consumption is not None:
            update_fields.append("consumption = %s")
            params.append(consumption)
            
        if no_of_cylinders is not None:
            update_fields.append("no_of_cylinders = %s")
            params.append(no_of_cylinders)
            
        if payment_option is not None:
            update_fields.append("payment_option = %s")
            params.append(payment_option)
            
        if car_image is not None:
            update_fields.append("car_image = %s")
            params.append(car_image)
        
        # Always update the updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if not update_fields:
            return False
        
        query = f"""
            UPDATE cars 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        params.append(car_id)
        
        execute_query(query, tuple(params), fetch=False)
        return True
    
    def update_car_status(self, car_id, status):
        """Update a car's status"""
        # Validate status value
        valid_statuses = ['available', 'sold']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status value. Must be one of: {', '.join(valid_statuses)}")
            
        query = """
            UPDATE cars
            SET status = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (status, datetime.now(), car_id), fetch=False)
    
    def delete_car(self, car_id):
        """Delete a car listing by moving it to deleted_cars table"""
        try:
            # First, get the car details
            car_query = """
                SELECT * FROM cars WHERE id = %s
            """
            car = execute_query(car_query, (car_id,))
            
            if not car:
                return False, "Car not found"
            
            car = car[0]  # Get the first (and should be only) result
            
            # Insert into deleted_cars table
            insert_query = """
                INSERT INTO deleted_cars (
                    id, user_id, make, model, year, price, description, fuel_type, 
                    body_type, car_condition, location, status, rejection_reason, 
                    is_featured, created_at, updated_at, ad_title, car_information, 
                    exterior_color, trim, regional_specs, badges, kilometers, 
                    warranty_date, accident_history, number_of_seats, number_of_doors, 
                    transmission_type, drive_type, engine_cc, extra_features, car_image, 
                    approval, draft, sold_at, consumption, no_of_cylinders, views, likes
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                car['id'], car['user_id'], car['make'], car['model'], car['year'],
                car['price'], car['description'], car['fuel_type'], car['body_type'],
                car['condition'], car['location'], car['status'], car['rejection_reason'],
                car['is_featured'], car['created_at'], car['updated_at'], car['ad_title'],
                car['car_information'], car['exterior_color'], car['trim'],
                car['regional_specs'], car['badges'], car['kilometers'],
                car['warranty_date'], car['accident_history'], car['number_of_seats'],
                car['number_of_doors'], car['transmission_type'], car['drive_type'],
                car['engine_cc'], car['extra_features'], car['car_image'],
                car['approval'], car['draft'], car['sold_at'], car['consumption'],
                car['no_of_cylinders'], car['views'], car['likes']
            )
            
            execute_query(insert_query, params, fetch=False)
            
            # Delete car images
            self.delete_car_images(car_id)
            
            # Delete from favorites
            delete_favorites_query = """
                DELETE FROM favorites WHERE car_id = %s
            """
            execute_query(delete_favorites_query, (car_id,), fetch=False)
            
            # Finally, delete from cars table
            delete_query = """
                DELETE FROM cars WHERE id = %s
            """
            execute_query(delete_query, (car_id,), fetch=False)
            
            return True, "Car successfully deleted"
            
        except Exception as e:
            print(f"Error deleting car: {str(e)}")
            return False, str(e)
    
    def get_car_by_id(self, car_id):
        """Get a car by ID"""
        query = """
            SELECT c.*, 
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url
            FROM cars c
            WHERE c.id = %s
        """
        results = execute_query(query, (car_id,))
        if not results:
            return None
            
        car = results[0]
        
        # Format the image URLs if they exist
        if car.get('car_image'):
            # Extract the filename from the path
            filename = car['car_image'].split('/')[-1]
            # Format the image URL in the required format
            car['car_image'] = f"/static/uploads/{filename}"
            
        if car.get('image_url'):
            # Extract the filename from the path
            filename = car['image_url'].split('/')[-1]
            # Format the image URL in the required format
            car['image_url'] = f"/static/uploads/{filename}"
            
        return car
    
    def get_cars(self, page=1, limit=10, filters=None, user_id=None):
        """Get cars with pagination and filtering"""
        offset = (page - 1) * limit
        filters = filters or {}
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        # Add draft=0 condition
        where_clauses.append("c.draft = 0")
        
        # Add block filter if user_id is provided
        if user_id:
            where_clauses.append("""
                c.user_id NOT IN (
                    SELECT blocked_id 
                    FROM user_blocks 
                    WHERE blocker_id = %s
                )
                AND c.user_id NOT IN (
                    SELECT blocker_id 
                    FROM user_blocks 
                    WHERE blocked_id = %s
                )
            """)
            params.extend([user_id, user_id])
        
        if 'status' in filters:
            where_clauses.append("c.status = %s")
            params.append(filters['status'])
        
        if 'approval' in filters:
            where_clauses.append("c.approval = %s")
            params.append(filters['approval'])
        
        if 'is_featured' in filters:
            where_clauses.append("c.is_featured = %s")
            params.append(filters['is_featured'])
        
        # Construct final query
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get cars with pagination
        query = f"""
            SELECT c.*, u.first_name, u.last_name, u.profile_pic, u.user_type,
                   u.is_dealer, u.company_name
            FROM cars c
            JOIN users u ON c.user_id = u.id
            {where_clause}
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        cars = execute_query(query, params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM cars c
            {where_clause}
        """
        count_result = execute_query(count_query, params[:-2] if params else [])
        total = count_result[0]['total'] if count_result else 0
        
        return cars, total
    
    def search_cars(self, filters, sort_by='created_at', sort_order='desc', page=1, limit=10):
        """Search for cars with advanced filtering"""
        offset = (page - 1) * limit
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        # Handle type='all' case
        if filters.get('type') == 'all':
            # Include all cars regardless of featured/recommended status
            where_clauses.append("approval = 'approved'")
        elif filters.get('type') == 'featured':
            where_clauses.append("is_featured = 1 AND approval = 'approved'")
        elif filters.get('type') == 'recommended':
            # You can implement your recommendation logic here
            # For now, we'll just get approved cars
            where_clauses.append("approval = 'approved'")
        
        if 'status' in filters:
            where_clauses.append("status = %s")
            params.append(filters['status'])
        
        if 'make' in filters and filters['make']:
            where_clauses.append("make = %s")
            params.append(filters['make'])
        
        if 'model' in filters and filters['model']:
            where_clauses.append("model = %s")
            params.append(filters['model'])
        
        if 'year_from' in filters and filters['year_from']:
            where_clauses.append("year >= %s")
            params.append(filters['year_from'])
        
        if 'year_to' in filters and filters['year_to']:
            where_clauses.append("year <= %s")
            params.append(filters['year_to'])
        
        if 'price_from' in filters and filters['price_from']:
            where_clauses.append("price >= %s")
            params.append(filters['price_from'])
        
        if 'price_to' in filters and filters['price_to']:
            where_clauses.append("price <= %s")
            params.append(filters['price_to'])
        
        if 'mileage_from' in filters and filters['mileage_from']:
            where_clauses.append("mileage >= %s")
            params.append(filters['mileage_from'])
        
        if 'mileage_to' in filters and filters['mileage_to']:
            where_clauses.append("mileage <= %s")
            params.append(filters['mileage_to'])
        
        if 'fuel_type' in filters and filters['fuel_type']:
            where_clauses.append("fuel_type = %s")
            params.append(filters['fuel_type'])
        
        if 'transmission' in filters and filters['transmission']:
            where_clauses.append("transmission = %s")
            params.append(filters['transmission'])
        
        if 'body_type' in filters and filters['body_type']:
            where_clauses.append("body_type = %s")
            params.append(filters['body_type'])
        
        if 'condition' in filters and filters['condition']:
            where_clauses.append("`condition` = %s")
            params.append(filters['condition'])
        
        if 'location' in filters and filters['location']:
            where_clauses.append("location = %s")
            params.append(filters['location'])
        
        if 'seller_type' in filters and filters['seller_type']:
            where_clauses.append("(SELECT user_type FROM users WHERE users.id = cars.user_id) = %s")
            params.append(filters['seller_type'])
        
        if 'keyword' in filters and filters['keyword']:
            where_clauses.append("(make LIKE %s OR model LIKE %s OR description LIKE %s)")
            keyword = f"%{filters['keyword']}%"
            params.extend([keyword, keyword, keyword])
        
        # Construct final query
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Validate sort_by and sort_order
        valid_sort_fields = ['created_at', 'price', 'year']
        valid_sort_orders = ['asc', 'desc']
        
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        if sort_order.lower() not in valid_sort_orders:
            sort_order = 'desc'
        
        # Get user_id for favorite check
        user_id = filters.get('user_id')
        if not user_id:
            user_id = 0  # Use 0 for non-authenticated users
        
        print(f"search_cars - user_id: {user_id}, type: {type(user_id)}")
        
        # Get cars with pagination - using the same fields as featured and recommended
        query = f"""
            SELECT 
                c.id,
                c.user_id,
                c.make,
                c.model,
                c.year,
                c.price,
                c.description,
                c.exterior_color as color,
                c.kilometers as mileage,
                c.fuel_type,
                c.transmission_type as transmission,
                c.body_type,
                c.`condition`,
                c.location,
                c.status,
                c.is_featured,
                c.created_at,
                c.updated_at,
                c.car_image,
                c.trim,
                c.regional_specs,
                c.badges,
                c.warranty_date,
                c.accident_history,
                c.number_of_seats,
                c.number_of_doors,
                c.drive_type,
                c.engine_cc,
                c.extra_features,
                (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url,
                CASE WHEN f.id IS NOT NULL THEN TRUE ELSE FALSE END as is_favorite
            FROM cars c
            LEFT JOIN favorites f ON c.id = f.car_id AND f.user_id = %s
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        # Add user_id to params if provided in filters
        user_id = filters.get('user_id')
        if not user_id:
            user_id = 0  # Use 0 for non-authenticated users
        params.insert(0, user_id)  # Insert user_id at the beginning of params
        params.extend([limit, offset])
        
        cars = execute_query(query, params)
        
        # Format image URLs and standardize fields
        for car in cars:
            # Format car_image if it exists
            if car.get('car_image'):
                filename = car['car_image'].split('/')[-1]
                car['car_image'] = f"/static/uploads/{filename}"
            
            # Format image_url if it exists
            if car.get('image_url'):
                filename = car['image_url'].split('/')[-1]
                car['image_url'] = f"/static/uploads/{filename}"
            
            # Convert is_featured to featured integer (0 or 1)
            car['featured'] = 1 if car.pop('is_featured', 0) else 0
            
            # Convert is_favorite to proper boolean
            car['is_favorite'] = bool(car.get('is_favorite', 0))
            
            # Add recommended flag based on type
            car['recommended'] = filters.get('type') == 'recommended'
            
            # Ensure all fields are present with default values if missing
            car.setdefault('id', '')
            car.setdefault('user_id', '')
            car.setdefault('make', '')
            car.setdefault('model', '')
            car.setdefault('year', '')
            car.setdefault('price', 0)
            car.setdefault('description', '')
            car.setdefault('color', '')
            car.setdefault('mileage', 0)
            car.setdefault('fuel_type', '')
            car.setdefault('transmission', '')
            car.setdefault('body_type', '')
            car.setdefault('condition', '')
            car.setdefault('location', '')
            car.setdefault('status', '')
            car.setdefault('created_at', '')
            car.setdefault('updated_at', '')
            car.setdefault('car_image', '')
            car.setdefault('image_url', '')
            car.setdefault('trim', '')
            car.setdefault('regional_specs', '')
            car.setdefault('badges', '')
            car.setdefault('warranty_date', '')
            car.setdefault('accident_history', '')
            car.setdefault('number_of_seats', '')
            car.setdefault('number_of_doors', '')
            car.setdefault('drive_type', '')
            car.setdefault('engine_cc', '')
            car.setdefault('extra_features', '')
            car.setdefault('is_favorite', False)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM cars c
            {where_clause}
        """
        count_result = execute_query(count_query, params[1:-2] if params else [])  # Remove user_id and pagination params
        total = count_result[0]['total'] if count_result else 0
        
        return cars, total
    
    def get_featured_cars(self, user_id=None):
        """Get featured car listings"""
        # Get user_id for favorite check
        if not user_id:
            user_id = 0  # Use 0 for non-authenticated users
            
        print(f"get_featured_cars - user_id: {user_id}, type: {type(user_id)}")
        
        query = """
            SELECT 
                c.id,
                c.user_id,
                c.make,
                c.model,
                c.year,
                c.price,
                c.description,
                c.exterior_color as color,
                c.kilometers as mileage,
                c.fuel_type,
                c.transmission_type as transmission,
                c.body_type,
                c.`condition`,
                c.location,
                c.status,
                c.is_featured,
                c.created_at,
                c.updated_at,
                c.car_image,
                c.trim,
                c.regional_specs,
                c.badges,
                c.warranty_date,
                c.accident_history,
                c.number_of_seats,
                c.number_of_doors,
                c.drive_type,
                c.engine_cc,
                c.extra_features,
                (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url,
                CASE WHEN f.id IS NOT NULL THEN TRUE ELSE FALSE END as is_favorite
            FROM cars c
            LEFT JOIN favorites f ON c.id = f.car_id AND f.user_id = %s
            WHERE c.is_featured = 1 AND c.approval = 'approved'
            ORDER BY c.created_at DESC
        """
        cars = execute_query(query, (user_id,))
        
        # Format image URLs and standardize fields
        for car in cars:
            # Format car_image if it exists
            if car.get('car_image'):
                filename = car['car_image'].split('/')[-1]
                car['car_image'] = f"/static/uploads/{filename}"
            
            # Format image_url if it exists
            if car.get('image_url'):
                filename = car['image_url'].split('/')[-1]
                car['image_url'] = f"/static/uploads/{filename}"
            
            # Convert is_featured to featured integer (0 or 1)
            car['featured'] = 1 if car.pop('is_featured', 0) else 0
            
            # Convert is_favorite to proper boolean
            car['is_favorite'] = bool(car.get('is_favorite', 0))
            
            # Add recommended flag
            car['recommended'] = False
            
            # Ensure all fields are present with default values if missing
            car.setdefault('id', '')
            car.setdefault('user_id', '')
            car.setdefault('make', '')
            car.setdefault('model', '')
            car.setdefault('year', '')
            car.setdefault('price', 0)
            car.setdefault('description', '')
            car.setdefault('color', '')
            car.setdefault('mileage', 0)
            car.setdefault('fuel_type', '')
            car.setdefault('transmission', '')
            car.setdefault('body_type', '')
            car.setdefault('condition', '')
            car.setdefault('location', '')
            car.setdefault('status', '')
            car.setdefault('created_at', '')
            car.setdefault('updated_at', '')
            car.setdefault('car_image', '')
            car.setdefault('image_url', '')
            car.setdefault('trim', '')
            car.setdefault('regional_specs', '')
            car.setdefault('badges', '')
            car.setdefault('warranty_date', '')
            car.setdefault('accident_history', '')
            car.setdefault('number_of_seats', '')
            car.setdefault('number_of_doors', '')
            car.setdefault('drive_type', '')
            car.setdefault('engine_cc', '')
            car.setdefault('extra_features', '')
            car.setdefault('is_favorite', False)
                
        return cars
    
    def get_similar_cars(self, make, model, car_id, limit=5):
        """Get similar cars based on make and model"""
        # Print debug info
        print(f"Getting similar cars for make: {make}, model: {model}, car_id: {car_id}")
        
        # First try to get cars with same make and model
        query = """
            SELECT c.*, 
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url
            FROM cars c
            WHERE c.make = %s 
            AND c.model = %s 
            AND c.id != %s 
            AND c.status = 'available'
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        results = execute_query(query, (make, model, car_id, limit))
        print(f"Found {len(results)} similar cars with same make and model")
        
        # If no results found, get cars with same make
        if not results:
            print("No cars found with same make and model, trying same make only")
            query = """
                SELECT c.*, 
                       (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url
                FROM cars c
                WHERE c.make = %s 
                AND c.id != %s 
                AND c.status = 'available'
                ORDER BY c.created_at DESC
                LIMIT %s
            """
            results = execute_query(query, (make, car_id, limit))
            print(f"Found {len(results)} cars with same make")
        
        # If still no results, get any available cars
        if not results:
            print("No cars found with same make, getting any available cars")
            query = """
                SELECT c.*, 
                       (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url
                FROM cars c
                WHERE c.id != %s 
                AND c.status = 'unsold'
                ORDER BY c.created_at DESC
                LIMIT %s
            """
            results = execute_query(query, (car_id, limit))
            print(f"Found {len(results)} available cars")
        
        # Print the results for debugging
        if results:
            print("Similar cars found:")
            for car in results:
                print(f"- Car ID: {car.get('id')}, Make: {car.get('make')}, Model: {car.get('model')}, Status: {car.get('status')}")
        else:
            print("No similar cars found at all")
        
        return results
    
    def get_recommended_cars(self, makes, models, limit=10):
        """Get recommended cars based on makes and models"""
        where_clauses = []
        params = []
        
        # Only add make/model conditions if we have valid makes and models
        if makes and models and len(makes) > 0 and len(models) > 0:
            for make, model in zip(makes, models):
                if make and model:  # Only add if both make and model are not empty
                    where_clauses.append(f"(c.make = %s AND c.model = %s)")
                    params.extend([make, model])
        
        # If we have no valid conditions, return featured cars instead
        if not where_clauses:
            return self.get_featured_cars()
        
        where_clause = f"WHERE ({' OR '.join(where_clauses)}) AND c.approval = 'approved'"
        
        query = f"""
            SELECT c.id, c.user_id, c.make, c.model, c.year, c.price, c.description, c.exterior_color as color,
                   c.kilometers as mileage, c.fuel_type, c.transmission_type as transmission, c.body_type, c.`condition`,
                   c.location, c.status, c.created_at, c.updated_at, c.car_image,
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url
            FROM cars c
            {where_clause}
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        params.append(limit)
        cars = execute_query(query, params)
        
        # Format car_image URLs and add recommended flag
        for car in cars:
            if car.get('car_image'):
                filename = car['car_image'].split('/')[-1]
                car['car_image'] = f"/static/uploads/{filename}"
            if car.get('image_url'):
                filename = car['image_url'].split('/')[-1]
                car['image_url'] = f"/static/uploads/{filename}"
            # Add recommended flag
            car['recommended'] = True
                
        return cars
    
    def add_car_images(self, car_id, image_urls):
        """Add images to a car listing"""
        # Format image URLs to use uploads directory
        formatted_urls = []
        for url in image_urls:
            if url:
                # Extract filename from path
                filename = url.split('/')[-1]
                # Ensure path is in uploads directory
                formatted_url = f"/static/uploads/{filename}"
                formatted_urls.append(formatted_url)

        query = """
            INSERT INTO car_images (car_id, image_url, created_at)
            VALUES (%s, %s, %s)
        """
        
        params = [(car_id, url, datetime.now()) for url in formatted_urls]
        execute_many(query, params)
    
    def get_car_images(self, car_id):
        """Get images for a car listing"""
        query = """
            SELECT id, car_id, image_url, created_at
            FROM car_images
            WHERE car_id = %s
            ORDER BY id
        """
        return execute_query(query, (car_id,))
    
    def delete_car_images(self, car_id):
        """Delete all images for a car listing"""
        query = """
            DELETE FROM car_images
            WHERE car_id = %s
        """
        execute_query(query, (car_id,), fetch=False)
    
    def get_user_cars_count(self, user_id):
        """Get the count of car listings for a user"""
        query = """
            SELECT COUNT(*) as total
            FROM cars
            WHERE user_id = %s
        """
        result = execute_query(query, (user_id,))
        return result[0]['total'] if result else 0
    
    def get_user_active_cars_count(self, user_id):
        """Get count of user's active car listings"""
        query = """
            SELECT COUNT(*) as count
            FROM cars
            WHERE user_id = %s AND status = 'active'
        """
        results = execute_query(query, (user_id,))
        return results[0]['count'] if results else 0
    
    def get_user_search_history(self, user_id, limit=5):
        """Get a user's search history"""
        query = """
            SELECT search_params
            FROM saved_searches
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        results = execute_query(query, (user_id, limit))
        
        # Parse search_params JSON
        search_history = []
        for result in results:
            if result['search_params']:
                search_history.append(json.loads(result['search_params']))
        
        return search_history
    
    def get_makes(self):
        """Get all car makes"""
        query = """
            SELECT DISTINCT make
            FROM cars
            WHERE approval = 'approved'
            ORDER BY make
        """
        results = execute_query(query)
        return [result['make'] for result in results]
    
    def get_models(self, make):
        """Get models for a specific make"""
        query = """
            SELECT DISTINCT model
            FROM cars
            WHERE make = %s AND approval = 'approved'
            ORDER BY model
        """
        results = execute_query(query, (make,))
        return [result['model'] for result in results]
    
    def get_years(self):
        """Get available years for filtering"""
        query = """
            SELECT DISTINCT year
            FROM cars
            WHERE approval = 'approved'
            ORDER BY year DESC
        """
        results = execute_query(query)
        return [result['year'] for result in results]
    
    def get_fuel_types(self):
        """Get all fuel types"""
        query = """
            SELECT id, fuel_type
            FROM fuel_type
            ORDER BY fuel_type
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'fuel_type': result.get('fuel_type', '')
        } for result in results]
    
    def get_transmissions(self):
        """Get available transmissions for filtering"""
        query = """
            SELECT DISTINCT transmission
            FROM cars
            WHERE transmission IS NOT NULL AND approval = 'approved'
            ORDER BY transmission
        """
        results = execute_query(query)
        return [result['transmission'] for result in results]
    
    def get_body_types(self):
        """Get available body types for filtering"""
        query = """
            SELECT DISTINCT body_type
            FROM cars
            WHERE body_type IS NOT NULL AND approval = 'approved'
            ORDER BY body_type
        """
        results = execute_query(query)
        return [result['body_type'] for result in results]
    
    def get_conditions(self):
        """Get available conditions for filtering"""
        query = """
            SELECT DISTINCT `condition`
            FROM cars
            WHERE `condition` IS NOT NULL AND approval = 'approved'
            ORDER BY `condition`
        """
        results = execute_query(query)
        return [result['condition'] for result in results]
    
    def get_locations(self):
        """Get available locations for filtering"""
        query = """
            SELECT DISTINCT location
            FROM cars
            WHERE location IS NOT NULL AND approval = 'approved'
            ORDER BY location
        """
        results = execute_query(query)
        return [result['location'] for result in results]
    
    def get_cars_count(self, status=None):
        """Get the count of cars"""
        if status:
            query = """
                SELECT COUNT(*) as total
                FROM cars
                WHERE status = %s
            """
            result = execute_query(query, (status,))
        else:
            query = """
                SELECT COUNT(*) as total
                FROM cars
            """
            result = execute_query(query)
        
        return result[0]['total'] if result else 0
    
    def get_recent_cars(self, limit=5):
        """Get recently added cars"""
        query = """
            SELECT id, make, model, year, price, status, created_at
            FROM cars
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (limit,))
    
    def reject_car(self, car_id, reason):
        """Reject a car listing"""
        query = """
            UPDATE cars
            SET approval = 'rejected', rejection_reason = %s, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (reason, datetime.now(), car_id), fetch=False)
    
    def feature_car(self, car_id):
        """Feature a car listing"""
        query = """
            UPDATE cars
            SET is_featured = 1, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), car_id), fetch=False)
    
    def unfeature_car(self, car_id):
        """Unfeature a car listing"""
        query = """
            UPDATE cars
            SET is_featured = 0, updated_at = %s
            WHERE id = %s
        """
        execute_query(query, (datetime.now(), car_id), fetch=False)

    def get_all_makes(self):
        """Get all car makes from the makes table"""
        query = """
            SELECT id, make_name as name, image
            FROM makes
            WHERE image IS NOT NULL
            ORDER BY make_name
        """
        results = execute_query(query)
        # Return image paths using static/uploads/ instead of api/uploads/
        return [{
            'id': str(result.get('id', '')),
            'name': result.get('name', ''),
            'image': result.get('image', '').replace('api/uploads/', 'static/uploads/') if result.get('image') else ''
        } for result in results]

    def get_models_by_make(self, make_name):
        """Get all models for a specific make from the models table"""
        query = """
            SELECT id, make_name, model_name, make_id
            FROM models
            WHERE make_name = %s
            ORDER BY model_name
        """
        results = execute_query(query, (make_name,))
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'make_name': result.get('make_name', ''),
            'model_name': result.get('model_name', ''),
            'make_id': str(result.get('make_id', ''))
        } for result in results]

    def get_years_by_make_model(self, make_name, model_name):
        """Get all years for a specific make and model from the years table"""
        query = """
            SELECT id, year, make_name, model_name
            FROM years
            WHERE make_name = %s AND model_name = %s
            ORDER BY year DESC
        """
        results = execute_query(query, (make_name, model_name))
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'year': str(result.get('year', '')),
            'make_name': result.get('make_name', ''),
            'model_name': result.get('model_name', '')
        } for result in results]

    def get_trims_by_make_model_year(self, make_name, model_name):
        """Get all trims for a specific make, model from the trim table"""
        query = """
            SELECT id, make_name, model_name, trim_name, year
            FROM trim
            WHERE make_name = %s AND model_name = %s 
            ORDER BY trim_name
        """
        results = execute_query(query, (make_name, model_name))
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'make_name': result.get('make_name', ''),
            'model_name': result.get('model_name', ''),
            'trim_name': result.get('trim_name', ''),
            'year': str(result.get('year', ''))
        } for result in results]

    def get_all_body_types(self):
        """Get all body types with their images"""
        query = "SELECT id, body_type, body_type_image FROM body_types ORDER BY body_type"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'body_type': result.get('body_type', ''),
            'body_type_image': result.get('body_type_image', '')
        } for result in results]

    def get_all_locations(self):
        """Get all locations"""
        query = "SELECT id, location FROM locations ORDER BY location"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'location': result.get('location', '')
        } for result in results]

    def get_all_colors(self):
        """Get all colours with their images"""
        query = "SELECT id, colour, colour_image FROM colour ORDER BY colour"
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'colour': result.get('colour', ''),
            'colour_image': result.get('colour_image', '')
        } for result in results]
    
    def get_all_car_conditions(self):
        """Get all car conditions"""
        query = "SELECT id, car_condition FROM car_condition ORDER BY car_condition"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'car_condition': result.get('car_condition', '')
        } for result in results]
    
    def get_all_regional_specs(self):
        """Get all regional specs"""
        query = "SELECT id, regional_spec FROM regional_specs ORDER BY regional_spec"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'regional_spec': result.get('regional_spec', '')
        } for result in results]
    
    def get_all_accident_histories(self):
        """Get all accident histories"""
        query = "SELECT id, accident_history FROM accident_history ORDER BY accident_history"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'accident_history': result.get('accident_history', '')
        } for result in results]
    
    def get_all_number_of_seats(self):
        """Get all number of seats"""
        query = "SELECT id, no_of_seats FROM no_of_seats ORDER BY no_of_seats"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'no_of_seats': result.get('no_of_seats', '')
        } for result in results]
    
    def get_all_number_of_doors(self):
        """Get all number of doors"""
        query = "SELECT id, no_of_doors FROM no_of_doors ORDER BY no_of_doors"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'no_of_doors': result.get('no_of_doors', '')
        } for result in results]
    
    def get_all_number_of_cylinders(self):
        """Get all number of cylinders"""
        query = "SELECT id, no_of_cylinders FROM no_of_cylinders ORDER BY no_of_cylinders"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'no_of_cylinders': result.get('no_of_cylinders', '')
        } for result in results]
    
    def get_all_fuel_types(self):
        """Get all fuel types"""
        query = "SELECT id, fuel_type FROM fuel_type ORDER BY fuel_type"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'fuel_type': result.get('fuel_type', '')
        } for result in results]
    
    def get_all_transmission_types(self):
        """Get all transmission types"""
        query = "SELECT id, transmission_type FROM transmission_type ORDER BY transmission_type"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'transmission_type': result.get('transmission_type', '')
        } for result in results]
    
    def get_all_drive_types(self):
        """Get all drive types"""
        query = "SELECT id, drive_type FROM drive_type ORDER BY drive_type"
        results = execute_query(query)
        return [{'id': row['id'], 'drive_type': row['drive_type'] or ''} for row in results]
    
    def get_all_extra_features(self):
        """Get all extra features"""
        query = "SELECT id, extra_feature FROM extra_features ORDER BY extra_feature"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'extra_feature': result.get('extra_feature', '')
        } for result in results]
    
    def get_all_interiors(self):
        """Get all interiors"""
        query = "SELECT id, interior FROM interiors ORDER BY interior"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'interior': result.get('interior', '')
        } for result in results]

    def get_all_badges(self):
        """Get all badges"""
        query = "SELECT id, badge FROM badges ORDER BY badge"
        results = execute_query(query)
        return [{
            'id': str(result.get('id', '')),
            'badge': result.get('badge', '')
        } for result in results]

    def get_regional_specs(self):
        """Get all regional specs"""
        query = """
            SELECT id, regional, regional_spec
            FROM regional_specs
            ORDER BY regional, regional_spec
        """
        return execute_query(query)

    def get_extra_features(self):
        """Get all extra features"""
        query = """
            SELECT id, extra_feature
            FROM extra_features
            ORDER BY extra_feature
        """
        return execute_query(query)

    def get_interiors(self):
        """Get all interiors"""
        query = """
            SELECT id, interior
            FROM interiors
            ORDER BY interior
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'interior': result.get('interior', '')
        } for result in results]

    def get_accident_histories(self):
        """Get all accident histories"""
        query = """
            SELECT id, accident_history
            FROM accident_history
            ORDER BY accident_history
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'accident_history': result.get('accident_history', '')
        } for result in results]

    def get_car_conditions(self):
        """Get all car conditions"""
        query = """
            SELECT id, car_condition
            FROM car_condition
            ORDER BY car_condition
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'car_condition': result.get('car_condition', '')
        } for result in results]

    def get_badges(self):
        """Get all badges"""
        query = """
            SELECT id, badge
            FROM badges
            ORDER BY badge
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'badge': result.get('badge', '')
        } for result in results]

    def get_number_of_seats(self):
        """Get all number of seats"""
        query = """
            SELECT id, no_of_seats
            FROM no_of_seats
            ORDER BY no_of_seats
        """
        results = execute_query(query)
        # Convert any null values to empty strings
        return [{
            'id': str(result.get('id', '')),
            'no_of_seats': result.get('no_of_seats', '')
        } for result in results]

    def get_number_of_doors(self):
        """Get all number of doors"""
        query = """
            SELECT id, no_of_doors
            FROM no_of_doors
            ORDER BY no_of_doors
        """
        results = execute_query(query)
        return [{'id': row['id'], 'no_of_doors': row['no_of_doors'] or ''} for row in results]

    def get_transmission_types(self):
        """Get all transmission types"""
        query = """
            SELECT id, transmission_type
            FROM transmission_type
            ORDER BY transmission_type
        """
        results = execute_query(query)
        return [{'id': row['id'], 'transmission_type': row['transmission_type'] or ''} for row in results]

    def get_drive_types(self):
        """Get all drive types"""
        query = """
            SELECT id, drive_type
            FROM drive_type
            ORDER BY drive_type
        """
        results = execute_query(query)
        return [{'id': row['id'], 'drive_type': row['drive_type'] or ''} for row in results]

    def get_payment_options(self):
        """Get all payment options"""
        query = """
            SELECT id, payment_option
            FROM payment_options
            ORDER BY payment_option
        """
        results = execute_query(query)
        return [{'id': row['id'], 'payment_option': row['payment_option'] or ''} for row in results]

    def update_car_image_paths(self):
        """Update all car image paths to use uploads directory"""
        # Update car_image column in cars table
        query = """
            UPDATE cars 
            SET car_image = CONCAT('/static/uploads/', SUBSTRING_INDEX(car_image, '/', -1))
            WHERE car_image LIKE '%profile_pics%'
        """
        execute_query(query, fetch=False)
        
        # Update image_url column in car_images table
        query = """
            UPDATE car_images 
            SET image_url = CONCAT('/static/uploads/', SUBSTRING_INDEX(image_url, '/', -1))
            WHERE image_url LIKE '%profile_pics%'
        """
        execute_query(query, fetch=False)

    def get_user_cars(self, user_id, page=1, limit=10):
        """Get user's cars separated by status and draft state"""
        # Get approved/pending cars (unsold and not draft)
        approved_query = """
            SELECT c.*, 
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url,
                   COALESCE(c.likes, 0) as likes
            FROM cars c
            WHERE c.user_id = %s 
            AND c.status = 'unsold'
            AND c.draft = 0
            ORDER BY c.created_at DESC
        """
        approved_cars = execute_query(approved_query, (user_id,))
        
        # Get sold cars (not draft)
        sold_query = """
            SELECT c.*, 
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url,
                   COALESCE(c.likes, 0) as likes
            FROM cars c
            WHERE c.user_id = %s 
            AND c.status = 'sold'
            AND c.draft = 0
            ORDER BY c.created_at DESC
        """
        sold_cars = execute_query(sold_query, (user_id,))
        
        # Get draft cars
        draft_query = """
            SELECT c.*, 
                   (SELECT image_url FROM car_images WHERE car_id = c.id LIMIT 1) AS image_url,
                   COALESCE(c.views, '') as views,
                   COALESCE(c.likes, 0) as likes
            FROM cars c
            WHERE c.user_id = %s 
            AND c.draft = 1
            ORDER BY c.created_at DESC
        """
        draft_cars = execute_query(draft_query, (user_id,))
        
        # Format image URLs and standardize fields for all cars
        def format_car(car):
            if car.get('car_image'):
                filename = car['car_image'].split('/')[-1]
                car['car_image'] = f"static/uploads/{filename}"
            
            if car.get('image_url'):
                filename = car['image_url'].split('/')[-1]
                car['image_url'] = f"static/uploads/{filename}"
            
            # Convert is_featured to featured integer (0 or 1)
            car['is_featured'] = 1 if car.pop('is_featured', 0) else 0
            
            # Ensure all fields are present with default values if missing
            car.setdefault('id', '')
            car.setdefault('user_id', '')
            car.setdefault('make', '')
            car.setdefault('model', '')
            car.setdefault('year', '')
            car.setdefault('price', 0)
            car.setdefault('description', '')
            car.setdefault('color', '')
            car.setdefault('mileage', 0)
            car.setdefault('fuel_type', '')
            car.setdefault('transmission', '')
            car.setdefault('body_type', '')
            car.setdefault('condition', '')
            car.setdefault('location', '')
            car.setdefault('status', '')
            car.setdefault('created_at', '')
            car.setdefault('updated_at', '')
            car.setdefault('car_image', '')
            car.setdefault('image_url', '')
            car.setdefault('trim', '')
            car.setdefault('regional_specs', '')
            car.setdefault('badges', '')
            car.setdefault('warranty_date', '')
            car.setdefault('accident_history', '')
            car.setdefault('number_of_seats', '')
            car.setdefault('number_of_doors', '')
            car.setdefault('drive_type', '')
            car.setdefault('engine_cc', '')
            car.setdefault('extra_features', '')
            car.setdefault('is_favorite', False)
            car.setdefault('likes', 0)
            
            # Ensure views is empty string if null
            if 'views' in car:
                car['views'] = car['views'] if car['views'] is not None else ""
            
            return car
        
        # Format all car arrays
        approved_cars = [format_car(car) for car in approved_cars]
        sold_cars = [format_car(car) for car in sold_cars]
        draft_cars = [format_car(car) for car in draft_cars]
        
        return {
            'approved_pending': approved_cars,
            'sold': sold_cars,
            'draft': draft_cars
        }

    def increment_car_views(self, car_id):
        """Increment the views count for a car"""
        query = """
            UPDATE cars 
            SET views = COALESCE(views, 0) + 1
            WHERE id = %s
        """
        execute_query(query, (car_id,), fetch=False)

    def increment_car_likes(self, car_id):
        """Increment the likes count for a car"""
        query = """
            UPDATE cars 
            SET likes = COALESCE(likes, 0) + 1
            WHERE id = %s
        """
        execute_query(query, (car_id,), fetch=False)

    def decrement_car_likes(self, car_id):
        """Decrement the likes count for a car"""
        query = """
            UPDATE cars 
            SET likes = GREATEST(COALESCE(likes, 0) - 1, 0)
            WHERE id = %s
        """
        execute_query(query, (car_id,), fetch=False)

    def get_user_listing_stats(self, user_id):
        """Get listing stats for a user: total, active, sold, rejected, pending (custom logic)"""
        # Total listings
        total = execute_query("SELECT COUNT(*) as cnt FROM cars WHERE user_id = %s", (user_id,))[0]['cnt']
        # Active listings: status='unsold' and approval='approved'
        active = execute_query("SELECT COUNT(*) as cnt FROM cars WHERE user_id = %s AND status = 'unsold' AND approval = 'approved'", (user_id,))[0]['cnt']
        # Sold listings: status='sold' and approval='approved'
        sold = execute_query("SELECT COUNT(*) as cnt FROM cars WHERE user_id = %s AND status = 'sold' AND approval = 'approved'", (user_id,))[0]['cnt']
        # Rejected listings: status='unsold' and approval='rejected'
        rejected = execute_query("SELECT COUNT(*) as cnt FROM cars WHERE user_id = %s AND status = 'unsold' AND approval = 'rejected'", (user_id,))[0]['cnt']
        # Pending listings: status='unsold' and approval='pending'
        pending = execute_query("SELECT COUNT(*) as cnt FROM cars WHERE user_id = %s AND status = 'unsold' AND approval = 'pending'", (user_id,))[0]['cnt']
        return {
            "total": total,
            "active": active,
            "sold": sold,
            "rejected": rejected,
            "pending": pending
        }
