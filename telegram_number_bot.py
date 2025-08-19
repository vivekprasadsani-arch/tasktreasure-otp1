#!/usr/bin/env python3
"""
Telegram Number Bot - User Interaction Handler
Handles user requests for numbers and OTP notifications
"""

import os
import csv
import json
import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramNumberBot:
    def __init__(self):
        self.bot_token = "8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0"
        self.channel_id = "-1002724043027"
        
        # Supabase configuration
        self.supabase_url = "https://wddcrtrgirhcemmobgcc.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkZGNydHJnaXJoY2VtbW9iZ2NjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjA1NTYsImV4cCI6MjA3MDkzNjU1Nn0.K5vpqoc_zakEwBd96aC-drJ5OoInTSFcrMlWy7ShIyI"
        self.supabase: Client = None
        
        # Countries directory
        self.countries_dir = "Countries"
        self.available_countries = []
        
        # User sessions and number tracking
        self.user_sessions: Dict[int, Dict] = {}  # user_id -> session_data
        self.country_number_indices: Dict[str, int] = {}  # country -> current_index
        self.assigned_numbers: Dict[str, Set[str]] = {}  # country -> set_of_assigned_numbers
        
        # Initialize
        self.init_supabase()
        self.load_countries()
        self.load_number_states()
    
    def init_supabase(self):
        """Initialize Supabase connection"""
        try:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Supabase connection initialized")
            
            # Create tables if they don't exist
            self.create_user_tables()
            
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
    
    def create_user_tables(self):
        """Create necessary tables for user management"""
        try:
            # Create user_sessions table
            self.supabase.table('user_sessions').select("id").limit(1).execute()
        except Exception:
            logger.info("Creating user_sessions table...")
            # Table doesn't exist, we'll handle it in the main app
    
    def load_countries(self):
        """Load available countries from CSV files"""
        try:
            if not os.path.exists(self.countries_dir):
                logger.error(f"❌ Countries directory not found: {self.countries_dir}")
                return
            
            self.available_countries = []
            for file in os.listdir(self.countries_dir):
                if file.endswith('.csv'):
                    country_name = file.replace('.csv', '')
                    self.available_countries.append(country_name)
                    logger.info(f"📂 Found country: {country_name}")
            
            logger.info(f"✅ Loaded {len(self.available_countries)} countries")
            
        except Exception as e:
            logger.error(f"❌ Error loading countries: {e}")
    
    def load_number_states(self):
        """Load current number allocation states"""
        try:
            for country in self.available_countries:
                self.country_number_indices[country] = 0
                self.assigned_numbers[country] = set()
            logger.info("✅ Number states initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing number states: {e}")
    
    def get_country_numbers(self, country: str) -> List[str]:
        """Get all numbers from a country CSV file"""
        try:
            csv_file = os.path.join(self.countries_dir, f"{country}.csv")
            numbers = []
            
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if row and len(row) > 0:
                        # Handle scientific notation in CSV
                        number = str(row[0]).replace('.', '').split('E')[0]
                        if len(number) > 5:  # Valid phone number length
                            numbers.append(number)
            
            logger.info(f"📞 Loaded {len(numbers)} numbers for {country}")
            return numbers
            
        except Exception as e:
            logger.error(f"❌ Error loading numbers for {country}: {e}")
            return []
    
    def get_next_available_number(self, country: str, user_id: int) -> Optional[str]:
        """Get next available number for a user"""
        try:
            numbers = self.get_country_numbers(country)
            if not numbers:
                return None
            
            total_numbers = len(numbers)
            current_index = self.country_number_indices.get(country, 0)
            assigned = self.assigned_numbers.get(country, set())
            
            # Find next available number
            attempts = 0
            while attempts < total_numbers:
                number = numbers[current_index]
                
                # Check if number is already assigned
                if number not in assigned:
                    # Assign this number
                    self.assigned_numbers[country].add(number)
                    self.country_number_indices[country] = (current_index + 1) % total_numbers
                    
                    logger.info(f"📱 Assigned {number} from {country} to user {user_id}")
                    return number
                
                # Move to next number
                current_index = (current_index + 1) % total_numbers
                attempts += 1
            
            # All numbers assigned, reset and start from beginning
            logger.warning(f"⚠️ All numbers assigned for {country}, resetting...")
            self.assigned_numbers[country].clear()
            self.country_number_indices[country] = 0
            
            # Get first number after reset
            if numbers:
                number = numbers[0]
                self.assigned_numbers[country].add(number)
                self.country_number_indices[country] = 1
                return number
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting number for {country}: {e}")
            return None
    
    def release_number(self, country: str, number: str):
        """Release a number back to available pool"""
        try:
            if country in self.assigned_numbers:
                self.assigned_numbers[country].discard(number)
                logger.info(f"🔓 Released number {number} from {country}")
        except Exception as e:
            logger.error(f"❌ Error releasing number: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
        
        logger.info(f"👤 User {user_name} ({user_id}) started the bot")
        
        # Create main menu keyboard
        keyboard = [
            [KeyboardButton("📱 Get Number"), KeyboardButton("🔄 Change Number")],
            [KeyboardButton("📊 My Status"), KeyboardButton("ℹ️ Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_message = f"""
🤖 **Welcome to TaskTreasure OTP Bot** 🤖

Hi {user_name}! 👋

🎯 **What I can do:**
📱 **Get Number** - Choose country and get a phone number
🔄 **Change Number** - Get a different number  
📊 **My Status** - Check your current number status
⚡ **Auto OTP** - Receive OTP codes instantly

🌍 **Available Countries:** {len(self.available_countries)}
🔢 **Total Numbers:** 1000+

**Choose an option from the menu below:**
"""
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_countries(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available countries"""
        if not self.available_countries:
            await update.message.reply_text("❌ No countries available at the moment.")
            return
        
        # Create inline keyboard for countries
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
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌍 **Choose a Country:**\n\nSelect a country to get a phone number:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_country_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle country selection callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        country = query.data.replace("country_", "")
        
        # Get number for user
        number = self.get_next_available_number(country, user_id)
        
        if not number:
            await query.edit_message_text(
                f"❌ Sorry, no numbers available for {country} right now.\n\nTry another country or contact support.",
                parse_mode='Markdown'
            )
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

💡 **Note:** Keep this number active. When an OTP arrives, you'll get notified instantly!
"""
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Save session to database
        await self.save_user_session(user_id, self.user_sessions[user_id])
    
    async def handle_change_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle change number request"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        country = query.data.replace("change_", "")
        
        # Release current number
        if user_id in self.user_sessions:
            old_number = self.user_sessions[user_id].get('number')
            if old_number:
                self.release_number(country, old_number)
        
        # Get new number
        new_number = self.get_next_available_number(country, user_id)
        
        if not new_number:
            await query.edit_message_text(
                f"❌ Sorry, no more numbers available for {country}.\n\nAll numbers are currently in use.",
                parse_mode='Markdown'
            )
            return
        
        # Update session
        self.user_sessions[user_id] = {
            'country': country,
            'number': new_number,
            'assigned_at': datetime.now().isoformat(),
            'waiting_for_otp': True
        }
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Change Again", callback_data=f"change_{country}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"""
🔄 **Number Changed Successfully!**

🌍 **Country:** {country}
📞 **New Number:** `{new_number}`
⏰ **Changed At:** {datetime.now().strftime('%H:%M:%S')}

🎯 **Status:** Waiting for OTP...
⚡ You will receive OTP codes for this new number!
"""
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Save updated session
        await self.save_user_session(user_id, self.user_sessions[user_id])
    
    async def show_user_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user current status"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "📊 **Your Status:**\n\n❌ No active number assigned.\n\n📱 Click 'Get Number' to start!",
                parse_mode='Markdown'
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

💡 **Tip:** OTP codes will be delivered instantly when they arrive!
"""
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
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
   • Previous number gets released

4️⃣ **Check Status:**
   • Click "📊 My Status"
   • See your current number
   • Check assignment time

🔥 **Features:**
• 🌍 Multiple countries
• 📱 1000+ phone numbers
• ⚡ Instant OTP delivery
• 🔄 Easy number changing
• 💾 Session persistence

❓ **Need Support?**
Contact: @tasktreasur_support

Powered by TaskTreasure 🚀
"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text
        
        if text == "📱 Get Number":
            await self.show_countries(update, context)
        elif text == "🔄 Change Number":
            user_id = update.effective_user.id
            if user_id in self.user_sessions:
                country = self.user_sessions[user_id]['country']
                # Simulate callback query for change number
                update.callback_query = type('CallbackQuery', (), {
                    'data': f'change_{country}',
                    'answer': lambda: None,
                    'edit_message_text': update.message.reply_text
                })()
                await self.handle_change_number(update, context)
            else:
                await update.message.reply_text("❌ No active number to change. Get a number first!")
        elif text == "📊 My Status":
            await self.show_user_status(update, context)
        elif text == "ℹ️ Help":
            await self.show_help(update, context)
        else:
            await update.message.reply_text(
                "🤖 Please use the menu buttons below or type /start to begin.",
                parse_mode='Markdown'
            )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("country_"):
            await self.handle_country_selection(update, context)
        elif query.data.startswith("change_"):
            await self.handle_change_number(update, context)
        elif query.data == "back_to_menu":
            await self.start_command(update, context)
    
    async def save_user_session(self, user_id: int, session_data: dict):
        """Save user session to database"""
        try:
            if self.supabase:
                data = {
                    'user_id': user_id,
                    'country': session_data['country'],
                    'number': session_data['number'],
                    'assigned_at': session_data['assigned_at'],
                    'waiting_for_otp': session_data['waiting_for_otp'],
                    'updated_at': datetime.now().isoformat()
                }
                
                # Upsert (insert or update)
                result = self.supabase.table('user_sessions').upsert(data, on_conflict='user_id').execute()
                logger.info(f"💾 Saved session for user {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error saving session: {e}")
    
    async def notify_user_otp(self, number: str, otp_code: str, service: str, full_message: str):
        """Notify user when OTP arrives for their number"""
        try:
            # Find user with this number
            target_user = None
            for user_id, session in self.user_sessions.items():
                if session.get('number') == number and session.get('waiting_for_otp'):
                    target_user = user_id
                    break
            
            if not target_user:
                logger.info(f"📱 No user found waiting for OTP on number {number}")
                return
            
            # Send notification to user
            app = Application.builder().token(self.bot_token).build()
            
            notification_text = f"""
🔔 **OTP Received!**

📞 **Number:** `{number}`
🔐 **OTP Code:** `{otp_code}`
💬 **Service:** {service}

⚡ **Your OTP is ready to use!**

**Full Message:**
```
{full_message}
```

Powered by @tasktreasur_support
"""
            
            await app.bot.send_message(
                chat_id=target_user,
                text=notification_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Notified user {target_user} about OTP {otp_code} for number {number}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying user: {e}")
    
    async def run_bot(self):
        """Run the Telegram bot"""
        try:
            # Create application
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            app.add_handler(CallbackQueryHandler(self.handle_callback_query))
            
            logger.info("🤖 Telegram Number Bot starting...")
            
            # Start the bot
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            logger.info("✅ Telegram Number Bot is running!")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            
        finally:
            if 'app' in locals():
                await app.updater.stop()
                await app.stop()
                await app.shutdown()

def main():
    """Main function"""
    bot = TelegramNumberBot()
    asyncio.run(bot.run_bot())

if __name__ == "__main__":
    main()
