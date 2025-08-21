-- User Approval System for TaskTreasure OTP Bot
-- Run this in your Supabase SQL Editor

-- Create user_approvals table for tracking access requests
CREATE TABLE IF NOT EXISTS user_approvals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE NULL,
    approved_by BIGINT NULL,
    rejection_reason TEXT NULL,
    last_request_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_approvals_user_id ON user_approvals(user_id);
CREATE INDEX IF NOT EXISTS idx_user_approvals_status ON user_approvals(status);
CREATE INDEX IF NOT EXISTS idx_user_approvals_requested_at ON user_approvals(requested_at);

-- Add unique constraint to prevent duplicate entries
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_approvals_user_id_unique ON user_approvals(user_id);

-- Add comments
COMMENT ON TABLE user_approvals IS 'Tracks user access requests and approval status for bot access';
COMMENT ON COLUMN user_approvals.status IS 'pending: awaiting approval, approved: can use bot, rejected: access denied';
COMMENT ON COLUMN user_approvals.last_request_at IS 'Last time user requested access (for 3-hour cooldown)';

-- Create function to update last_request_at on status change to pending
CREATE OR REPLACE FUNCTION update_last_request_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'pending' AND OLD.status != 'pending' THEN
        NEW.last_request_at = NOW();
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER trigger_update_user_approvals_timestamp
    BEFORE UPDATE ON user_approvals
    FOR EACH ROW
    EXECUTE FUNCTION update_last_request_at();

-- Sample queries:
-- Check if user can request access (3-hour cooldown): 
-- SELECT * FROM user_approvals WHERE user_id = 123456 AND last_request_at > NOW() - INTERVAL '3 hours' AND status = 'pending';

-- Get pending approvals for admin:
-- SELECT * FROM user_approvals WHERE status = 'pending' ORDER BY requested_at ASC;

-- Check if user is approved:
-- SELECT * FROM user_approvals WHERE user_id = 123456 AND status = 'approved';
