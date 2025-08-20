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
import re
import pandas as pd
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
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
        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            logger.error("❌ BOT_TOKEN environment variable not set!")
            raise ValueError("BOT_TOKEN environment variable is required")
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
        
        # Admin settings
        self.admin_user_id = None
        
        # Initialize
        self.init_supabase()
        self.load_countries()
        self.load_number_states()
        self.load_admin_settings()
        self.load_user_sessions_from_db()
    
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
                if file.endswith('.xlsx'):
                    country_name = file.replace('.xlsx', '')
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
    
    def load_admin_settings(self):
        """Load admin settings from database"""
        try:
            if self.supabase:
                result = self.supabase.table('admin_settings').select('setting_value').eq('setting_key', 'admin_user_id').execute()
                if result.data:
                    self.admin_user_id = int(result.data[0]['setting_value'])
                    logger.info(f"✅ Admin user loaded: {self.admin_user_id}")
                else:
                    logger.warning("⚠️ No admin user configured")
        except Exception as e:
            logger.error(f"❌ Error loading admin settings: {e}")
    
    def format_phone_number(self, number: str, country: str = "") -> str:
        """Format phone number for display with proper spacing and country code"""
        try:
            # Remove any existing formatting
            clean_number = re.sub(r'[^\d+]', '', number)
            
            # If number doesn't start with +, try to add country code
            if not clean_number.startswith('+'):
                # Add + if it's a valid international number
                if len(clean_number) > 7:
                    clean_number = '+' + clean_number
            
            # Format with spaces for readability
            if len(clean_number) > 10:
                # International format: +XX XXX XXX XXXX
                return f"{clean_number[:3]} {clean_number[3:6]} {clean_number[6:9]} {clean_number[9:]}"
            else:
                # Shorter numbers: +XX XXXX XXXX
                return f"{clean_number[:3]} {clean_number[3:7]} {clean_number[7:]}"
                
        except Exception as e:
            logger.warning(f"⚠️ Number formatting error: {e}")
            return number  # Return original if formatting fails
    
    def get_copy_friendly_number(self, number: str) -> str:
        """Get clean number for copy-paste without spaces"""
        try:
            # Remove any existing formatting and ensure clean format
            clean_number = re.sub(r'[^\d+]', '', number)
            
            # If number doesn't start with +, add it
            if not clean_number.startswith('+'):
                if len(clean_number) > 7:
                    clean_number = '+' + clean_number
            
            return clean_number
                
        except Exception as e:
            logger.warning(f"⚠️ Copy-friendly format error: {e}")
            return number
    
    def load_user_sessions_from_db(self):
        """Load active user sessions from database on bot restart"""
        try:
            if self.supabase:
                result = self.supabase.table('user_sessions').select('*').eq('waiting_for_otp', True).execute()
                for session in result.data:
                    user_id = session['user_id']
                    self.user_sessions[user_id] = {
                        'country': session['country'],
                        'number': session['number'],
                        'assigned_at': session['assigned_at'],
                        'waiting_for_otp': session['waiting_for_otp']
                    }
                    
                    # Mark number as assigned
                    country = session['country']
                    number = session['number']
                    if country in self.assigned_numbers:
                        self.assigned_numbers[country].add(number)
                
                logger.info(f"✅ Restored {len(result.data)} user sessions from database")
        except Exception as e:
            logger.error(f"❌ Error loading user sessions: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return self.admin_user_id and user_id == self.admin_user_id
    
    def add_number_to_cooldown(self, number: str):
        """Add number to 3-day cooldown after receiving OTP"""
        try:
            if not self.supabase:
                return
            
            # Remove any existing cooldown for this number
            self.supabase.table('otp_cooldown').delete().eq('number', number).execute()
            
            # Add new cooldown
            cooldown_data = {
                'number': number,
                'last_otp_at': datetime.now().isoformat(),
                'cooldown_until': (datetime.now() + timedelta(days=3)).isoformat()
            }
            
            self.supabase.table('otp_cooldown').insert(cooldown_data).execute()
            logger.info(f"⏰ Number {number} added to 3-day cooldown")
            
        except Exception as e:
            logger.error(f"❌ Error adding cooldown: {e}")

    async def log_otp_received(self, user_id: int, number: str, country: str, service: str, otp_code: str, message: str):
        """Log OTP received for user statistics and add number to cooldown"""
        try:
            if self.supabase:
                data = {
                    'user_id': user_id,
                    'number': number,
                    'country': country,
                    'service': service,
                    'otp_code': otp_code,
                    'message': message,
                    'received_at': datetime.now().isoformat()
                }
                self.supabase.table('otp_history').insert(data).execute()
                logger.info(f"📊 OTP logged for user {user_id}: {service} - {otp_code}")
                
                # Add number to 3-day cooldown
                self.add_number_to_cooldown(number)
                
        except Exception as e:
            logger.error(f"❌ Error logging OTP: {e}")
    
    async def get_user_otp_stats(self, user_id: int) -> dict:
        """Get user OTP statistics"""
        try:
            if self.supabase:
                # Get overall stats
                stats_result = self.supabase.table('user_otp_stats').select('*').eq('user_id', user_id).execute()
                
                # Get recent OTPs
                recent_result = self.supabase.table('otp_history').select('*').eq('user_id', user_id).order('received_at', desc=True).limit(5).execute()
                
                if stats_result.data:
                    stats = stats_result.data[0]
                    return {
                        'total_otps': stats.get('total_otps', 0),
                        'unique_services': stats.get('unique_services', 0),
                        'unique_countries': stats.get('unique_countries', 0),
                        'last_otp_at': stats.get('last_otp_at'),
                        'first_otp_at': stats.get('first_otp_at'),
                        'recent_otps': recent_result.data
                    }
                else:
                    return {
                        'total_otps': 0,
                        'unique_services': 0,
                        'unique_countries': 0,
                        'last_otp_at': None,
                        'first_otp_at': None,
                        'recent_otps': []
                    }
        except Exception as e:
            logger.error(f"❌ Error getting OTP stats: {e}")
            return {'total_otps': 0, 'unique_services': 0, 'unique_countries': 0, 'recent_otps': []}
    
    async def get_all_users(self) -> list:
        """Get all users who have used the bot"""
        try:
            if self.supabase:
                result = self.supabase.table('user_sessions').select('user_id').execute()
                return list(set([session['user_id'] for session in result.data]))
            return []
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    def get_country_numbers(self, country: str) -> List[str]:
        """Get all numbers from a country XLSX file"""
        try:
            xlsx_file = os.path.join(self.countries_dir, f"{country}.xlsx")
            numbers = []
            
            # Read Excel file using pandas
            df = pd.read_excel(xlsx_file)
            
            # Get first column (assuming phone numbers are in first column)
            for value in df.iloc[:, 0]:
                if pd.notna(value):  # Skip NaN values
                    # Convert to string and handle scientific notation
                    number = str(int(float(value))) if str(value).replace('.', '').replace('e', '').replace('+', '').replace('-', '').isdigit() else str(value)
                    
                    # Clean the number (remove any non-digit characters except +)
                    clean_number = ''.join(c for c in number if c.isdigit() or c == '+')
                    
                    if len(clean_number) > 5:  # Valid phone number length
                        numbers.append(clean_number)
            
            logger.info(f"📞 Loaded {len(numbers)} numbers for {country}")
            return numbers
            
        except Exception as e:
            logger.error(f"❌ Error loading numbers for {country}: {e}")
            return []
    
    def is_number_in_cooldown(self, number: str) -> bool:
        """Check if number is in 3-day cooldown period"""
        try:
            if not self.supabase:
                return False
                
            result = self.supabase.table('otp_cooldown').select('*').eq('number', number).gte('cooldown_until', datetime.now().isoformat()).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error checking cooldown: {e}")
            return False
    
    def is_number_currently_assigned(self, number: str) -> bool:
        """Check if number is currently assigned to another user"""
        try:
            if not self.supabase:
                return False
                
            result = self.supabase.table('number_assignments').select('*').eq('number', number).eq('is_active', True).gte('expires_at', datetime.now().isoformat()).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error checking assignment: {e}")
            return False
    
    def assign_number_to_user(self, user_id: int, number: str, country: str) -> bool:
        """Assign number to user with concurrent protection"""
        try:
            if not self.supabase:
                return False
            
            # Double-check availability with database lock
            if self.is_number_currently_assigned(number):
                return False
            
            # Check cooldown
            if self.is_number_in_cooldown(number):
                return False
            
            # Deactivate any existing assignments for this user
            self.supabase.table('number_assignments').update({'is_active': False}).eq('user_id', user_id).eq('is_active', True).execute()
            
            # Create new assignment
            assignment_data = {
                'user_id': user_id,
                'number': number,
                'country': country,
                'assigned_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),  # 24 hour assignment
                'is_active': True
            }
            
            result = self.supabase.table('number_assignments').insert(assignment_data).execute()
            
            if result.data:
                logger.info(f"✅ Number {number} assigned to user {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to assign number {number} to user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error assigning number: {e}")
            return False

    def get_next_available_number(self, country: str, user_id: int) -> Optional[str]:
        """Get next available number for a user with concurrent protection and cooldown check"""
        try:
            numbers = self.get_country_numbers(country)
            if not numbers:
                return None
            
            # Shuffle numbers to distribute load and avoid conflicts
            import random
            random.shuffle(numbers)
            
            # Find available number
            for number in numbers:
                # Check if number is in cooldown
                if self.is_number_in_cooldown(number):
                    logger.info(f"⏰ Number {number} is in cooldown, skipping")
                    continue
                
                # Try to assign this number (with concurrent protection)
                if self.assign_number_to_user(user_id, number, country):
                    logger.info(f"📱 Successfully assigned {number} from {country} to user {user_id}")
                    return number
                else:
                    logger.info(f"🔒 Number {number} already assigned, trying next")
            
            logger.warning(f"⚠️ No available numbers for {country} (all in use or cooldown)")
            return None  # No available numbers
            
        except Exception as e:
            logger.error(f"❌ Error getting available number: {e}")
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
            reply_markup=reply_markup
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
            "🌍 Choose a Country:\n\nSelect a country to get a phone number:",
            reply_markup=reply_markup
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
                f"❌ Sorry, no numbers available for {country} right now.\n\nTry another country or contact support."
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
        
        # Get both formatted and copy-friendly versions
        formatted_display = self.format_phone_number(number, country)
        copy_friendly = self.get_copy_friendly_number(number)
        
        message_text = f"""📱 **Your Number Assigned Successfully!**

🌍 **Country:** {country}
📞 **Display:** {formatted_display}
📋 **Copy Number:** `{copy_friendly}`
⏰ **Assigned:** {datetime.now().strftime('%H:%M:%S')}

🎯 **Status:** ✅ Waiting for OTP...
⚡ **Auto-Notification:** You'll receive OTP codes instantly!

💡 **Instructions:**
• Click the number above to copy it
• OTP will arrive within 1-2 minutes
• Keep this number active for more OTPs

🔔 **Real-time alerts enabled!**
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
        
        # Get both formatted and copy-friendly versions
        formatted_display = self.format_phone_number(new_number, country)
        copy_friendly = self.get_copy_friendly_number(new_number)
        
        message_text = f"""🔄 **Number Changed Successfully!**

🌍 **Country:** {country}
📞 **Display:** {formatted_display}
📋 **Copy Number:** `{copy_friendly}`
⏰ **Changed At:** {datetime.now().strftime('%H:%M:%S')}

🎯 **Status:** ✅ Waiting for OTP...
⚡ **Auto-Notification:** You'll receive OTP codes instantly!

💡 **Instructions:**
• Click the number above to copy it
• Use this number to receive OTP codes
• Get instant notifications when OTP arrives
"""
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Save updated session
        await self.save_user_session(user_id, self.user_sessions[user_id])
    
    async def show_user_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user current status with OTP statistics"""
        user_id = update.effective_user.id
        
        # Get OTP statistics
        otp_stats = await self.get_user_otp_stats(user_id)
        
        # Current session info
        session_info = ""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            assigned_time = datetime.fromisoformat(session['assigned_at'])
            duration = datetime.now() - assigned_time
            
            # Get copy-friendly version of the current number
            copy_friendly = self.get_copy_friendly_number(session['number'])
            formatted_display = self.format_phone_number(session['number'])
            
            session_info = f"""
🌍 **Current Country:** {session['country']}
📞 **Display:** {formatted_display}
📋 **Copy Number:** `{copy_friendly}`
⏰ **Assigned:** {assigned_time.strftime('%Y-%m-%d %H:%M:%S')}
⌛ **Duration:** {str(duration).split('.')[0]}
🎯 **Status:** {'🟢 Waiting for OTP' if session['waiting_for_otp'] else '🔴 Inactive'}
"""
        else:
            session_info = "\n❌ **No active number assigned.**\n📱 Click 'Get Number' to start!"
        
        # OTP Statistics
        stats_info = f"""
📊 **OTP Statistics:**
🔢 **Total OTPs Received:** {otp_stats['total_otps']}
🌍 **Countries Used:** {otp_stats['unique_countries']}
💬 **Services Used:** {otp_stats['unique_services']}
"""
        
        # Recent OTPs
        recent_info = ""
        if otp_stats['recent_otps']:
            recent_info = "\n🕒 **Recent OTPs:**\n"
            for i, otp in enumerate(otp_stats['recent_otps'][:3], 1):
                received_time = datetime.fromisoformat(otp['received_at'].replace('Z', '+00:00')).strftime('%m-%d %H:%M')
                recent_info += f"{i}. {otp['service']} - `{otp['otp_code']}` ({received_time})\n"
        
        # Last activity
        last_activity = ""
        if otp_stats['last_otp_at']:
            last_time = datetime.fromisoformat(otp_stats['last_otp_at'].replace('Z', '+00:00'))
            time_diff = datetime.now().replace(tzinfo=last_time.tzinfo) - last_time
            if time_diff.days > 0:
                last_activity = f"\n⏰ **Last OTP:** {time_diff.days} days ago"
            else:
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds % 3600) // 60
                if hours > 0:
                    last_activity = f"\n⏰ **Last OTP:** {hours}h {minutes}m ago"
                else:
                    last_activity = f"\n⏰ **Last OTP:** {minutes}m ago"
        
        status_message = f"""
📊 **Your Status & Statistics:**
{session_info}
{stats_info}{last_activity}{recent_info}
💡 **Tip:** OTP codes are delivered instantly and tracked automatically!
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
        
        await update.message.reply_text(help_text)
    
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to broadcast message to all users"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Check if message provided
        if not context.args:
            await update.message.reply_text(
                "📢 **Admin Broadcast Usage:**\n\n"
                "`/broadcast Your message here`\n\n"
                "This will send your message to all bot users."
            )
            return
        
        # Get message
        broadcast_message = " ".join(context.args)
        
        # Get all users
        all_users = await self.get_all_users()
        
        if not all_users:
            await update.message.reply_text("❌ No users found to broadcast to.")
            return
        
        # Confirm broadcast
        await update.message.reply_text(
            f"📢 **Broadcasting to {len(all_users)} users...**\n\n"
            f"**Message:**\n{broadcast_message}"
        )
        
        # Send to all users
        success_count = 0
        failed_count = 0
        
        app = Application.builder().token(self.bot_token).build()
        
        for target_user in all_users:
            try:
                admin_message = f"""
📢 **Admin Message**

{broadcast_message}

---
From: TaskTreasure Support Team
"""
                await app.bot.send_message(
                    chat_id=target_user,
                    text=admin_message
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send to user {target_user}: {e}")
        
        # Report results
        await update.message.reply_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"📤 **Sent:** {success_count} users\n"
            f"❌ **Failed:** {failed_count} users\n"
            f"👥 **Total:** {len(all_users)} users"
        )
    
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to show bot statistics"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        try:
            # Get overall stats
            if self.supabase:
                total_users_result = self.supabase.table('user_sessions').select('user_id', count='exact').execute()
                total_otps_result = self.supabase.table('otp_history').select('id', count='exact').execute()
                active_sessions_result = self.supabase.table('user_sessions').select('id', count='exact').eq('waiting_for_otp', True).execute()
                
                total_users = total_users_result.count
                total_otps = total_otps_result.count
                active_sessions = active_sessions_result.count
                
                # Get country distribution
                country_stats = {}
                for country in self.available_countries:
                    assigned_count = len(self.assigned_numbers.get(country, set()))
                    total_numbers = len(self.get_country_numbers(country))
                    country_stats[country] = f"{assigned_count}/{total_numbers}"
                
                stats_message = f"""
🔧 **Admin Dashboard - Bot Statistics**

👥 **Users:**
📊 Total Users: {total_users}
🟢 Active Sessions: {active_sessions}
📱 Numbers Assigned: {sum(len(nums) for nums in self.assigned_numbers.values())}

📊 **OTP Statistics:**
🔢 Total OTPs Processed: {total_otps}
⚡ Average per User: {total_otps / max(total_users, 1):.1f}

🌍 **Country Usage:**
"""
                
                for country, usage in country_stats.items():
                    stats_message += f"📂 {country}: {usage}\n"
                
                stats_message += f"""
💾 **System Status:**
✅ Supabase: Connected
✅ Countries: {len(self.available_countries)} loaded
✅ Number Management: Active
✅ OTP Tracking: Enabled

🔧 **Admin ID:** {self.admin_user_id}
"""
                
                await update.message.reply_text(stats_message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting stats: {e}")
            logger.error(f"Admin stats error: {e}")
    
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
                "🤖 Please use the menu buttons below or type /start to begin."
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
            # For callback queries, we need to edit the message instead
            keyboard = [
                [KeyboardButton("📱 Get Number"), KeyboardButton("🔄 Change Number")],
                [KeyboardButton("📊 My Status"), KeyboardButton("ℹ️ Help")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            welcome_message = f"""
🤖 **Welcome to TaskTreasure OTP Bot** 🤖

🎯 **What I can do:**
📱 **Get Number** - Choose country and get a phone number
🔄 **Change Number** - Get a different number  
📊 **My Status** - Check your current number status
⚡ **Auto OTP** - Receive OTP codes instantly

🌍 **Available Countries:** {len(self.available_countries)}
🔢 **Total Numbers:** 1000+

**Choose an option from the menu below:**
"""
            
            await query.edit_message_text(
                welcome_message
            )
    
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
    
    async def send_to_channel(self, message: str):
        """Send message to Telegram channel"""
        try:
            if hasattr(self, 'application') and self.application:
                await self.application.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info("📢 Message sent to channel")
            else:
                logger.warning("⚠️ Bot application not initialized, cannot send to channel")
        except Exception as e:
            logger.error(f"❌ Channel send error: {e}")

    async def notify_user_otp(self, number: str, otp_code: str, service: str, full_message: str):
        """Notify user when OTP arrives for their number"""
        try:
            logger.info(f"🔍 NOTIFICATION DEBUG: Searching for user with number {number}")
            logger.info(f"🔍 ACTIVE SESSIONS: {len(self.user_sessions)} total")
            
            # Debug: Log all active sessions
            for user_id, session in self.user_sessions.items():
                session_number = session.get('number')
                waiting = session.get('waiting_for_otp')
                logger.info(f"🔍 USER {user_id}: number={session_number}, waiting={waiting}")
            
            # Find user with this number
            target_user = None
            target_country = None
            
            # Try exact match first
            for user_id, session in self.user_sessions.items():
                session_number = session.get('number')
                if session_number == number and session.get('waiting_for_otp'):
                    target_user = user_id
                    target_country = session.get('country', 'Unknown')
                    logger.info(f"✅ EXACT MATCH: User {user_id} found for number {number}")
                    break
            
            # Try fuzzy match (remove formatting)
            if not target_user:
                clean_incoming = re.sub(r'[^\d+]', '', number)
                logger.info(f"🔍 FUZZY SEARCH: Cleaned incoming number: {clean_incoming}")
                
                for user_id, session in self.user_sessions.items():
                    session_number = session.get('number', '')
                    clean_session = re.sub(r'[^\d+]', '', session_number)
                    if clean_session == clean_incoming and session.get('waiting_for_otp'):
                        target_user = user_id
                        target_country = session.get('country', 'Unknown')
                        logger.info(f"✅ FUZZY MATCH: User {user_id} found. Session: {session_number} → {clean_session}")
                        break
            
            if not target_user:
                logger.warning(f"❌ NO USER FOUND: No user waiting for OTP on number {number}")
                logger.warning(f"❌ Available numbers: {[s.get('number') for s in self.user_sessions.values()]}")
                return
            
            # Log OTP in history for statistics
            await self.log_otp_received(target_user, number, target_country, service, otp_code, full_message)
            
            # Send notification to user
            app = Application.builder().token(self.bot_token).build()
            
            # Get copy-friendly number for notifications  
            copy_friendly = self.get_copy_friendly_number(number)
            
            notification_text = f"""🔔 **OTP Received**

📞 Number: `{copy_friendly}`
🔐 OTP: `{otp_code}`
💬 Service: {service}"""
            
            await app.bot.send_message(
                chat_id=target_user,
                text=notification_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ USER NOTIFICATION SENT: User {target_user} notified about OTP {otp_code}")
            
            logger.info(f"✅ Notified user {target_user} about OTP {otp_code} for number {number} - Logged to history")
            
        except Exception as e:
            logger.error(f"❌ Error notifying user: {e}")
    
    async def run_bot(self):
        """Run the Telegram bot"""
        try:
            # Create application
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("broadcast", self.admin_broadcast))
            app.add_handler(CommandHandler("stats", self.admin_stats))
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
