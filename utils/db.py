import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise e

def execute_query(query, params=None, fetch=True):
    """Execute a database query"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Execute the query
        cursor.execute(query, params or ())
        
        if fetch:
            # Fetch results
            results = cursor.fetchall()
            return results
        else:
            # Commit changes for non-fetch queries
            connection.commit()
            return cursor.lastrowid
            
    except Error as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def execute_many(query, params_list):
    """Execute a query with multiple parameter sets"""
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.executemany(query, params_list)
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
