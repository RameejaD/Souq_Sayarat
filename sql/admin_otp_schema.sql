-- Create admin_otp table for password reset functionality
CREATE TABLE IF NOT EXISTS `admin_otp` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `email` varchar(255) NOT NULL,
    `otp` varchar(10) NOT NULL,
    `expires_at` datetime NOT NULL,
    `verified` tinyint(1) DEFAULT 0,
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_email` (`email`),
    KEY `idx_otp` (`otp`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 