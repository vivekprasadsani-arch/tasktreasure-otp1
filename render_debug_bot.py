#!/usr/bin/env python3
"""
Debug Bot for Render Deployment Issues
Simple bot with maximum logging for troubleshooting
"""

import os
import asyncio
import logging
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    logger.info("✅ Telegram imports successful")
except ImportError as e:
    logger.error(f"❌ Telegram import failed: {e}")
    exit(1)

class QuickHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        status = f"""
        <html><head><title>Debug Bot Status</title></head><body>
        <h1>🤖 Debug Telegram Bot</h1>
        <p><strong>Status:</strong> ✅ Running</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Port:</strong> {os.getenv('PORT', '10000')}</p>
        <p><strong>Bot Token:</strong> {os.getenv('BOT_TOKEN', 'Not Set')[:15]}...</p>
        <p><strong>Environment:</strong> Render Debug Mode</p>
        </body></html>
        """
        self.wfile.write(status.encode('utf-8'))
        
    def log_message(self, format, *args):
        pass

class DebugBot:
    def __init__(self):
        # Environment variables with detailed logging
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_user_id = int(os.getenv('ADMIN_USER_ID', 7325836764))
        self.port = int(os.getenv('PORT', 10000))
        
        logger.info("🔧 Debug Bot Configuration:")
        logger.info(f"   Token: {'✅ Set' if self.bot_token else '❌ Missing'}")
        logger.info(f"   Admin: {self.admin_user_id}")
        logger.info(f"   Port: {self.port}")
        
        if not self.bot_token:
            logger.error("❌ BOT_TOKEN not found in environment!")
            raise ValueError("BOT_TOKEN required")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with debugging"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            logger.info(f"📥 /start from user {user.id} ({user.first_name}) in chat {chat_id}")
            
            # Create a detailed response
            keyboard = [
                [InlineKeyboardButton("🔧 Test Echo", callback_data="test_echo")],
                [InlineKeyboardButton("📊 Debug Info", callback_data="debug_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = f"""
🤖 **Debug Bot Active!**

✅ **Connection Status:** Working
🆔 **Your ID:** `{user.id}`
💬 **Chat ID:** `{chat_id}`
🕐 **Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 **Platform:** Render Cloud
🔧 **Mode:** Debug Version

👇 **Test Functions:**
"""
            
            await update.message.reply_text(
                message_text, 
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ Response sent to user {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            data = query.data
            
            logger.info(f"📱 Callback '{data}' from user {user_id}")
            
            if data == "test_echo":
                await query.edit_message_text(
                    f"🔄 **Echo Test Successful!**\n\n"
                    f"✅ Callback working\n"
                    f"✅ Message editing working\n"
                    f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"Send any message to test text handling!"
                )
            
            elif data == "debug_info":
                await query.edit_message_text(
                    f"🔧 **Debug Information**\n\n"
                    f"🆔 User ID: `{user_id}`\n"
                    f"🤖 Bot Token: `{self.bot_token[:15]}...`\n"
                    f"👑 Admin: `{self.admin_user_id}`\n"
                    f"🌐 Port: `{self.port}`\n"
                    f"📅 Server: {datetime.now().isoformat()}\n\n"
                    f"✅ All systems operational!"
                )
            
            logger.info(f"✅ Callback processed: {data}")
            
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            user = update.effective_user
            text = update.message.text
            
            logger.info(f"💬 Message from {user.id}: {text}")
            
            response = f"📢 **Echo Response**\n\n" \
                      f"👤 From: {user.first_name}\n" \
                      f"💬 Message: `{text}`\n" \
                      f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n\n" \
                      f"✅ Bot is responding correctly!"
            
            await update.message.reply_text(response)
            logger.info(f"✅ Echo sent to {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
    
    async def run_bot(self):
        """Run the debug bot"""
        try:
            logger.info("🚀 Starting Debug Bot...")
            
            # Create application
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            app.add_handler(CallbackQueryHandler(self.handle_callback))
            
            logger.info("✅ Handlers registered")
            
            # Test connection
            try:
                bot_info = await app.bot.get_me()
                logger.info(f"✅ Bot connected successfully: @{bot_info.username}")
                logger.info(f"   Bot ID: {bot_info.id}")
                logger.info(f"   Bot Name: {bot_info.first_name}")
            except Exception as conn_error:
                logger.error(f"❌ Bot connection test failed: {conn_error}")
                raise
            
            # Start polling with optimized settings
            logger.info("🔄 Starting polling...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                poll_interval=2.0,
                timeout=20,
                read_timeout=10,
                write_timeout=10,
                connect_timeout=15
            )
            
            logger.info("✅ Debug Bot is now polling for messages...")
            
            # Keep alive with regular status
            while True:
                await asyncio.sleep(60)
                logger.info(f"🔄 Bot Status: Active - {datetime.now().strftime('%H:%M:%S')}")
                
        except Exception as e:
            logger.error(f"❌ Bot startup failed: {e}")
            import traceback
            logger.error(f"❌ Full error: {traceback.format_exc()}")
            raise

def start_health_server():
    """Start health check server"""
    try:
        port = int(os.getenv('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), QuickHealthHandler)
        logger.info(f"🌐 Health server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

async def main():
    """Main function"""
    logger.info("=" * 50)
    logger.info("🔧 DEBUG TELEGRAM BOT - Render Troubleshooting")
    logger.info("=" * 50)
    
    try:
        bot = DebugBot()
        await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")

if __name__ == "__main__":
    print("🔧 Starting Debug Telegram Bot...")
    
    # Start health server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    time.sleep(1)
    
    # Start bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Debug bot stopped")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
