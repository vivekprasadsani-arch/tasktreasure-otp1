#!/usr/bin/env python3
"""
IMMEDIATE FIX: Run the telegram test bot
This file exists to satisfy Render's cached startCommand
"""

import subprocess
import sys

if __name__ == "__main__":
    print("🔄 REDIRECT: Running telegram test bot instead...")
    try:
        subprocess.run([sys.executable, "telegram_test_bot.py"])
    except Exception as e:
        print(f"❌ Error: {e}")
        # Fallback to simple bot
        try:
            subprocess.run([sys.executable, "simple_telegram_bot.py"])
        except:
            print("❌ All bots failed")
