from flask import jsonify

def handle_error(e):
    """Global error handler for the application"""
    # Log the error here
    print(f"Error: {str(e)}")
    
    # Return a JSON response
    response = {
        "error": True,
        "message": str(e)
    }
    
    # Determine status code based on error type
    if hasattr(e, 'code'):
        status_code = e.code
    else:
        status_code = 500
        
    return jsonify(response), status_code
