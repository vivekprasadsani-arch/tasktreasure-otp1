-- Update Admin User ID in Supabase
-- Run this in your Supabase SQL Editor

-- Update admin user ID to 7325836764
UPDATE admin_settings 
SET setting_value = '7325836764', 
    updated_at = NOW()
WHERE setting_key = 'admin_user_id';

-- If admin_settings table doesn't exist or record doesn't exist, insert it
INSERT INTO admin_settings (setting_key, setting_value) 
VALUES ('admin_user_id', '7325836764') 
ON CONFLICT (setting_key) DO UPDATE SET 
    setting_value = EXCLUDED.setting_value,
    updated_at = NOW();

-- Verify the update
SELECT setting_key, setting_value, updated_at 
FROM admin_settings 
WHERE setting_key = 'admin_user_id';
