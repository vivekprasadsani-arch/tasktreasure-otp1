-- Create OTP history table for tracking user OTP statistics
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS otp_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    number VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL,
    service VARCHAR(100) NOT NULL,
    otp_code VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_otp_history_user_id ON otp_history(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_history_number ON otp_history(number);
CREATE INDEX IF NOT EXISTS idx_otp_history_received_at ON otp_history(received_at);

-- Create admin_settings table for admin configurations
CREATE TABLE IF NOT EXISTS admin_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default admin user (change this ID to your actual Telegram user ID)
INSERT INTO admin_settings (setting_key, setting_value) 
VALUES ('admin_user_id', '7325836764') 
ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;

-- Create view for user OTP statistics
CREATE OR REPLACE VIEW user_otp_stats AS
SELECT 
    user_id,
    COUNT(*) as total_otps,
    COUNT(DISTINCT service) as unique_services,
    COUNT(DISTINCT country) as unique_countries,
    MAX(received_at) as last_otp_at,
    MIN(received_at) as first_otp_at
FROM otp_history 
GROUP BY user_id;

-- Add comments
COMMENT ON TABLE otp_history IS 'Stores complete OTP history for each user';
COMMENT ON TABLE admin_settings IS 'Stores admin configuration settings';
COMMENT ON VIEW user_otp_stats IS 'Provides aggregated OTP statistics per user';

-- Create number_assignments table for concurrent assignment tracking
CREATE TABLE IF NOT EXISTS number_assignments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    number VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for number assignments
CREATE INDEX IF NOT EXISTS idx_number_assignments_user_id ON number_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_number_assignments_number ON number_assignments(number);
CREATE INDEX IF NOT EXISTS idx_number_assignments_active ON number_assignments(is_active, expires_at);

-- Create otp_cooldown table for 3-day cooldown tracking
CREATE TABLE IF NOT EXISTS otp_cooldown (
    id SERIAL PRIMARY KEY,
    number VARCHAR(20) NOT NULL,
    last_otp_at TIMESTAMP WITH TIME ZONE NOT NULL,
    cooldown_until TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '3 days'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for OTP cooldown
CREATE INDEX IF NOT EXISTS idx_otp_cooldown_number ON otp_cooldown(number);
CREATE INDEX IF NOT EXISTS idx_otp_cooldown_until ON otp_cooldown(cooldown_until);

-- Add comments for new tables
COMMENT ON TABLE number_assignments IS 'Tracks active number assignments to prevent concurrent conflicts';
COMMENT ON TABLE otp_cooldown IS 'Enforces 3-day cooldown period for numbers that received OTP';

-- Sample queries:
-- Get user OTP stats: SELECT * FROM user_otp_stats WHERE user_id = 123456;
-- Get recent OTPs: SELECT * FROM otp_history WHERE user_id = 123456 ORDER BY received_at DESC LIMIT 10;
-- Get admin setting: SELECT setting_value FROM admin_settings WHERE setting_key = 'admin_user_id';
-- Check if number is in cooldown: SELECT * FROM otp_cooldown WHERE number = '+1234567890' AND cooldown_until > NOW();
-- Get active assignments: SELECT * FROM number_assignments WHERE is_active = TRUE AND expires_at > NOW();
