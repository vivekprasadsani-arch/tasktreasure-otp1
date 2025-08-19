#!/usr/bin/env python3
"""
Complete OTP Bot System
Runs both the OTP monitoring bot and the user interaction bot
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickHealthHandler(BaseHTTPRequestHandler):
    """Immediate health check handler"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TaskTreasure OTP Bot System</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🤖 TaskTreasure OTP Bot System</h1>
            <h2>✅ System Status: Running</h2>
            <p>🕒 <strong>Server Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>🔧 Available Services:</h3>
            <ul>
                <li>📡 <strong>OTP Monitor:</strong> Scraping website for OTP messages</li>
                <li>📱 <strong>User Bot:</strong> Telegram bot for number requests</li>
                <li>🔔 <strong>Notifications:</strong> Individual user OTP delivery</li>
                <li>📢 <strong>Channel:</strong> Broadcasting all OTPs to channel</li>
            </ul>
            
            <h3>🌍 Supported Countries:</h3>
            <p>Venezuela, Tunisia, Tanzania, Jordan + More</p>
            
            <hr>
            <p><small>Powered by @tasktreasur_support | TaskTreasure OTP System</small></p>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logs
        pass

def start_health_server():
    """Start health check server immediately"""
    try:
        import os
        port = int(os.environ.get('PORT', 10000))
        
        server = HTTPServer(('0.0.0.0', port), QuickHealthHandler)
        logger.info(f"🌐 Health server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

# Global shared instance
SHARED_NUMBER_BOT = None

async def get_shared_number_bot():
    """Get or create shared number bot instance"""
    global SHARED_NUMBER_BOT
    if SHARED_NUMBER_BOT is None:
        from telegram_number_bot import TelegramNumberBot
        SHARED_NUMBER_BOT = TelegramNumberBot()
        logger.info("🔗 Shared number bot instance created")
    return SHARED_NUMBER_BOT

async def run_otp_monitor(shared_number_bot):
    """Run the OTP monitoring bot with shared number bot"""
    try:
        from otp_telegram_bot import OTPTelegramBot
        
        logger.info("🔍 Starting OTP Monitor Bot...")
        bot = OTPTelegramBot()
        
        # Use shared number bot instance
        bot.number_bot = shared_number_bot
        logger.info("🔗 OTP Monitor connected to shared number bot")
        
        # Test connections
        if not await bot.test_telegram_connection():
            logger.error("❌ Telegram connection failed")
            return
        
        # Initialize browser and login
        if not await bot.setup_browser():
            logger.error("❌ Browser setup failed")
            return
        
        if not await bot.login_to_website():
            logger.error("❌ Website login failed")
            return
        
        logger.info("✅ OTP Monitor Bot initialized successfully")
        
        # Start monitoring loop
        await bot.run_monitoring_loop()
        
    except Exception as e:
        logger.error(f"❌ OTP Monitor error: {e}")
        # Keep retrying
        await asyncio.sleep(10)
        await run_otp_monitor(shared_number_bot)

async def run_user_bot(shared_number_bot):
    """Run the user interaction bot using shared instance"""
    try:
        logger.info("👥 Starting User Interaction Bot...")
        
        # Use the shared instance directly
        await shared_number_bot.run_bot()
        
    except Exception as e:
        logger.error(f"❌ User Bot error: {e}")
        # Keep retrying
        await asyncio.sleep(10)
        await run_user_bot(shared_number_bot)

async def main():
    """Main async function that runs both bots with shared state"""
    try:
        logger.info("🚀 Starting Complete OTP Bot System...")
        
        # Give health server a moment to bind
        await asyncio.sleep(1)
        
        # Create shared number bot instance
        shared_number_bot = await get_shared_number_bot()
        logger.info("✅ Shared bot instance ready")
        
        # Run both bots concurrently with shared state
        await asyncio.gather(
            run_otp_monitor(shared_number_bot),
            run_user_bot(shared_number_bot),
            return_exceptions=True
        )
        
    except Exception as e:
        logger.error(f"❌ System error: {e}")

if __name__ == "__main__":
    print("🤖 Starting TaskTreasure OTP Bot System...")
    print("Press Ctrl+C to stop the system")
    
    # Start health server in background thread FIRST
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Wait a moment for port binding
    time.sleep(2)
    
    # Start main bot system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
    except Exception as e:
        logger.error(f"❌ System crash: {e}")
