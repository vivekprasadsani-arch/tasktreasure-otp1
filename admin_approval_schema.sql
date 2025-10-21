-- Admin Approval System Schema
-- Run this in your Supabase SQL Editor

-- Create user access requests table
CREATE TABLE IF NOT EXISTS user_access_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    admin_response_at TIMESTAMP WITH TIME ZONE,
    admin_user_id BIGINT,
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create approved users table
CREATE TABLE IF NOT EXISTS approved_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    approved_by BIGINT NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create access request cooldown table
CREATE TABLE IF NOT EXISTS access_request_cooldown (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    last_request_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cooldown_until TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create admin settings table if not exists
CREATE TABLE IF NOT EXISTS admin_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_access_requests_user_id ON user_access_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_access_requests_status ON user_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_approved_users_user_id ON approved_users(user_id);
CREATE INDEX IF NOT EXISTS idx_approved_users_is_active ON approved_users(is_active);
CREATE INDEX IF NOT EXISTS idx_access_request_cooldown_user_id ON access_request_cooldown(user_id);
CREATE INDEX IF NOT EXISTS idx_access_request_cooldown_until ON access_request_cooldown(cooldown_until);

-- Add RLS policies if needed
-- ALTER TABLE user_access_requests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE approved_users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE access_request_cooldown ENABLE ROW LEVEL SECURITY;

-- Insert default admin user if not exists
INSERT INTO admin_settings (setting_key, setting_value) 
VALUES ('admin_user_id', '7325836764') 
ON CONFLICT (setting_key) DO UPDATE SET 
    setting_value = EXCLUDED.setting_value,
    updated_at = NOW();

-- Sample queries to check data
-- SELECT * FROM user_access_requests ORDER BY requested_at DESC;
-- SELECT * FROM approved_users WHERE is_active = TRUE;
-- SELECT * FROM access_request_cooldown WHERE cooldown_until > NOW();
