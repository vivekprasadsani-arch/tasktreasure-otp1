#!/usr/bin/env python3
"""
Simple Telegram Bot for Render Debugging
Minimal version to test if basic bot functionality works on Render
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickHealthHandler(BaseHTTPRequestHandler):
    """Immediate health check handler for Render"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Simple Telegram Bot</title></head>
        <body>
            <h1>🤖 Simple Telegram Bot</h1>
            <h2>✅ Status: Running</h2>
            <p>🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>🌐 Port: {os.getenv('PORT', '10000')}</p>
            <p>🤖 Bot: Active and polling</p>
            <hr>
            <p>This is a simplified version for debugging Render deployment.</p>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress default HTTP logs

class SimpleTelegramBot:
    def __init__(self):
        # Get configuration from environment or use defaults
        self.bot_token = os.getenv('BOT_TOKEN', '8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0')
        self.port = int(os.getenv('PORT', 10000))
        
        logger.info(f"🤖 Initializing Simple Telegram Bot")
        logger.info(f"🌐 Port: {self.port}")
        logger.info(f"🤖 Bot token: {self.bot_token[:20]}...")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_name = update.effective_user.first_name or "User"
            user_id = update.effective_user.id
            
            message = f"""
🤖 **Simple Bot Working!**

👋 Hello {user_name}!
👤 Your ID: {user_id}
🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Deployed on Render
            
✅ If you see this message, the bot is working correctly!

Try typing anything to test echo functionality.
"""
            
            await update.message.reply_text(message)
            logger.info(f"✅ Responded to /start from user {user_id} ({user_name})")
            
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
    
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Echo any text message"""
        try:
            user_text = update.message.text
            user_id = update.effective_user.id
            
            response = f"📢 Echo: {user_text}\n🕒 {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(response)
            logger.info(f"✅ Echoed message from user {user_id}: {user_text}")
            
        except Exception as e:
            logger.error(f"❌ Echo error: {e}")
    
    async def run_bot(self):
        """Run the simple telegram bot"""
        try:
            logger.info("🚀 Starting Simple Telegram Bot...")
            
            # Create application
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_message))
            
            logger.info("✅ Command handlers added")
            
            # Start the bot
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            logger.info("✅ Bot is now running and polling for messages...")
            logger.info("📱 Test the bot by sending /start command")
            
            # Keep running
            while True:
                await asyncio.sleep(10)
                logger.info("🔄 Bot is alive and polling...")
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            raise
        finally:
            if 'app' in locals():
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
                logger.info("🛑 Bot stopped")

def start_health_server():
    """Start health check server immediately"""
    try:
        port = int(os.getenv('PORT', 10000))
        
        server = HTTPServer(('0.0.0.0', port), QuickHealthHandler)
        logger.info(f"🌐 Health server starting on 0.0.0.0:{port}")
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

async def main():
    """Main function"""
    logger.info("🔍 SIMPLE TELEGRAM BOT - RENDER DEBUG VERSION")
    logger.info("=" * 50)
    
    # Environment check
    logger.info("📊 Environment Variables:")
    logger.info(f"   PORT: {os.getenv('PORT', 'Not set')}")
    logger.info(f"   BOT_TOKEN: {'✅ Set' if os.getenv('BOT_TOKEN') else '❌ Not set'}")
    
    try:
        # Start bot
        bot = SimpleTelegramBot()
        await bot.run_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🤖 Starting Simple Telegram Bot for Render...")
    print("Press Ctrl+C to stop")
    
    # Start health server in background thread FIRST
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Give health server time to bind
    time.sleep(2)
    
    # Start main bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
    except Exception as e:
        logger.error(f"❌ System crash: {e}")
