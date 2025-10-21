#!/usr/bin/env python3
"""
TaskTreasure OTP Bot - Complete System
Runs both OTP monitoring and user interaction bots
"""

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 STARTING COMPLETE OTP BOT SYSTEM...")
    try:
        subprocess.run([sys.executable, "run_complete_bot.py"])
    except Exception as e:
        print(f"❌ Complete system error: {e}")
        print("🔄 Fallback: Starting number bot only...")
        try:
            subprocess.run([sys.executable, "telegram_number_bot.py"])
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
