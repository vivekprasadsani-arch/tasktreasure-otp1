#!/usr/bin/env python3
"""
Render Bot Fix - Simplified version for deployment debugging
This version helps identify why bot is not responding on Render
"""

import asyncio
import logging
import os
from datetime import datetime
from telegram import Application
from telegram.ext import CommandHandler, MessageHandler, filters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBotTest:
    def __init__(self):
        # Try to get bot token from environment first, then fallback to hardcoded
        self.bot_token = os.getenv('BOT_TOKEN', '8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0')
        self.port = int(os.getenv('PORT', 10000))
        
        logger.info(f"🤖 Bot token: {self.bot_token[:20]}...")
        logger.info(f"🌐 Port: {self.port}")
    
    async def start_command(self, update, context):
        """Simple start command"""
        try:
            await update.message.reply_text(
                "✅ Bot is working!\n\n"
                f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"💬 Chat: {update.effective_chat.id}\n\n"
                "This is a test response from Render deployment."
            )
            logger.info(f"Responded to user {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Start command error: {e}")
    
    async def echo_message(self, update, context):
        """Echo any message"""
        try:
            text = update.message.text
            await update.message.reply_text(f"Echo: {text}")
            logger.info(f"Echoed message: {text}")
        except Exception as e:
            logger.error(f"Echo error: {e}")
    
    async def run_simple_bot(self):
        """Run simplified bot for testing"""
        try:
            logger.info("🚀 Starting Simple Bot Test...")
            
            # Create application
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_message))
            
            logger.info("✅ Handlers added")
            
            # Start the bot
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            logger.info("✅ Bot is running and polling...")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            raise

def start_health_server():
    """Start simple health server"""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = f"""
                <h1>🤖 Simple Bot Test</h1>
                <p>✅ Server running at {datetime.now()}</p>
                <p>🌐 Port: {os.getenv('PORT', 10000)}</p>
                <p>🤖 Bot: Active</p>
                """.encode('utf-8')
                
                self.wfile.write(html)
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        port = int(os.getenv('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        
        def run_server():
            logger.info(f"🌐 Health server starting on port {port}")
            server.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔍 RENDER BOT DEBUGGING")
    logger.info("=" * 30)
    
    # Check environment
    logger.info("📊 Environment Check:")
    logger.info(f"   🐍 Python: Working")
    logger.info(f"   🌐 PORT: {os.getenv('PORT', 'Not set')}")
    logger.info(f"   🤖 BOT_TOKEN: {'Set' if os.getenv('BOT_TOKEN') else 'Not set'}")
    
    # Start health server first
    health_ok = start_health_server()
    logger.info(f"   🌐 Health Server: {'✅ Started' if health_ok else '❌ Failed'}")
    
    # Wait for health server to bind
    await asyncio.sleep(2)
    
    # Test simple bot
    logger.info("\n🧪 Starting Simple Bot Test...")
    
    try:
        bot = SimpleBotTest()
        await bot.run_simple_bot()
    except Exception as e:
        logger.error(f"❌ Simple bot failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
