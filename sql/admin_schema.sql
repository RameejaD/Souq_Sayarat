-- Admin schema for Souq Sayarat

-- Admins table
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_super_admin TINYINT(1) NOT NULL DEFAULT 0,
    is_subscription_transaction_manager TINYINT(1) NOT NULL DEFAULT 0,
    is_listing_manager TINYINT(1) NOT NULL DEFAULT 0,
    is_user_manager TINYINT(1) NOT NULL DEFAULT 0,
    is_support_manager TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    needs_password_update TINYINT(1) NOT NULL DEFAULT 1,
    deleted_at DATETIME NULL
);

-- Admin sessions table for tracking login sessions
CREATE TABLE admin_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
);

-- Admin activity log table
CREATE TABLE admin_activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
);

-- Insert default super admin (you should change this password in production)
INSERT INTO admins (
    email, 
    password_hash, 
    is_super_admin, 
    is_subscription_transaction_manager, 
    is_listing_manager, 
    is_user_manager, 
    is_support_manager,
    needs_password_update
) VALUES (
    'superadmin@souqsayarat.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.sJmWrK', -- password: admin123
    1, 1, 1, 1, 1, 0
); 