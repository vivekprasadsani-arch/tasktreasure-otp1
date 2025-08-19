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
VALUES ('admin_user_id', '5742928021') 
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

-- Sample queries:
-- Get user OTP stats: SELECT * FROM user_otp_stats WHERE user_id = 123456;
-- Get recent OTPs: SELECT * FROM otp_history WHERE user_id = 123456 ORDER BY received_at DESC LIMIT 10;
-- Get admin setting: SELECT setting_value FROM admin_settings WHERE setting_key = 'admin_user_id';
