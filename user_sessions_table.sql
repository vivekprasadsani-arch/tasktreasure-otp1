-- Create user_sessions table for Telegram Number Bot
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    country VARCHAR(50) NOT NULL,
    number VARCHAR(20) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL,
    waiting_for_otp BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_number ON user_sessions(number);
CREATE INDEX IF NOT EXISTS idx_user_sessions_country ON user_sessions(country);

-- Add comment
COMMENT ON TABLE user_sessions IS 'Stores user sessions for Telegram Number Bot - tracks assigned numbers and OTP waiting status';

-- Sample query to view all active sessions
-- SELECT * FROM user_sessions WHERE waiting_for_otp = TRUE ORDER BY assigned_at DESC;
