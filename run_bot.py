#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple runner script for the OTP Telegram Bot
IMMEDIATE PORT BINDING for Render
"""

import sys
import os
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickHealthHandler(BaseHTTPRequestHandler):
    """Immediate health check handler"""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is starting...")
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def immediate_port_bind():
    """Immediately bind to port for Render"""
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🚨 IMMEDIATE PORT BIND: {port}")
        
        server = HTTPServer(("0.0.0.0", port), QuickHealthHandler)
        logger.info(f"🔗 PORT {port} BOUND SUCCESSFULLY")
        
        # Keep server running in background
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ IMMEDIATE PORT BIND FAILED: {e}")
        raise

if __name__ == "__main__":
    # STEP 1: IMMEDIATE PORT BINDING
    logger.info("🚀 STEP 1: Binding port immediately...")
    port_thread = threading.Thread(target=immediate_port_bind, daemon=True)
    port_thread.start()
    
    # Give port bind time
    time.sleep(0.5)
    logger.info("✅ STEP 1 COMPLETE: Port bound")
    
    # STEP 2: Start the actual bot
    logger.info("🤖 STEP 2: Starting OTP bot...")
    
    try:
        import asyncio
        from otp_telegram_bot import OTPTelegramBot
        
        async def run_bot():
            bot = OTPTelegramBot()
            await bot.run_monitoring_loop()
        
        # Run the bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")