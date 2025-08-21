#!/usr/bin/env python3
"""
Setup script for Admin Approval System
Automatically creates the required database tables in Supabase
"""

import os
from supabase import create_client, Client

def setup_approval_system():
    """Setup the approval system tables in Supabase"""
    
    # Supabase configuration
    SUPABASE_URL = "https://wddcrtrgirhcemmobgcc.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkZGNydHJnaXJoY2VtbW9iZ2NjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjA1NTYsImV4cCI6MjA3MDkzNjU1Nn0.K5vpqoc_zakEwBd96aC-drJ5OoInTSFcrMlWy7ShIyI"
    
    print("🚀 Setting up Admin Approval System...")
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
        
        # Test if tables already exist
        try:
            result = supabase.table('user_approval_requests').select("id").limit(1).execute()
            print("✅ user_approval_requests table already exists")
        except Exception:
            print("❌ user_approval_requests table does not exist")
            print("📝 Please run the SQL script 'user_approval_system.sql' in Supabase SQL Editor")
        
        try:
            result = supabase.table('approved_users').select("id").limit(1).execute()
            print("✅ approved_users table already exists")
        except Exception:
            print("❌ approved_users table does not exist")
            print("📝 Please run the SQL script 'user_approval_system.sql' in Supabase SQL Editor")
        
        # Check admin settings
        try:
            result = supabase.table('admin_settings').select('setting_value').eq('setting_key', 'admin_user_id').execute()
            if result.data:
                admin_id = result.data[0]['setting_value']
                print(f"✅ Admin user configured: {admin_id}")
            else:
                print("⚠️  No admin user configured")
                print("📝 Please set admin_user_id in admin_settings table")
        except Exception as e:
            print(f"❌ Error checking admin settings: {e}")
        
        print("\n🎉 Setup check completed!")
        print("\n📋 Next steps:")
        print("1. If tables don't exist, run 'user_approval_system.sql' in Supabase")
        print("2. Ensure admin user ID is set in admin_settings table")
        print("3. Deploy the updated bot with approval system")
        print("4. Test the approval workflow")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_approval_system()
