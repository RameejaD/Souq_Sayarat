from utils.db import execute_query

class AuthRepository:
    def save_otp_request(self, request_id, phone_number, otp, expiry):
        """Save an OTP request"""
        query = """
            INSERT INTO otp_requests (request_id, phone_number, otp, expiry)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(query, (request_id, phone_number, otp, expiry), fetch=False)
    
    def get_otp_request(self, request_id):
        """Get an OTP request by ID"""
        query = """
            SELECT request_id, phone_number, otp, expiry
            FROM otp_requests
            WHERE request_id = %s
        """
        results = execute_query(query, (request_id,))
        return results[0] if results else None
    
    def delete_otp_request(self, request_id):
        """Delete an OTP request"""
        query = """
            DELETE FROM otp_requests
            WHERE request_id = %s
        """
        execute_query(query, (request_id,), fetch=False)
