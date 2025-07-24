import requests
from config import SMS_API_KEY, SMS_SENDER_ID

def send_otp(phone_number, otp):
    """Send OTP via SMS"""
    # Print OTP in terminal
    print(f"Your OTP is: {otp}")
    
    # This is a placeholder. Replace with actual SMS gateway implementation
    url = "https://api.smsgateway.com/send"
    payload = {
        "api_key": SMS_API_KEY,
        "sender_id": SMS_SENDER_ID,
        "phone": phone_number,
        "message": f"Your Souq Sayarat verification code is: {otp}"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"SMS sending error: {str(e)}")
        return False
