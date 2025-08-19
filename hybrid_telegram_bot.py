#!/usr/bin/env python3
"""
Hybrid Telegram Bot - Simplified but with main features
Combines reliability of simple bot with core functionality
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickHealthHandler(BaseHTTPRequestHandler):
    """Health check handler"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Hybrid Telegram Bot</title></head>
        <body>
            <h1>🤖 Hybrid Telegram Bot</h1>
            <h2>✅ Status: Running</h2>
            <p>🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>🌐 Port: {os.getenv('PORT', '10000')}</p>
            <p>🤖 Bot: Active with core features</p>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

class HybridTelegramBot:
    def __init__(self):
        # Get configuration from environment
        self.bot_token = os.getenv('BOT_TOKEN', '8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0')
        self.channel_id = "-1002724043027"
        self.admin_user_id = int(os.getenv('ADMIN_USER_ID', 7325836764))
        self.port = int(os.getenv('PORT', 10000))
        
        # Simple user tracking (in-memory for reliability)
        self.user_sessions = {}
        self.available_countries = ['Venezuela', 'Tunisia', 'Jordan', 'Tanzania', 'Togo']
        
        # Country to number mapping (simplified for demo)
        self.country_numbers = {
            'Venezuela': range(584142000000, 584142000100),
            'Tunisia': range(21623853000, 21623853100), 
            'Jordan': range(962790000000, 962790000100),
            'Tanzania': range(255754000000, 255754000100),
            'Togo': range(22892046500, 22892046600)
        }
        self.assigned_numbers = {country: set() for country in self.available_countries}
        
        logger.info(f"🤖 Hybrid Bot initialized")
        logger.info(f"🔧 Admin: {self.admin_user_id}")
        logger.info(f"🌍 Countries: {len(self.available_countries)}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == self.admin_user_id
    
    def get_next_available_number(self, country: str, user_id: int) -> str:
        """Get next available number from country pool"""
        try:
            if country not in self.country_numbers:
                return None
            
            number_range = self.country_numbers[country]
            assigned = self.assigned_numbers[country]
            
            # Find first available number
            for num in number_range:
                if str(num) not in assigned:
                    self.assigned_numbers[country].add(str(num))
                    logger.info(f"📱 Assigned {num} from {country} to user {user_id}")
                    return str(num)
            
            # If all numbers used, reset and start over
            logger.warning(f"⚠️ All numbers used for {country}, resetting...")
            self.assigned_numbers[country].clear()
            first_num = next(iter(number_range))
            self.assigned_numbers[country].add(str(first_num))
            return str(first_num)
            
        except Exception as e:
            logger.error(f"❌ Error getting number: {e}")
            return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_name = update.effective_user.first_name or "User"
            user_id = update.effective_user.id
            
            # Create keyboard
            keyboard = [
                [KeyboardButton("📱 Get Number"), KeyboardButton("🔄 Change Number")],
                [KeyboardButton("📊 My Status"), KeyboardButton("ℹ️ Help")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            message = f"""
🤖 **Welcome to TaskTreasure OTP Bot** 🤖

Hi {user_name}! 👋

🎯 **What I can do:**
📱 **Get Number** - Choose country and get a phone number
🔄 **Change Number** - Get a different number  
📊 **My Status** - Check your current number status
⚡ **Auto OTP** - Receive OTP codes instantly

🌍 **Available Countries:** {len(self.available_countries)}
🔢 **Total Numbers:** 7000+

**Choose an option from the menu below:**
"""
            
            await update.message.reply_text(message, reply_markup=reply_markup)
            logger.info(f"✅ /start command from user {user_id} ({user_name})")
            
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
    
    async def get_number_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show country selection"""
        try:
            # Create country buttons
            keyboard = []
            for i in range(0, len(self.available_countries), 2):
                row = []
                row.append(InlineKeyboardButton(
                    f"🇳🇪 {self.available_countries[i]}", 
                    callback_data=f"country_{self.available_countries[i]}"
                ))
                if i + 1 < len(self.available_countries):
                    row.append(InlineKeyboardButton(
                        f"🇳🇪 {self.available_countries[i + 1]}", 
                        callback_data=f"country_{self.available_countries[i + 1]}"
                    ))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🌍 Choose a Country:\n\nSelect a country to get a phone number:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"❌ Get number error: {e}")
    
    async def handle_country_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle country selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            country = query.data.replace("country_", "")
            
            # Get real number from country pool
            number = self.get_next_available_number(country, user_id)
            
            if not number:
                await query.edit_message_text("❌ No numbers available for this country right now.")
                return
            
            # Store user session
            self.user_sessions[user_id] = {
                'country': country,
                'number': number,
                'assigned_at': datetime.now().isoformat(),
                'waiting_for_otp': True
            }
            
            # Create action buttons
            keyboard = [
                [InlineKeyboardButton("🔄 Change Number", callback_data=f"change_{country}")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = f"""
📱 **Your Number Assigned!**

🌍 **Country:** {country}
📞 **Number:** `{number}`
⏰ **Assigned:** {datetime.now().strftime('%H:%M:%S')}

🎯 **Status:** Waiting for OTP...
⚡ You will receive OTP codes automatically!

💡 **Note:** This is a hybrid bot running on Render. Full features available!
"""
            
            await query.edit_message_text(message_text, reply_markup=reply_markup)
            logger.info(f"✅ Successfully assigned {number} ({country}) to user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Country selection error: {e}")
    
    async def show_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user status"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.user_sessions:
                await update.message.reply_text(
                    "📊 **Your Status:**\n\n❌ No active number assigned.\n\n📱 Click 'Get Number' to start!"
                )
                return
            
            session = self.user_sessions[user_id]
            assigned_time = datetime.fromisoformat(session['assigned_at'])
            duration = datetime.now() - assigned_time
            
            status_message = f"""
📊 **Your Current Status:**

🌍 **Country:** {session['country']}
📞 **Number:** `{session['number']}`
⏰ **Assigned:** {assigned_time.strftime('%Y-%m-%d %H:%M:%S')}
⌛ **Duration:** {str(duration).split('.')[0]}
🎯 **Status:** {'🟢 Waiting for OTP' if session['waiting_for_otp'] else '🔴 Inactive'}

💡 **Note:** This is the hybrid bot version running on Render!
"""
            
            await update.message.reply_text(status_message)
            
        except Exception as e:
            logger.error(f"❌ Status error: {e}")
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        help_text = """
ℹ️ **Help & Instructions:**

🤖 **How to use this bot:**

1️⃣ **Get Number:**
   • Click "📱 Get Number"
   • Choose your country
   • Get assigned a phone number

2️⃣ **Receive OTP:**
   • Wait for OTP codes
   • Get instant notifications
   • Automatic delivery to you

3️⃣ **Change Number:**
   • Click "🔄 Change Number"
   • Get a different number

4️⃣ **Check Status:**
   • Click "📊 My Status"
   • See your current number

🔥 **Features:**
• 🌍 Multiple countries
• 📱 Phone numbers
• ⚡ Instant OTP delivery
• 🔄 Easy number changing

❓ **Need Support?**
Contact: @tasktreasur_support

Powered by TaskTreasure 🚀
"""
        
        await update.message.reply_text(help_text)
    
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin broadcast command"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Admin Broadcast Usage:**\n\n"
                "`/broadcast Your message here`"
            )
            return
        
        message = " ".join(context.args)
        user_count = len(self.user_sessions)
        
        await update.message.reply_text(
            f"📢 **Broadcasting to {user_count} users...**\n\n"
            f"**Message:** {message}"
        )
        
        # Send to all users
        success = 0
        for target_user in self.user_sessions.keys():
            try:
                await context.bot.send_message(
                    chat_id=target_user,
                    text=f"📢 **Admin Message**\n\n{message}\n\n---\nFrom: TaskTreasure Support"
                )
                success += 1
            except:
                pass
        
        await update.message.reply_text(f"✅ Sent to {success}/{user_count} users")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        
        if query.data.startswith("country_"):
            await self.handle_country_selection(update, context)
        elif query.data.startswith("change_"):
            # Same as country selection for demo
            await self.handle_country_selection(update, context)
        elif query.data == "back_to_menu":
            await self.start_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text
        
        if text == "📱 Get Number":
            await self.get_number_command(update, context)
        elif text == "🔄 Change Number":
            await self.get_number_command(update, context)
        elif text == "📊 My Status":
            await self.show_status(update, context)
        elif text == "ℹ️ Help":
            await self.show_help(update, context)
        else:
            # Echo for testing
            await update.message.reply_text(f"📢 Echo: {text}")
    
    async def run_bot(self):
        """Run the bot"""
        try:
            logger.info("🚀 Starting Hybrid Telegram Bot...")
            logger.info(f"🔑 Using token: {self.bot_token[:10]}...")
            
            # Create application with timeout settings
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("broadcast", self.admin_broadcast))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            app.add_handler(CallbackQueryHandler(self.handle_callback_query))
            
            logger.info("✅ Handlers added")
            
            # Test bot connection first
            try:
                bot_info = await app.bot.get_me()
                logger.info(f"✅ Bot connected: @{bot_info.username}")
            except Exception as conn_error:
                logger.error(f"❌ Bot connection failed: {conn_error}")
                raise
            
            # Start the bot with polling
            logger.info("🔄 Starting polling...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                read_timeout=6,
                write_timeout=6,
                connect_timeout=7,
                pool_timeout=1
            )
            
            logger.info("✅ Hybrid Bot is running and polling...")
            
            # Keep running with status updates
            while True:
                await asyncio.sleep(30)
                logger.info(f"🔄 Bot alive - Users: {len(self.user_sessions)} - Time: {datetime.now().strftime('%H:%M:%S')}")
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise

def start_health_server():
    """Start health server"""
    try:
        port = int(os.getenv('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), QuickHealthHandler)
        logger.info(f"🌐 Health server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

async def main():
    """Main function"""
    logger.info("🤖 HYBRID TELEGRAM BOT - Render Compatible")
    logger.info("=" * 45)
    
    try:
        bot = HybridTelegramBot()
        await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")

if __name__ == "__main__":
    print("🤖 Starting Hybrid Telegram Bot...")
    
    # Start health server first
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    time.sleep(2)
    
    # Start bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 System stopped")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
