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
import shutil
import tempfile
import requests
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
        
        # Store bot application reference for admin notifications
        self.application = None
        
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
        """Load admin settings from environment variable or database"""
        try:
            # First try to load from environment variable (for Render deployment)
            admin_user_env = os.getenv('ADMIN_USER_ID')
            if admin_user_env:
                self.admin_user_id = int(admin_user_env)
                logger.info(f"✅ Admin user loaded from environment: {self.admin_user_id}")
            return
            
            # Fallback to database
            if self.supabase:
                result = self.supabase.table('admin_settings').select('setting_value').eq('setting_key', 'admin_user_id').execute()
                if result.data:
                    self.admin_user_id = int(result.data[0]['setting_value'])
                    logger.info(f"✅ Admin user loaded from database: {self.admin_user_id}")
                else:
                    logger.warning("⚠️ No admin user configured in database")
            else:
                logger.warning("⚠️ No admin user configured - neither environment nor database")
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
    
    async def is_user_approved(self, user_id: int) -> bool:
        """Check if user is approved to use the bot"""
        try:
            if self.is_admin(user_id):
            return True
            
            if not self.supabase:
            return False
            
            result = self.supabase.table('approved_users').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error checking user approval: {e}")
            return False
    
    async def check_request_cooldown(self, user_id: int) -> Optional[datetime]:
        """Check if user is in cooldown period, returns cooldown end time if in cooldown"""
        try:
            if not self.supabase:
            return None
            
            result = self.supabase.table('user_approval_requests').select('next_request_allowed_at').eq('user_id', user_id).execute()
            if result.data:
                cooldown_end = datetime.fromisoformat(result.data[0]['next_request_allowed_at'].replace('Z', '+00:00'))
                if cooldown_end > datetime.now():
                return cooldown_end
            return None
        except Exception as e:
            logger.error(f"❌ Error checking request cooldown: {e}")
            return None
    
    async def create_approval_request(self, user_id: int, user_data: dict):
        """Create a new approval request"""
        try:
            if not self.supabase:
            return False
            
            # Set next allowed request time (3 hours from now)
            next_allowed = datetime.now() + timedelta(hours=3)
            
            request_data = {
                'user_id': user_id,
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'status': 'pending',
                'next_request_allowed_at': next_allowed.isoformat()
            }
            
            # Upsert the request
            result = self.supabase.table('user_approval_requests').upsert(request_data, on_conflict='user_id').execute()
            logger.info(f"📝 Created approval request for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating approval request: {e}")
            return False
    
    async def notify_admin_new_request(self, user_id: int, user_data: dict):
        """Notify admin about new user request"""
        try:
            logger.info(f"🔔 Attempting to notify admin about user {user_id} request")
            logger.info(f"🔧 Admin user ID: {self.admin_user_id}")
            logger.info(f"🔧 Application available: {self.application is not None}")
            
            if not self.admin_user_id:
                logger.error("❌ Admin user ID not set - cannot send notification")
            return
                
            if not self.application:
                logger.error("❌ Bot application not available - cannot send notification")
            return
            
            # Escape HTML special characters
            def escape_html(text):
                if not text:
                return "N/A"
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            first_name = escape_html(user_data.get('first_name', 'N/A'))
            last_name = escape_html(user_data.get('last_name', ''))
            username = escape_html(user_data.get('username', ''))
            
            user_info = f"👤 <b>New User Request</b>\n\n"
            user_info += f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            user_info += f"👤 <b>Name:</b> {first_name}"
            if last_name:
                user_info += f" {last_name}"
            user_info += "\n"
            if username:
                user_info += f"🔤 <b>Username:</b> @{username}\n"
            user_info += f"⏰ <b>Requested:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            user_info += "<b>Choose an action:</b>"
            
            # Create inline keyboard for admin actions
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.send_message(
                chat_id=self.admin_user_id,
                text=user_info,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            logger.info(f"✅ Successfully notified admin {self.admin_user_id} about user {user_id} request")
        except Exception as e:
            logger.error(f"❌ Error notifying admin with HTML: {e}")
            
            # Fallback: try without formatting
            try:
                simple_message = f"""👤 New User Request

🆔 User ID: {user_id}
👤 Name: {user_data.get('first_name', 'N/A')} {user_data.get('last_name', '')}
🔤 Username: @{user_data.get('username', 'N/A')}
⏰ Requested: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Choose an action:"""
                
                    keyboard = [
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.application.bot.send_message(
                    chat_id=self.admin_user_id,
                    text=simple_message,
                    reply_markup=reply_markup
                )
                logger.info(f"✅ Fallback notification sent to admin {self.admin_user_id}")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback notification also failed: {fallback_error}")
                logger.error(f"❌ Admin ID: {self.admin_user_id}, App available: {self.application is not None}")
    
    async def approve_user(self, user_id: int, admin_id: int):
        """Approve user access"""
        try:
            if not self.supabase:
            return False
            
            # Get user request data
            request_result = self.supabase.table('user_approval_requests').select('*').eq('user_id', user_id).execute()
            if not request_result.data:
            return False
            
            request_data = request_result.data[0]
            
            # Add to approved users
            approved_data = {
                'user_id': user_id,
                'username': request_data.get('username'),
                'first_name': request_data.get('first_name'),
                'last_name': request_data.get('last_name'),
                'approved_by': admin_id
            }
            self.supabase.table('approved_users').upsert(approved_data, on_conflict='user_id').execute()
            
            # Update request status
            self.supabase.table('user_approval_requests').update({
                'status': 'approved',
                'approved_at': datetime.now().isoformat(),
                'approved_by': admin_id
            }).eq('user_id', user_id).execute()
            
            logger.info(f"✅ User {user_id} approved by admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error approving user: {e}")
            return False
    
    async def reject_user(self, user_id: int, admin_id: int, reason: str = "Request rejected"):
        """Reject user access"""
        try:
            if not self.supabase:
            return False
            
            # Update request status
            self.supabase.table('user_approval_requests').update({
                'status': 'rejected',
                'approved_by': admin_id,
                'rejection_reason': reason
            }).eq('user_id', user_id).execute()
            
            logger.info(f"❌ User {user_id} rejected by admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error rejecting user: {e}")
            return False
    
    async def notify_user_approval_result(self, user_id: int, approved: bool, reason: str = None):
        """Notify user about approval/rejection result"""
        try:
            if not self.application:
            return
            
            if approved:
                message = """
🎉 <b>Congratulations!</b> 🎉

✅ Your request has been <b>APPROVED</b> by admin!

You can now use the bot to get phone numbers and receive OTP codes.

<b>Available Commands:</b>
📱 Get Number - Choose country and get a phone number
🔄 Change Number - Get a different number  
📊 My Status - Check your current number status

<b>Choose an option from the menu below:</b>
"""
                # Create main menu keyboard
                    keyboard = [
                    [KeyboardButton("📱 Get Number"), KeyboardButton("🔄 Change Number")],
                    [KeyboardButton("📊 My Status"), KeyboardButton("ℹ️ Help")]
                ]
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            else:
                reason_escaped = reason.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if reason else 'No specific reason provided'
                message = f"""
😔 <b>Request Rejected</b> 😔

❌ Your access request has been <b>REJECTED</b> by admin.

<b>Reason:</b> {reason_escaped}

⏰ You can submit a new request after <b>3 hours</b> from your last request.

If you believe this is a mistake, please contact the administrator.
"""
                reply_markup = None
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            logger.info(f"📧 Notified user {user_id} about {'approval' if approved else 'rejection'}")
        except Exception as e:
            logger.error(f"❌ Error notifying user: {e}")
    
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
        """Handle /start command with approval system"""
        user_id = update.effective_user.id
        user = update.effective_user
        user_name = user.first_name or "User"
        
        logger.info(f"👤 User {user_name} ({user_id}) started the bot")
        
        # Check if user is approved
        if await self.is_user_approved(user_id):
            # User is approved, show main menu
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
            return
        
        # Check if user is in cooldown
        cooldown_end = await self.check_request_cooldown(user_id)
        if cooldown_end:
            cooldown_remaining = cooldown_end - datetime.now()
            hours = int(cooldown_remaining.total_seconds() // 3600)
            minutes = int((cooldown_remaining.total_seconds() % 3600) // 60)
            
            cooldown_message = f"""
⏰ **Request Cooldown Active** ⏰

You have recently submitted an access request.

⏳ **Time Remaining:** {hours}h {minutes}m

You can submit a new request after the cooldown period ends.

**Cooldown End:** {cooldown_end.strftime('%Y-%m-%d %H:%M:%S')}

Please wait and try again later.
"""
                await update.message.reply_text(cooldown_message)
            return
        
        # User is not approved and not in cooldown - show request access option
            keyboard = [
            [KeyboardButton("🔑 Request Access")],
            [KeyboardButton("ℹ️ Help")]
        ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        request_message = f"""
🤖 **Welcome to TaskTreasure OTP Bot** 🤖

Hi {user_name}! 👋

🔐 **Access Required**

To use this bot, you need admin approval first.

📝 **How it works:**
1️⃣ Click "🔑 Request Access" below
2️⃣ Your request will be sent to admin
3️⃣ Admin will approve/reject your request
4️⃣ You'll get notified about the decision

⏰ **Note:** After submitting a request, you must wait 3 hours before submitting another request.

**Click the button below to request access:**
"""
        
            await update.message.reply_text(
            request_message,
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
    
    async def admin_approve_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to approve a user"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if len(context.args) != 1:
                    await update.message.reply_text("Usage: /approve <user_id>")
            return
            
            user_id_to_approve = int(context.args[0])
            admin_id = update.effective_user.id
            
            if await self.approve_user(user_id_to_approve, admin_id):
                await self.notify_user_approval_result(user_id_to_approve, True)
                    await update.message.reply_text(f"✅ User {user_id_to_approve} has been approved successfully!")
                logger.info(f"✅ Admin {admin_id} approved user {user_id_to_approve} via command")
            else:
                    await update.message.reply_text("❌ Error approving user. User may not exist or already approved.")
        except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin approve error: {e}")
    
    async def admin_reject_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to reject a user"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if len(context.args) < 1:
                    await update.message.reply_text("Usage: /reject <user_id> [reason]")
            return
            
            user_id_to_reject = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Request rejected by admin"
            admin_id = update.effective_user.id
            
            if await self.reject_user(user_id_to_reject, admin_id, reason):
                await self.notify_user_approval_result(user_id_to_reject, False, reason)
                    await update.message.reply_text(f"❌ User {user_id_to_reject} has been rejected.\nReason: {reason}")
                logger.info(f"❌ Admin {admin_id} rejected user {user_id_to_reject} via command")
            else:
                    await update.message.reply_text("❌ Error rejecting user. User may not exist.")
        except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin reject error: {e}")
    
    async def admin_remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to remove an approved user"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if len(context.args) != 1:
                    await update.message.reply_text("Usage: /remove <user_id>")
            return
            
            user_id_to_remove = int(context.args[0])
            
            if not self.supabase:
                    await update.message.reply_text("❌ Database connection error.")
            return
            
            # Deactivate user
            result = self.supabase.table('approved_users').update({
                'is_active': False
            }).eq('user_id', user_id_to_remove).execute()
            
            if result.data:
                    await update.message.reply_text(f"✅ User {user_id_to_remove} has been removed from approved users.")
                logger.info(f"🗑️ Admin {update.effective_user.id} removed user {user_id_to_remove}")
                
                # Notify user
                try:
                    if self.application:
                        await self.application.bot.send_message(
                            chat_id=user_id_to_remove,
                            text="""
🚫 **Access Revoked** 🚫

Your access to the TaskTreasure OTP Bot has been revoked by admin.

You will no longer be able to use the bot's features.

If you believe this is a mistake, please contact the administrator.
"""
                        )
                except Exception:
                    pass  # User may have blocked the bot
            else:
                    await update.message.reply_text("❌ User not found in approved users list.")
        except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin remove error: {e}")
    
    async def admin_list_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list pending approval requests"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if not self.supabase:
                    await update.message.reply_text("❌ Database connection error.")
            return
            
            # Get pending requests
            result = self.supabase.table('user_approval_requests').select('*').eq('status', 'pending').order('requested_at', desc=True).execute()
            
            if not result.data:
                    await update.message.reply_text("📝 No pending approval requests.")
            return
            
            message = "📋 **Pending Approval Requests:**\n\n"
            for i, req in enumerate(result.data[:10], 1):  # Limit to 10 requests
                user_id = req['user_id']
                name = req.get('first_name', 'N/A')
                if req.get('last_name'):
                    name += f" {req.get('last_name')}"
                username = req.get('username')
                requested_at = datetime.fromisoformat(req['requested_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                
                message += f"**{i}.** ID: `{user_id}`\n"
                message += f"   👤 **Name:** {name}\n"
                if username:
                    message += f"   🔤 **Username:** @{username}\n"
                message += f"   ⏰ **Requested:** {requested_at}\n\n"
            
            if len(result.data) > 10:
                message += f"... and {len(result.data) - 10} more requests\n\n"
            
            message += "Use /approve <user_id> or /reject <user_id> to handle requests."
            
                await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin list requests error: {e}")
    
    async def admin_list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list approved users"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if not self.supabase:
                    await update.message.reply_text("❌ Database connection error.")
            return
            
            # Get approved users
            result = self.supabase.table('approved_users').select('*').eq('is_active', True).order('approved_at', desc=True).execute()
            
            if not result.data:
                    await update.message.reply_text("👥 No approved users found.")
            return
            
            message = f"👥 **Approved Users ({len(result.data)}):**\n\n"
            for i, user in enumerate(result.data[:15], 1):  # Limit to 15 users
                user_id = user['user_id']
                name = user.get('first_name', 'N/A')
                if user.get('last_name'):
                    name += f" {user.get('last_name')}"
                username = user.get('username')
                approved_at = datetime.fromisoformat(user['approved_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                
                message += f"**{i}.** ID: `{user_id}`\n"
                message += f"   👤 **Name:** {name}\n"
                if username:
                    message += f"   🔤 **Username:** @{username}\n"
                message += f"   ✅ **Approved:** {approved_at}\n\n"
            
            if len(result.data) > 15:
                message += f"... and {len(result.data) - 15} more users\n\n"
            
            message += "Use /remove <user_id> to remove a user's access."
            
                await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin list users error: {e}")
    
    async def admin_debug_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to show debug information"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            # Check system status
            debug_info = f"""
🔧 **System Debug Information**

**🔑 Admin Configuration:**
• Admin User ID: `{self.admin_user_id}`
• Environment Variable: `{os.getenv('ADMIN_USER_ID', 'Not Set')}`
• Your User ID: `{update.effective_user.id}`
• Admin Status: {'✅ Verified' if self.is_admin(update.effective_user.id) else '❌ Not Admin'}

**🤖 Bot Application:**
• Application Available: {'✅ Yes' if self.application else '❌ No'}
• Bot Instance: {'✅ Available' if hasattr(self, 'application') and self.application else '❌ Not Available'}

**💾 Database Connection:**
• Supabase Connected: {'✅ Yes' if self.supabase else '❌ No'}
• Database URL: `{self.supabase_url[:30]}...`

**🌍 Countries:**
• Available Countries: {len(self.available_countries)}
• Countries: {', '.join(self.available_countries[:5])}{'...' if len(self.available_countries) > 5 else ''}

**👥 User Sessions:**
• Active Sessions: {len(self.user_sessions)}

**📊 System Status:**
• Bot Running: ✅ Yes
• Notification System: {'✅ Ready' if self.admin_user_id and self.application else '❌ Not Ready'}
"""
            
                await update.message.reply_text(debug_info, parse_mode='Markdown')
            logger.info(f"🔧 Admin {update.effective_user.id} requested debug info")
            
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin debug error: {e}")
    
    def validate_excel_file(self, file_path: str, country_name: str) -> tuple[bool, str, int]:
        """Validate uploaded Excel file format and content"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check if file has required columns (flexible column names)
            required_columns = ['number', 'phone', 'mobile']  # Accept any of these
            column_found = False
            number_column = None
            
            for col in df.columns:
                if col.lower() in required_columns:
                    number_column = col
                    column_found = True
                    break
            
            if not column_found:
            return False, f"Excel file must have a column with phone numbers (e.g., 'number', 'phone', or 'mobile')", 0
            
            # Check if file has data
            if len(df) == 0:
            return False, "Excel file is empty", 0
            
            # Validate phone numbers format
            valid_numbers = 0
            for idx, row in df.iterrows():
                number = str(row[number_column]).strip()
                if number and number != 'nan' and len(number) >= 8:
                    # Basic phone number validation
                    clean_number = re.sub(r'[^\d+]', '', number)
                    if len(clean_number) >= 8:
                        valid_numbers += 1
            
            if valid_numbers == 0:
            return False, "No valid phone numbers found in the file", 0
            
            success_rate = (valid_numbers / len(df)) * 100
            if success_rate < 50:
            return False, f"Too many invalid numbers. Only {success_rate:.1f}% are valid (minimum 50% required)", valid_numbers
            
            return True, f"File validated successfully. Found {valid_numbers} valid numbers out of {len(df)} total.", valid_numbers
            
        except Exception as e:
            return False, f"Error reading Excel file: {str(e)}", 0
    
    def process_country_file(self, file_path: str, country_name: str) -> bool:
        """Process and save country Excel file"""
        try:
            # Ensure Countries directory exists
            os.makedirs(self.countries_dir, exist_ok=True)
            
            # Target file path
            target_path = os.path.join(self.countries_dir, f"{country_name}.xlsx")
            
            # Backup existing file if it exists
            backup_path = None
            if os.path.exists(target_path):
                backup_path = f"{target_path}.backup"
                shutil.copy2(target_path, backup_path)
                logger.info(f"📋 Backed up existing file: {country_name}.xlsx")
            
            # Copy new file
            shutil.copy2(file_path, target_path)
            logger.info(f"📁 Saved new country file: {target_path}")
            
            # Update available countries list
            if country_name not in self.available_countries:
                self.available_countries.append(country_name)
                logger.info(f"🆕 Added new country: {country_name}")
            
            # Initialize number tracking for new country
            if country_name not in self.country_number_indices:
                self.country_number_indices[country_name] = 0
                self.assigned_numbers[country_name] = set()
                logger.info(f"🔢 Initialized number tracking for: {country_name}")
            
            # Remove backup if everything succeeded
            if backup_path and os.path.exists(backup_path):
                os.remove(backup_path)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing country file: {e}")
            
            # Restore backup if something went wrong
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.move(backup_path, target_path)
                    logger.info("🔄 Restored backup file due to error")
                except Exception:
                    pass
            
            return False
    
    async def admin_upload_country(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to upload country file"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
            await update.message.reply_text("""
📁 **Upload Country Numbers File**

To upload a new country or update existing one:

1️⃣ **Prepare Excel File:**
   - File must be in .xlsx format
   - Must contain a column with phone numbers
   - Column can be named: 'number', 'phone', or 'mobile'
   - Numbers should be in international format

2️⃣ **Upload File:**
   - Send the Excel file as a document
   - Add caption with country name (e.g., "Tunisia")
   - Example: Send Tunisia.xlsx with caption "Tunisia"

3️⃣ **File Processing:**
   - Bot will validate the file format
   - Check phone number validity
   - Replace existing file if country exists
   - Add as new country if it doesn't exist

**File Format Example:**
```
number
+21612345678
+21687654321
+21698765432
```

**Send your Excel file now with country name as caption!**
""")
    
    async def admin_list_countries(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to list all available countries"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if not self.available_countries:
                    await update.message.reply_text("📁 No countries available.")
            return
            
            message = f"🌍 **Available Countries ({len(self.available_countries)}):**\n\n"
            
            for i, country in enumerate(sorted(self.available_countries), 1):
                # Get file info
                file_path = os.path.join(self.countries_dir, f"{country}.xlsx")
                if os.path.exists(file_path):
                    # Get file stats
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size / 1024  # KB
                    modified_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    # Count numbers in file
                    try:
                        df = pd.read_excel(file_path)
                        number_count = len(df)
                    except:
                        number_count = "?"
                    
                    # Check current usage
                    assigned_count = len(self.assigned_numbers.get(country, set()))
                    current_index = self.country_number_indices.get(country, 0)
                    
                    message += f"**{i}.** 🇳🇪 **{country}**\n"
                    message += f"   📊 Numbers: {number_count} total, {assigned_count} assigned\n"
                    message += f"   📁 Size: {file_size:.1f} KB\n"
                    message += f"   🕒 Updated: {modified_time}\n"
                    message += f"   📍 Index: {current_index}\n\n"
                else:
                    message += f"**{i}.** ❌ **{country}** (file missing)\n\n"
            
            message += "**Commands:**\n"
            message += "• `/upload` - Upload new country file\n"
            message += "• `/delete_country <name>` - Delete country file\n"
            message += "• `/reload_countries` - Reload country list"
            
                await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin list countries error: {e}")
    
    async def admin_delete_country(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to delete a country file"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            if len(context.args) != 1:
                    await update.message.reply_text("Usage: /delete_country <country_name>")
            return
            
            country_name = context.args[0]
            file_path = os.path.join(self.countries_dir, f"{country_name}.xlsx")
            
            if not os.path.exists(file_path):
                    await update.message.reply_text(f"❌ Country '{country_name}' not found.")
            return
            
            # Check if country has active users
            active_users = 0
            for user_id, session in self.user_sessions.items():
                if session.get('country') == country_name:
                    active_users += 1
            
            if active_users > 0:
                    await update.message.reply_text(f"⚠️ Cannot delete '{country_name}' - {active_users} users are currently using numbers from this country.")
            return
            
            # Create backup before deletion
            backup_path = f"{file_path}.deleted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            
            # Delete file
            os.remove(file_path)
            
            # Remove from available countries
            if country_name in self.available_countries:
                self.available_countries.remove(country_name)
            
            # Clean up tracking data
            if country_name in self.country_number_indices:
                del self.country_number_indices[country_name]
            if country_name in self.assigned_numbers:
                del self.assigned_numbers[country_name]
            
                await update.message.reply_text(f"""
✅ **Country Deleted Successfully**

🗑️ **Country:** {country_name}
📁 **Backup:** {os.path.basename(backup_path)}
🔢 **Available Countries:** {len(self.available_countries)}

The file has been backed up before deletion.
""")
            
            logger.info(f"🗑️ Admin deleted country: {country_name}")
            
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin delete country error: {e}")
    
    async def admin_reload_countries(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to reload countries from files"""
        if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            old_count = len(self.available_countries)
            
            # Reload countries
            self.load_countries()
            self.load_number_states()
            
            new_count = len(self.available_countries)
            
                await update.message.reply_text(f"""
🔄 **Countries Reloaded**

📊 **Before:** {old_count} countries
📊 **After:** {new_count} countries
📈 **Change:** {new_count - old_count:+d}

🌍 **Available Countries:**
{', '.join(sorted(self.available_countries))}
""")
            
            logger.info(f"🔄 Admin reloaded countries: {old_count} → {new_count}")
            
        except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            logger.error(f"Admin reload countries error: {e}")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads (Excel files for countries)"""
        user_id = update.effective_user.id
        
        # Only admin can upload files
        if not self.is_admin(user_id):
                await update.message.reply_text("❌ Only admin can upload country files.")
            return
        
        document = update.message.document
        caption = update.message.caption or ""
        
        # Check if it's an Excel file
        if not document.file_name.endswith(('.xlsx', '.xls')):
                await update.message.reply_text("❌ Please upload an Excel file (.xlsx or .xls)")
            return
        
        # Get country name from caption
        country_name = caption.strip()
        if not country_name:
                await update.message.reply_text("""
❌ **Country Name Required**

Please add the country name as caption when sending the file.

**Example:**
Send Tunisia.xlsx with caption: "Tunisia"
""")
            return
        
        # Validate country name
        if not re.match(r'^[a-zA-Z\s]+$', country_name):
                await update.message.reply_text("❌ Country name should only contain letters and spaces.")
            return
        
        try:
                await update.message.reply_text("📥 **Processing file...** Please wait...")
            
            # Download file
            file = await context.bot.get_file(document.file_id)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Download file content
                file_url = file.file_path
                response = requests.get(file_url)
                temp_file.write(response.content)
            
            # Validate file
            is_valid, message, valid_count = self.validate_excel_file(temp_path, country_name)
            
            if not is_valid:
                os.unlink(temp_path)
                    await update.message.reply_text(f"❌ **File Validation Failed**\n\n{message}")
            return
            
            # Check if country exists
            country_exists = country_name in self.available_countries
            action = "Updated" if country_exists else "Added"
            
            # Process file
            if self.process_country_file(temp_path, country_name):
                    await update.message.reply_text(f"""
✅ **Country {action} Successfully!**

🌍 **Country:** {country_name}
📊 **Numbers:** {valid_count} valid numbers
📁 **File:** {document.file_name}
📈 **Action:** {action} existing country file

🔄 **Status:** Country is now available for users!
""")
                
                logger.info(f"📁 Admin uploaded country file: {country_name} ({valid_count} numbers)")
            else:
                    await update.message.reply_text("❌ Error processing file. Please try again.")
            
            # Clean up temporary file
            os.unlink(temp_path)
            
        except Exception as e:
                await update.message.reply_text(f"❌ Error processing file: {e}")
            logger.error(f"Document upload error: {e}")
            
            # Clean up on error
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text
        user_id = update.effective_user.id
        user = update.effective_user
        
        # Handle access request
        if text == "🔑 Request Access":
            # Check if user is already approved
            if await self.is_user_approved(user_id):
                    await update.message.reply_text("✅ You are already approved! Use /start to access the main menu.")
            return
            
            # Check cooldown
            cooldown_end = await self.check_request_cooldown(user_id)
            if cooldown_end:
                cooldown_remaining = cooldown_end - datetime.now()
                hours = int(cooldown_remaining.total_seconds() // 3600)
                minutes = int((cooldown_remaining.total_seconds() % 3600) // 60)
                
                    await update.message.reply_text(f"⏰ You are in cooldown. Wait {hours}h {minutes}m before requesting again.")
            return
            
            # Create approval request
            user_data = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            
            if await self.create_approval_request(user_id, user_data):
                await self.notify_admin_new_request(user_id, user_data)
                
                    await update.message.reply_text("""
📝 **Access Request Submitted!** 📝

✅ Your request has been sent to the admin for review.

⏰ **What happens next:**
1️⃣ Admin will review your request
2️⃣ You'll receive a notification with the decision
3️⃣ If approved, you can start using the bot
4️⃣ If rejected, you can try again after 3 hours

🕒 **Cooldown:** 3 hours from now

Please wait for admin approval. You will be notified once a decision is made.
""")
            else:
                    await update.message.reply_text("❌ Error submitting request. Please try again later.")
            return
        
        # Check if user is approved for all other commands
        if not await self.is_user_approved(user_id):
                await update.message.reply_text("""
🔐 **Access Required**

You need admin approval to use this bot.

Please click "🔑 Request Access" to submit your request, or use /start to see the request menu.
""")
            return
        
        # Handle approved user commands
        if text == "📱 Get Number":
            await self.show_countries(update, context)
        elif text == "🔄 Change Number":
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
        
        # Handle admin approval/rejection actions
        if query.data.startswith("approve_"):
            user_id_to_approve = int(query.data.split("_")[1])
            admin_id = query.from_user.id
            
            if not self.is_admin(admin_id):
                await query.edit_message_text("❌ You are not authorized to perform this action.")
            return
            
            if await self.approve_user(user_id_to_approve, admin_id):
                await self.notify_user_approval_result(user_id_to_approve, True)
                await query.edit_message_text(f"✅ User {user_id_to_approve} has been **APPROVED** successfully!")
                logger.info(f"✅ Admin {admin_id} approved user {user_id_to_approve}")
            else:
                await query.edit_message_text("❌ Error approving user. Please try again.")
            return
        
        elif query.data.startswith("reject_"):
            user_id_to_reject = int(query.data.split("_")[1])
            admin_id = query.from_user.id
            
            if not self.is_admin(admin_id):
                await query.edit_message_text("❌ You are not authorized to perform this action.")
            return
            
            if await self.reject_user(user_id_to_reject, admin_id, "Request rejected by admin"):
                await self.notify_user_approval_result(user_id_to_reject, False, "Request rejected by admin")
                await query.edit_message_text(f"❌ User {user_id_to_reject} has been **REJECTED**.")
                logger.info(f"❌ Admin {admin_id} rejected user {user_id_to_reject}")
            else:
                await query.edit_message_text("❌ Error rejecting user. Please try again.")
            return
        
        # Check if user is approved for other callback actions
        user_id = query.from_user.id
        if not await self.is_user_approved(user_id):
            await query.edit_message_text("🔐 You need admin approval to use this bot. Please request access first.")
            return
        
        # Handle approved user callback queries
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
            
            # Store application reference for admin notifications
            self.application = app
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("broadcast", self.admin_broadcast))
            app.add_handler(CommandHandler("stats", self.admin_stats))
            
            # Add new admin commands
            app.add_handler(CommandHandler("approve", self.admin_approve_user))
            app.add_handler(CommandHandler("reject", self.admin_reject_user))
            app.add_handler(CommandHandler("remove", self.admin_remove_user))
            app.add_handler(CommandHandler("requests", self.admin_list_requests))
            app.add_handler(CommandHandler("users", self.admin_list_users))
            
            # Add country management commands
            app.add_handler(CommandHandler("upload", self.admin_upload_country))
            app.add_handler(CommandHandler("countries", self.admin_list_countries))
            app.add_handler(CommandHandler("delete_country", self.admin_delete_country))
            app.add_handler(CommandHandler("reload_countries", self.admin_reload_countries))
            
            # Add debug command
            app.add_handler(CommandHandler("debug", self.admin_debug_info))
            
            # Add document handler for file uploads
            app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
            
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            app.add_handler(CallbackQueryHandler(self.handle_callback_query))
            
            logger.info("🤖 Telegram Number Bot starting...")
            
            # Start the bot
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            logger.info("✅ Telegram Number Bot is running with admin approval system!")
            logger.info("📋 User Admin Commands: /approve /reject /remove /requests /users")
            logger.info("🌍 Country Admin Commands: /upload /countries /delete_country /reload_countries")
            logger.info("🔧 Debug Command: /debug - Show system status and configuration")
            
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
