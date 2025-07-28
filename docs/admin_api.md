# Admin API Documentation

## Overview

The Admin API provides authentication and management functionality for the Souq Sayarat application. It supports two types of admins:

1. **Super Admin**: Has full access to all features and can create/manage other admins
2. **Sub Admin**: Has limited access based on assigned permissions

## Authentication

All admin endpoints require authentication using session tokens. The session token should be included in the `Authorization` header.

### Login
```
POST /api/admin/login
```

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "session_token": "your_session_token_here",
  "admin": {
    "id": 1,
    "email": "admin@example.com",
    "is_super_admin": true,
    "is_transactions_manager": true,
    "is_listing_manager": true,
    "is_user_manager": true,
    "is_support_manager": true
  }
}
```

### Logout
```
POST /api/admin/logout
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### Get Profile
```
GET /api/admin/profile
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "admin": {
    "id": 1,
    "email": "admin@example.com",
    "is_super_admin": true,
    "is_transactions_manager": true,
    "is_listing_manager": true,
    "is_user_manager": true,
    "is_support_manager": true
  }
}
```

## Super Admin Endpoints

These endpoints are only accessible by super admins.

### Create Admin
```
POST /api/admin/admins
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Request Body:**
```json
{
  "email": "newadmin@example.com",
  "password": "password123",
  "is_super_admin": false,
  "is_transactions_manager": true,
  "is_listing_manager": true,
  "is_user_manager": false,
  "is_support_manager": false
}
```

**Response:**
```json
{
  "message": "Admin created successfully",
  "admin": {
    "id": 2,
    "email": "newadmin@example.com",
    "is_super_admin": false,
    "is_transactions_manager": true,
    "is_listing_manager": true,
    "is_user_manager": false,
    "is_support_manager": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

### Get All Admins
```
GET /api/admin/admins?page=1&limit=10
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "admins": [
    {
      "id": 1,
      "email": "superadmin@example.com",
      "is_super_admin": true,
      "is_transactions_manager": true,
      "is_listing_manager": true,
      "is_user_manager": true,
      "is_support_manager": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

### Update Admin Permissions
```
PUT /api/admin/admins/{admin_id}
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Request Body:**
```json
{
  "is_super_admin": false,
  "is_transactions_manager": true,
  "is_listing_manager": true,
  "is_user_manager": false,
  "is_support_manager": false
}
```

**Response:**
```json
{
  "message": "Admin permissions updated successfully"
}
```

### Delete Admin
```
DELETE /api/admin/admins/{admin_id}
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "message": "Admin deleted successfully"
}
```

## Admin Dashboard Endpoints

### Get Dashboard
```
GET /api/admin/dashboard
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "counts": {
    "cars": 150,
    "pending_cars": 25,
    "sold_cars": 75,
    "users": 500,
    "dealers": 50
  },
  "recent_activity": {
    "cars": [...],
    "users": [...]
  }
}
```

### Get Pending Cars
```
GET /api/admin/cars/pending?page=1&limit=10
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Approve Car
```
PUT /api/admin/cars/{car_id}/approve
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Reject Car
```
PUT /api/admin/cars/{car_id}/reject
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Request Body:**
```json
{
  "reason": "Car condition does not meet our standards"
}
```

### Get Users
```
GET /api/admin/users?page=1&limit=10&search=john&user_type=individual
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Verify User
```
PUT /api/admin/users/{user_id}/verify
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Ban User
```
PUT /api/admin/users/{user_id}/ban
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Request Body:**
```json
{
  "reason": "Violation of terms of service"
}
```

### Unban User
```
PUT /api/admin/users/{user_id}/unban
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Get Reports
```
GET /api/admin/reports?page=1&limit=10&status=pending
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Resolve Report
```
PUT /api/admin/reports/{report_id}/resolve
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Request Body:**
```json
{
  "resolution": "Issue resolved by contacting both parties"
}
```

### Get Featured Cars
```
GET /api/admin/featured-cars?page=1&limit=10
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Feature Car
```
PUT /api/admin/cars/{car_id}/feature
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

### Unfeature Car
```
PUT /api/admin/cars/{car_id}/unfeature
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

## Activity Log

### Get Activity Log
```
GET /api/admin/activity-log?page=1&limit=10&admin_id=1
```

**Headers:**
```
Authorization: Bearer your_session_token_here
```

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "admin_id": 1,
      "action": "login",
      "description": "Admin logged in from 192.168.1.1",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-01T00:00:00",
      "admin_email": "admin@example.com"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

## Permission Levels

### Super Admin
- Full access to all features
- Can create, update, and delete other admins
- Can manage all system settings

### Sub Admin Permissions
- **Transactions Manager**: Can view and manage payment transactions
- **Listing Manager**: Can approve/reject car listings and manage featured cars
- **User Manager**: Can verify, ban, and manage users
- **Support Manager**: Can handle user reports and support tickets

## Security Features

1. **Session-based Authentication**: Uses secure session tokens with 24-hour expiration
2. **Password Hashing**: All passwords are hashed using bcrypt
3. **Activity Logging**: All admin actions are logged with IP address and user agent
4. **Permission-based Access**: Different admin types have different access levels
5. **Input Validation**: All inputs are validated and sanitized

## Setup Instructions

1. Run the database setup script:
   ```bash
   python scripts/setup_admin.py
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the server:
   ```bash
   python main.py
   ```

4. Access the admin API at: `http://localhost:5000/api/admin` 