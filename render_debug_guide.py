#!/usr/bin/env python3
"""
Render Deployment Debug Guide for Telegram Bot
Common issues and solutions for Render deployment
"""

import os
import asyncio
import logging
from datetime import datetime

def check_render_deployment():
    """Check common Render deployment issues"""
    print("🔍 RENDER DEPLOYMENT DEBUG GUIDE")
    print("="*50)
    
    issues_found = []
    solutions = []
    
    print("\n📋 Common Render Bot Issues & Solutions:\n")
    
    # Issue 1: Environment Variables
    print("1️⃣ ENVIRONMENT VARIABLES:")
    print("   ❌ Problem: Bot token/credentials not set in Render")
    print("   ✅ Solution: Go to Render Dashboard > Environment > Add:")
    print("      - BOT_TOKEN=8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0")
    print("      - SUPABASE_URL=https://wddcrtrgirhcemmobgcc.supabase.co")
    print("      - SUPABASE_KEY=eyJhbGci...")
    print("      - PORT=10000")
    
    # Issue 2: Start Command
    print("\n2️⃣ START COMMAND:")
    print("   ❌ Problem: Wrong start command in render.yaml")
    print("   ✅ Current: python run_complete_bot.py")
    print("   ✅ Alternative: python telegram_number_bot.py")
    
    # Issue 3: Port Binding
    print("\n3️⃣ PORT BINDING:")
    print("   ❌ Problem: Health server not binding to PORT")
    print("   ✅ Solution: Ensure health server runs first")
    print("   ✅ Code: QuickHealthHandler binds immediately")
    
    # Issue 4: Dependencies
    print("\n4️⃣ DEPENDENCIES:")
    print("   ❌ Problem: Missing system packages")
    print("   ✅ Solution: Check Aptfile contains:")
    print("      - chromium")
    print("      - chromium-driver")
    
    # Issue 5: Database Tables
    print("\n5️⃣ DATABASE TABLES:")
    print("   ❌ Problem: Missing Supabase tables")
    print("   ✅ Solution: Run these SQL scripts in Supabase:")
    print("      - setup_database.sql")
    print("      - user_sessions_table.sql") 
    print("      - otp_history_table.sql")
    
    # Issue 6: Bot Commands Not Working
    print("\n6️⃣ BOT COMMANDS:")
    print("   ❌ Problem: /start command not responding")
    print("   ✅ Solution: Check bot runs in polling mode")
    print("   ✅ Check: Bot token is correct and active")
    
    # Issue 7: Playwright Browser
    print("\n7️⃣ PLAYWRIGHT BROWSER:")
    print("   ❌ Problem: Browser not installed on Render")
    print("   ✅ Solution: buildCommand in render.yaml:")
    print("      playwright install chromium && playwright install-deps chromium")
    
    print("\n" + "="*50)
    print("🔧 DEBUGGING STEPS:")
    print("="*50)
    
    print("\n📊 Check Render Logs:")
    print("   1. Go to Render Dashboard")
    print("   2. Click your service")
    print("   3. Go to 'Logs' tab")
    print("   4. Look for error messages")
    
    print("\n🧪 Test Locally First:")
    print("   1. Run: python telegram_number_bot.py")
    print("   2. Test /start command")
    print("   3. Check all features work")
    
    print("\n📱 Telegram Bot Issues:")
    print("   ❌ Bot not responding to /start")
    print("   ❌ Commands not working")
    print("   ❌ No reply from bot")
    
    print("\n🔧 Quick Fixes:")
    print("   1. Check bot token in Render environment")
    print("   2. Verify Supabase tables exist")
    print("   3. Check render.yaml configuration")
    print("   4. Test health server endpoint")
    
    print("\n🚨 CRITICAL CHECKS:")
    print("   ✅ Health server binding port immediately")
    print("   ✅ Bot token set in environment")
    print("   ✅ Supabase tables created")
    print("   ✅ Dependencies installed correctly")
    
    return True

async def test_bot_locally():
    """Test bot components locally before deployment"""
    print("\n🧪 LOCAL BOT TEST")
    print("="*30)
    
    try:
        # Test telegram bot import
        from telegram_number_bot import TelegramNumberBot
        print("✅ TelegramNumberBot import successful")
        
        # Test bot initialization
        bot = TelegramNumberBot()
        print(f"✅ Bot initialized: {len(bot.available_countries)} countries")
        print(f"✅ Supabase: {'Connected' if bot.supabase else 'Not connected'}")
        print(f"✅ Admin: {bot.admin_user_id or 'Not configured'}")
        
        # Test if bot can be run
        print("\n📱 Bot Components:")
        print(f"   🤖 Bot Token: {'Set' if bot.bot_token else 'Missing'}")
        print(f"   📡 Supabase URL: {'Set' if bot.supabase_url else 'Missing'}")
        print(f"   🔑 Supabase Key: {'Set' if bot.supabase_key else 'Missing'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

def render_deployment_checklist():
    """Complete deployment checklist"""
    print("\n📋 RENDER DEPLOYMENT CHECKLIST")
    print("="*40)
    
    checklist = [
        "✅ GitHub repository updated",
        "✅ render.yaml configured correctly", 
        "✅ requirements.txt has all dependencies",
        "✅ Aptfile has system packages",
        "✅ runtime.txt specifies Python version",
        "⚠️ Environment variables set in Render",
        "⚠️ Supabase tables created",
        "⚠️ Health server binding port",
        "⚠️ Bot token active and correct",
        "⚠️ Admin user ID configured"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n🔧 Next Steps:")
    print("   1. Check Render logs for specific errors")
    print("   2. Test bot locally first")
    print("   3. Verify database tables exist") 
    print("   4. Check environment variables")
    print("   5. Test health endpoint")

if __name__ == "__main__":
    check_render_deployment()
    
    print("\n" + "="*50)
    print("🧪 TESTING BOT LOCALLY...")
    
    success = asyncio.run(test_bot_locally())
    
    print("\n" + "="*50)
    render_deployment_checklist()
    
    if success:
        print("\n✅ Local test passed - Check Render environment")
    else:
        print("\n❌ Local test failed - Fix issues first")
