-- SQL script to create the processed_messages table in NEW Supabase Database
-- Project URL: https://wddcrtrgirhcemmobgcc.supabase.co
-- Run this in the Supabase SQL Editor

CREATE TABLE IF NOT EXISTS processed_messages (
    id SERIAL PRIMARY KEY,
    hash VARCHAR(64) UNIQUE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_processed_messages_hash ON processed_messages(hash);
CREATE INDEX IF NOT EXISTS idx_processed_messages_processed_at ON processed_messages(processed_at);

-- Add RLS (Row Level Security) policy if needed
-- ALTER TABLE processed_messages ENABLE ROW LEVEL SECURITY;

-- Grant permissions (adjust as needed for your Supabase setup)
-- Note: The anon role should have INSERT and SELECT permissions for this table
