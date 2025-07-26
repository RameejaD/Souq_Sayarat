import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from flask import current_app, url_for

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder_name='uploads'):
    """Save uploaded file and return its URL path"""
    if file and file.filename:
        print(f"Processing file: {file.filename}")  # Debug log
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{unique_id}{ext}"
        print(f"Generated unique filename: {unique_filename}")  # Debug log
        
        # Get the appropriate upload directory from Flask config
        if folder_name == 'profile_pics':
            upload_dir = current_app.config['PROFILE_PICS_FOLDER']
        else:
            upload_dir = current_app.config['UPLOAD_FOLDER']
            
        print(f"Upload directory: {upload_dir}")  # Debug log
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        print(f"Saving file to: {file_path}")  # Debug log
        file.save(file_path)
        
        # Return URL path relative to static folder
        url_path = f"/static/{folder_name}/{unique_filename}"
        print(f"Returning URL path: {url_path}")  # Debug log
        
        # Convert to full URL if possible
        try:
            full_url = url_for('static', filename=f"{folder_name}/{unique_filename}", _external=True)
            print(f"Full URL: {full_url}")  # Debug log
            return full_url
        except Exception as e:
            print(f"Error generating full URL: {str(e)}")  # Debug log
            return url_path
    
    print("No file or filename provided")  # Debug log
    return None
