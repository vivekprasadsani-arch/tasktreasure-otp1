-- User Approval System Tables
-- Add these tables to your existing Supabase database

-- Table for user approval requests
CREATE TABLE IF NOT EXISTS user_approval_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by BIGINT,
    rejection_reason TEXT,
    next_request_allowed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for approved users
CREATE TABLE IF NOT EXISTS approved_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_approval_requests_user_id ON user_approval_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_approval_requests_status ON user_approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_user_approval_requests_next_allowed ON user_approval_requests(next_request_allowed_at);
CREATE INDEX IF NOT EXISTS idx_approved_users_user_id ON approved_users(user_id);
CREATE INDEX IF NOT EXISTS idx_approved_users_active ON approved_users(is_active);

-- Add comments
COMMENT ON TABLE user_approval_requests IS 'Tracks user approval requests with 3-hour cooldown';
COMMENT ON TABLE approved_users IS 'List of users approved by admin to use the bot';

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_user_approval_requests_updated_at BEFORE UPDATE ON user_approval_requests 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_approved_users_updated_at BEFORE UPDATE ON approved_users 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Sample queries:
-- Check if user is approved: SELECT * FROM approved_users WHERE user_id = 123456 AND is_active = TRUE;
-- Get pending requests: SELECT * FROM user_approval_requests WHERE status = 'pending' ORDER BY requested_at;
-- Check cooldown: SELECT * FROM user_approval_requests WHERE user_id = 123456 AND next_request_allowed_at > NOW();
