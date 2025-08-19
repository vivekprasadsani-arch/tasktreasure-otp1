#!/usr/bin/env python3
"""
Ultra Simple Telegram Bot for Render Testing
Minimal dependencies, maximum reliability
"""

import os
import asyncio
import logging
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Telegram Bot Test - Running')
    
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health server on port {port}")
    server.serve_forever()

async def test_telegram_bot():
    """Test basic Telegram bot functionality"""
    try:
        # Import telegram
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
        logger.info("✅ Telegram imports successful")
        
        # Get bot token
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("❌ BOT_TOKEN not found!")
            return
        
        logger.info(f"✅ Bot token found: {bot_token[:15]}...")
        
        # Create app
        app = Application.builder().token(bot_token).build()
        
        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            logger.info(f"📥 /start from {user.id}")
            
            await update.message.reply_text(
                f"🤖 **Test Bot Working!**\n\n"
                f"✅ Render deployment successful\n"
                f"🆔 Your ID: `{user.id}`\n" 
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"🎉 Telegram bot is responding correctly!"
            )
            logger.info(f"✅ Response sent to {user.id}")
        
        async def echo_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text
            user = update.effective_user
            logger.info(f"💬 Echo from {user.id}: {text}")
            
            await update.message.reply_text(f"Echo: {text}")
            logger.info(f"✅ Echo sent to {user.id}")
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_msg))
        
        logger.info("✅ Handlers added")
        
        # Test connection
        bot_info = await app.bot.get_me()
        logger.info(f"✅ Bot connected: @{bot_info.username}")
        
        # Start polling
        logger.info("🔄 Starting polling...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        logger.info("✅ Telegram bot is polling for messages!")
        
        # Keep alive
        while True:
            await asyncio.sleep(30)
            logger.info(f"🔄 Bot alive: {datetime.now().strftime('%H:%M:%S')}")
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    logger.info("🤖 STARTING TELEGRAM TEST BOT")
    logger.info("=" * 40)
    
    await test_telegram_bot()

if __name__ == "__main__":
    print("🤖 Telegram Test Bot Starting...")
    
    # Health server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    time.sleep(1)
    
    # Bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
