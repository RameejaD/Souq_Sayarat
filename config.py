import os
from datetime import timedelta

# Use a fixed secret key for development
SECRET_KEY = 'souq-sayarat-secret-key-2024-development'
JWT_SECRET_KEY = SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '12345')
DB_NAME = os.environ.get('DB_NAME', 'souq_sayarat')

# SMS configuration
SMS_API_KEY = os.environ.get('SMS_API_KEY', '')
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'SouqSayarat')

# File upload configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Payment gateway configuration
PAYMENT_GATEWAY_API_KEY = os.environ.get('PAYMENT_GATEWAY_API_KEY', '')
PAYMENT_GATEWAY_SECRET = os.environ.get('PAYMENT_GATEWAY_SECRET', '')

class Config:
    # Flask configuration
    SECRET_KEY = SECRET_KEY
    
    # JWT configuration
    JWT_SECRET_KEY = JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = JWT_ACCESS_TOKEN_EXPIRES
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    # Database configuration
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    DB_NAME = DB_NAME
    
    # File upload configuration
    UPLOAD_FOLDER = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    
    # SMS configuration
    SMS_API_KEY = SMS_API_KEY
    SMS_SENDER_ID = SMS_SENDER_ID
    
    # Payment gateway configuration
    PAYMENT_GATEWAY_API_KEY = PAYMENT_GATEWAY_API_KEY
    PAYMENT_GATEWAY_SECRET = PAYMENT_GATEWAY_SECRET
