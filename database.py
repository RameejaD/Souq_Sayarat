import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='souq_sayarat',
            user='root',
            password='Rameeja@234'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise e 