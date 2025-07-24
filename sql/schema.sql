-- Database schema for Souq Sayarat

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_image VARCHAR(255),
    whatsapp VARCHAR(20),
    location VARCHAR(100),
    user_type ENUM('individual', 'dealer', 'admin') NOT NULL DEFAULT 'individual',
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    is_banned BOOLEAN NOT NULL DEFAULT 0,
    ban_reason TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME
);

-- OTP requests table
CREATE TABLE otp_requests (
    request_id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    expiry DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Cars table
CREATE TABLE cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ad_title VARCHAR(255) NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT NOT NULL,
    car_information TEXT,
    exterior_color VARCHAR(50),
    trim VARCHAR(50),
    regional_specs VARCHAR(50),
    kilometers DECIMAL(10, 2),
    fuel_type VARCHAR(50),
    transmission_type VARCHAR(50),
    body_type VARCHAR(50),
    `condition` VARCHAR(50),
    badges VARCHAR(50),
    warranty_date DATE,
    accident_history TEXT,
    number_of_seats INT,
    number_of_doors INT,
    drive_type VARCHAR(50),
    engine_cc INT,
    extra_features JSON,
    location VARCHAR(100),
    status ENUM('available', 'sold') NOT NULL DEFAULT 'available',
    approval ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    rejection_reason TEXT,
    is_featured BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Car images table
CREATE TABLE car_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

-- Favorites table
CREATE TABLE favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    car_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY (user_id, car_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

-- Saved searches table
CREATE TABLE saved_searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    search_params JSON NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Conversations table
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    car_id INT NOT NULL,
    last_message TEXT,
    last_message_sender_id INT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Blocked users table
CREATE TABLE blocked_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    blocked_user_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY (user_id, blocked_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subscription packages table
CREATE TABLE subscription_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    duration_days INT NOT NULL,
    listing_limit INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    package_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES subscription_packages(id)
);

-- Payment methods table
CREATE TABLE payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Payments table
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    checkout_id VARCHAR(36) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    description TEXT,
    payment_method VARCHAR(50) NOT NULL,
    status ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    metadata JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User reports table
CREATE TABLE user_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    reported_user_id INT NOT NULL,
    reason VARCHAR(100) NOT NULL,
    description TEXT,
    status ENUM('pending', 'resolved') NOT NULL DEFAULT 'pending',
    resolution TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Makes table
CREATE TABLE makes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    make_name VARCHAR(50) NOT NULL UNIQUE,
    image VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Models table
CREATE TABLE models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    make_id INT NOT NULL,
    make_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (make_id) REFERENCES makes(id) ON DELETE CASCADE,
    UNIQUE KEY (make_name, model_name)
);

-- Years table
CREATE TABLE years (
    id INT AUTO_INCREMENT PRIMARY KEY,
    make_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    UNIQUE KEY (make_name, model_name, year)
);

-- Locations table
CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(100) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Colours table
CREATE TABLE colour (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colour VARCHAR(50) NOT NULL UNIQUE,
    colour_image VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Insert default subscription packages
INSERT INTO subscription_packages (name, description, price, currency, duration_days, listing_limit, is_active, created_at)
VALUES
('Free', 'Free tier with limited features', 0.00, 'USD', 0, 1, 1, NOW()),
('Basic', 'Basic package for individual sellers', 9.99, 'USD', 30, 5, 1, NOW()),
('Premium', 'Premium package for individual sellers', 19.99, 'USD', 30, 15, 1, NOW()),
('Dealer', 'Package for car dealers', 49.99, 'USD', 30, 50, 1, NOW());

-- Insert default payment methods
INSERT INTO payment_methods (name, code, description, is_active, created_at)
VALUES
('Credit Card', 'card', 'Pay with credit or debit card', 1, NOW()),
('FIB', 'fib', 'Pay with FIB', 1, NOW()),
('FastPay', 'fastpay', 'Pay with FastPay', 1, NOW()),
('AsiaPay', 'asiapay', 'Pay with AsiaPay', 1, NOW()),
('ZainCash', 'zaincash', 'Pay with ZainCash', 1, NOW());

-- Insert admin user
INSERT INTO users (phone_number, first_name, last_name, password, user_type, is_verified, created_at)
VALUES
('9647700000000', 'Admin', 'User', '$2b$12$1oE8Xz3/c8K9FhI3Vd5tB.5Q.XLZFjqdwrNJwjwQNLQJXnT.Qvz3O', 'admin', 1, NOW());
-- Password: admin123

-- Insert some sample data for testing
INSERT INTO makes (make_name, image) VALUES
('Toyota', '/static/uploads/toyota.png'),
('Ferrari', '/static/uploads/ferrari.png'),
('BMW', '/static/uploads/bmw.png'),
('Mercedes', '/static/uploads/mercedes.png'),
('Audi', '/static/uploads/audi.png');

INSERT INTO models (make_id, make_name, model_name) VALUES
(1, 'Toyota', 'Camry'),
(1, 'Toyota', 'Corolla'),
(1, 'Toyota', 'RAV4'),
(2, 'Ferrari', 'F8'),
(2, 'Ferrari', 'SF90'),
(2, 'Ferrari', '296'),
(3, 'BMW', '3 Series'),
(3, 'BMW', '5 Series'),
(3, 'BMW', 'X5'),
(4, 'Mercedes', 'C-Class'),
(4, 'Mercedes', 'E-Class'),
(4, 'Mercedes', 'S-Class'),
(5, 'Audi', 'A4'),
(5, 'Audi', 'A6'),
(5, 'Audi', 'Q5');

INSERT INTO years (make_name, model_name, year) VALUES
('Toyota', 'Camry', 2020),
('Toyota', 'Camry', 2021),
('Toyota', 'Camry', 2022),
('Toyota', 'Camry', 2023),
('Ferrari', 'F8', 2020),
('Ferrari', 'F8', 2021),
('Ferrari', 'F8', 2022),
('Ferrari', 'F8', 2023);

INSERT INTO locations (location) VALUES
('Baghdad'),
('Basra'),
('Erbil'),
('Mosul'),
('Najaf'),
('Sulaymaniyah');

INSERT INTO colour (colour, colour_image) VALUES
('Black', '/static/uploads/black.png'),
('White', '/static/uploads/white.png'),
('Silver', '/static/uploads/silver.png'),
('Red', '/static/uploads/red.png'),
('Blue', '/static/uploads/blue.png');
