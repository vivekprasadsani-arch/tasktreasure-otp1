#!/usr/bin/env python3
"""
Simple OTP Bot using requests (NO BROWSER NEEDED)
- Render compatible (no system dependencies)
- Fast login and monitoring
- Direct HTTP requests
"""

import asyncio
import logging
import os
import re
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleRequestsOTPBot:
    def __init__(self):
        # Website credentials
        self.login_url = "http://94.23.120.156/ints/login"
        self.sms_url = "http://94.23.120.156/ints/client/SMSCDRStats"
        self.username = "Roni_dada"
        self.password = "Roni_dada"
        
        # Session for persistent cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # State management
        self.logged_in = False
        self.processed_hashes = set()
        self.last_check_time = 0
        self.failure_count = 0
        self.max_hashes = 1000
        
        # Initialize number bot
        try:
            from telegram_number_bot import TelegramNumberBot
            self.number_bot = TelegramNumberBot()
            logger.info("✅ Number bot ready for user notifications")
        except Exception as e:
            logger.warning(f"⚠️ Number bot not available: {e}")
            self.number_bot = None
    
    def login_once(self) -> bool:
        """Login once using requests"""
        try:
            logger.info("🔐 Logging in with requests...")
            
            # Get login page first
            response = self.session.get(self.login_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ Login page failed: {response.status_code}")
                return False
            
            # Parse the page for form and captcha
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"Login page title: {soup.title.string if soup.title else 'No title'}")
            
            # Find the login form
            form = soup.find('form')
            if not form:
                logger.error("❌ No form found on login page")
                return False
            
            # Get form action and method
            form_action = form.get('action', '')
            form_method = form.get('method', 'post').lower()
            logger.info(f"Form action: {form_action}, method: {form_method}")
            
            # Collect all form fields
            login_data = {}
            for input_field in form.find_all(['input', 'select', 'textarea']):
                field_name = input_field.get('name')
                field_type = input_field.get('type', 'text')
                field_value = input_field.get('value', '')
                
                if field_name:
                    login_data[field_name] = field_value
                    logger.info(f"Found form field: {field_name} = '{field_value}' (type: {field_type})")
            
            # Override with our credentials
            login_data['username'] = self.username
            login_data['password'] = self.password
            
            # Solve captcha - try multiple approaches
            captcha_answer = ""
            
            # Approach 1: Find label for captcha
            captcha_label = soup.find('label', {'for': 'capt'})
            if captcha_label:
                captcha_text = captcha_label.get_text()
                logger.info(f"Found captcha label: {captcha_text}")
                match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                if match:
                    captcha_answer = str(int(match.group(1)) + int(match.group(2)))
                    logger.info(f"✅ Captcha solved: {captcha_text} = {captcha_answer}")
            
            # Approach 2: Search entire page for captcha
            if not captcha_answer:
                page_text = response.text
                captcha_matches = re.findall(r'(\d+)\s*\+\s*(\d+)', page_text)
                if captcha_matches:
                    nums = captcha_matches[0]
                    captcha_answer = str(int(nums[0]) + int(nums[1]))
                    logger.info(f"✅ Captcha found in page: {nums[0]} + {nums[1]} = {captcha_answer}")
            
            if captcha_answer:
                login_data['capt'] = captcha_answer
            else:
                logger.warning("⚠️ No captcha found, proceeding without it")
            
            # Add common form headers
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.login_url,
                'Origin': 'http://94.23.120.156'
            }
            
            # Determine correct submit URL
            if form_action:
                if form_action.startswith('http'):
                    submit_url = form_action
                else:
                    # Relative URL - construct full URL
                    base_url = "http://94.23.120.156/ints/"
                    submit_url = base_url + form_action.lstrip('/')
            else:
                submit_url = self.login_url
            
            logger.info(f"Submitting to: {submit_url}")
            
            # Submit login
            login_response = self.session.post(
                submit_url, 
                data=login_data,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )
            
            # Check if login successful
            logger.info(f"Login response URL: {login_response.url}")
            logger.info(f"Login response status: {login_response.status_code}")
            
            # Multiple success checks
            success_indicators = [
                "client" in login_response.url and "login" not in login_response.url,
                "SMSCDRStats" in login_response.text,
                "Dashboard" in login_response.text,
                "welcome" in login_response.text.lower(),
                "logout" in login_response.text.lower()
            ]
            
            if any(success_indicators):
                logger.info("✅ Login successful - found success indicator")
                self.logged_in = True
                return True
            else:
                # Check for specific error messages
                response_text = login_response.text.lower()
                if "captcha verification failed" in response_text:
                    logger.error("❌ Login failed - CAPTCHA verification failed")
                    logger.info("🔧 SOLUTION NEEDED: Website may have changed captcha system")
                elif "username/password invalid" in response_text:
                    logger.error("❌ Login failed - Invalid credentials")
                    logger.info("🔧 SOLUTION NEEDED: Please check username/password")
                elif "error" in response_text or "invalid" in response_text:
                    logger.error("❌ Login failed - error message detected")
                else:
                    logger.error(f"❌ Login failed - no success indicators found")
                    logger.info(f"Response preview: {login_response.text[:200]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    def check_for_messages(self) -> List[Dict]:
        """Check for messages using requests"""
        try:
            if not self.logged_in:
                return []
            
            # Get SMS page
            response = self.session.get(self.sms_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"⚠️ SMS page failed: {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find SMS table
            table = soup.find('table')
            if not table:
                logger.warning("⚠️ No table found on SMS page")
                return []
            
            messages = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        # Extract message data
                        timestamp = cells[0].get_text(strip=True)
                        number = cells[1].get_text(strip=True)
                        service = cells[2].get_text(strip=True)
                        message = cells[3].get_text(strip=True)
                        
                        if message and len(message) > 10:  # Valid message
                            messages.append({
                                'timestamp': timestamp,
                                'number': number,
                                'service': service,
                                'message': message
                            })
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Row parse error: {parse_error}")
                        continue
            
            logger.info(f"📊 Found {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Message check error: {e}")
            self.failure_count += 1
            return []
    
    def extract_otp_data(self, message_data: Dict) -> Optional[Dict]:
        """Extract OTP from message"""
        try:
            message = message_data['message']
            
            # Find OTP code (4-8 digits)
            otp_patterns = [
                r'\b(\d{4,8})\b',
                r'code[:\s]+(\d{4,8})',
                r'verification[:\s]+(\d{4,8})',
                r'OTP[:\s]+(\d{4,8})'
            ]
            
            otp_code = None
            for pattern in otp_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    otp_code = match.group(1)
                    break
            
            if otp_code:
                return {
                    'otp_code': otp_code,
                    'service': message_data['service'],
                    'number': message_data['number'],
                    'message': message,
                    'timestamp': message_data['timestamp']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ OTP extraction error: {e}")
            return None
    
    def get_message_hash(self, message: str) -> str:
        """Generate hash for message"""
        return hashlib.md5(message.encode()).hexdigest()[:16]
    
    async def notify_user_otp(self, otp_data: Dict):
        """Notify users about new OTP"""
        try:
            if not self.number_bot:
                return
            
            # Channel notification
            channel_message = f"🔔 **OTP Received**\n\n📱 Service: {otp_data['service']}\n🔢 Code: `{otp_data['otp_code']}`\n📞 Number: {otp_data['number']}\n⏰ Time: {otp_data['timestamp']}"
            
            await self.number_bot.send_to_channel(channel_message)
            logger.info(f"📢 Channel notified: {otp_data['otp_code']}")
            
            # Individual user notifications
            await self.number_bot.notify_user_otp(otp_data)
            
        except Exception as e:
            logger.error(f"❌ User notification error: {e}")
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("🚀 SIMPLE REQUESTS OTP BOT STARTING...")
        
        while True:
            try:
                # Login if needed
                if not self.logged_in:
                    if not self.login_once():
                        logger.error("❌ Login failed, retrying in 30 seconds...")
                        await asyncio.sleep(30)
                        continue
                
                # Check for messages
                messages = self.check_for_messages()
                
                if messages:
                    new_otps = 0
                    for msg in messages:
                        otp_data = self.extract_otp_data(msg)
                        if otp_data:
                            msg_hash = self.get_message_hash(otp_data['message'])
                            if msg_hash not in self.processed_hashes:
                                # New OTP found
                                self.processed_hashes.add(msg_hash)
                                new_otps += 1
                                
                                logger.info(f"⚡ NEW OTP: {otp_data['otp_code']} → {otp_data['service']} ({otp_data['number']})")
                                
                                # Notify users
                                await self.notify_user_otp(otp_data)
                    
                    if new_otps == 0:
                        logger.info(f"📊 Checked {len(messages)} messages - no new OTPs")
                    
                    # Cleanup old hashes
                    if len(self.processed_hashes) > self.max_hashes:
                        old_hashes = list(self.processed_hashes)[:500]
                        for old_hash in old_hashes:
                            self.processed_hashes.remove(old_hash)
                        logger.info("🧹 Cleaned old message hashes")
                
                # Reset failure count on success
                self.failure_count = 0
                
                # Wait before next check
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                self.failure_count += 1
                
                # Re-login after 10 consecutive failures
                if self.failure_count >= 10:
                    logger.warning("🔄 Too many failures, forcing re-login...")
                    self.logged_in = False
                    self.failure_count = 0
                
                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = SimpleRequestsOTPBot()
    asyncio.run(bot.run())
