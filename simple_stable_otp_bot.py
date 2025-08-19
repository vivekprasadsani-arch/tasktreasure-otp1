#!/usr/bin/env python3
"""
SIMPLE STABLE OTP BOT
Simple approach: Check for OTP → Send to channel → Notify users
No unnecessary re-login, only restart when actually needed
"""

import asyncio
import logging
import time
import re
import os
import hashlib
from datetime import datetime
from typing import Set, Dict, Any
import json

import requests
from playwright.async_api import async_playwright
import telegram
from telegram.constants import ParseMode
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleOTPBot:
    def __init__(self):
        # Website credentials
        self.username = "Roni_dada"
        self.password = "Roni_dada"
        self.login_url = "http://94.23.120.156/ints/login"
        self.sms_url = "http://94.23.120.156/ints/client/SMSCDRStats"
        
        # Telegram Bot from environment
        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            logger.error("❌ BOT_TOKEN environment variable not set!")
            raise ValueError("BOT_TOKEN environment variable is required")
        self.channel_id = "-1002724043027"
        self.bot = telegram.Bot(token=self.bot_token)
        
        # Supabase
        self.supabase_url = "https://wddcrtrgirhcemmobgcc.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkZGNydHJnaXJoY2VtbW9iZ2NjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjA1NTYsImV4cCI6MjA3MDkzNjU1Nn0.K5vpqoc_zakEwBd96aC-drJ5OoInTSFcrMlWy7ShIyI"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Browser
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Simple tracking
        self.processed_hashes: Set[str] = set()
        self.last_successful_check = datetime.now()
        
        # User notification system
        self.number_bot = None
        self._init_number_bot()
    
    def _init_number_bot(self):
        """Initialize number bot for user notifications"""
        try:
            from telegram_number_bot import TelegramNumberBot
            self.number_bot = TelegramNumberBot()
            logger.info("✅ Number bot ready for user notifications")
        except Exception as e:
            logger.warning(f"⚠️ Number bot not available: {e}")
    
    async def setup_browser(self):
        """Render-compatible browser setup"""
        try:
            logger.info("🌐 Setting up browser...")
            
            self.playwright = await async_playwright().start()
            
            # Try multiple browsers in order: chromium -> webkit -> firefox
            browser_launched = False
            browsers_to_try = [
                ("chromium", self.playwright.chromium),
                ("webkit", self.playwright.webkit),
                ("firefox", self.playwright.firefox)
            ]
            
            for browser_name, browser_type in browsers_to_try:
                try:
                    logger.info(f"🔄 Trying {browser_name}...")
                    if browser_name == "chromium":
                        self.browser = await browser_type.launch(
                            headless=True,
                            args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox', 
                                '--disable-dev-shm-usage',
                                '--disable-background-timer-throttling',
                                '--disable-backgrounding-occluded-windows',
                                '--disable-renderer-backgrounding',
                                '--disable-web-security'
                            ]
                        )
                    else:
                        self.browser = await browser_type.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-dev-shm-usage']
                        )
                    
                    logger.info(f"✅ {browser_name.capitalize()} browser launched successfully")
                    browser_launched = True
                    break
                    
                except Exception as browser_error:
                    logger.warning(f"⚠️ {browser_name.capitalize()} failed: {browser_error}")
                    continue
            
            if not browser_launched:
                raise Exception("All browser types failed to launch")
            
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(60000)  # 60 seconds for Render
            
            logger.info("✅ Browser ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def login_once(self):
        """Login once and stay logged in"""
        try:
            logger.info("🔐 Logging in...")
            
            # Go to login page with longer timeout
            await self.page.goto(self.login_url, wait_until='load', timeout=45000)
            await asyncio.sleep(3)
            
            # Wait for form to be ready
            await self.page.wait_for_selector('input[name="username"]', timeout=10000)
            
            # Fill login form
            await self.page.fill('input[name="username"]', self.username)
            logger.info("✅ Username filled")
            
            await self.page.fill('input[name="password"]', self.password)
            logger.info("✅ Password filled")
            
            # Handle captcha with multiple approaches
            captcha_solved = False
            try:
                # Try label approach first
                captcha_label = await self.page.query_selector('label[for="capt"]')
                if captcha_label:
                    captcha_text = await captcha_label.text_content()
                    logger.info(f"Found captcha label: {captcha_text}")
                    match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                    if match:
                        result = int(match.group(1)) + int(match.group(2))
                        await self.page.fill('input[name="capt"]', str(result))
                        logger.info(f"✅ Captcha solved: {captcha_text} = {result}")
                        captcha_solved = True
                
                # If label approach failed, try direct page content
                if not captcha_solved:
                    page_content = await self.page.content()
                    captcha_matches = re.findall(r'(\d+)\s*\+\s*(\d+)', page_content)
                    if captcha_matches:
                        nums = captcha_matches[0]  # Take first match
                        result = int(nums[0]) + int(nums[1])
                        await self.page.fill('input[name="capt"]', str(result))
                        logger.info(f"✅ Captcha solved from page content: {nums[0]} + {nums[1]} = {result}")
                        captcha_solved = True
                        
            except Exception as captcha_error:
                logger.warning(f"⚠️ Captcha handling failed: {captcha_error}")
            
            if not captcha_solved:
                logger.warning("⚠️ No captcha found or failed to solve")
            
            await asyncio.sleep(1)  # Wait before submit
            
            # Submit and wait for navigation
            submit_button = await self.page.query_selector('input[type="submit"]')
            if not submit_button:
                submit_button = await self.page.query_selector('button[type="submit"]')
            if not submit_button:
                submit_button = await self.page.query_selector('button')
                
            if submit_button:
                await submit_button.click()
                logger.info("✅ Submit clicked")
            else:
                logger.error("❌ Submit button not found")
                return False
            
            # Wait for navigation - try multiple approaches
            for attempt in range(3):
                try:
                    logger.info(f"Navigation attempt {attempt + 1}/3...")
                    await asyncio.sleep(3)  # Wait for page to process
                    
                    current_url = self.page.url
                    logger.info(f"Current URL: {current_url}")
                    
                    # Check URL for success
                    if "client" in current_url and "login" not in current_url:
                        logger.info("✅ Login successful - URL changed")
                        return True
                    
                    # Check page content for success indicators
                    try:
                        page_text = await self.page.text_content('body')
                        if page_text:
                            if any(indicator in page_text.lower() for indicator in ['sms', 'dashboard', 'welcome', 'logout']):
                                logger.info("✅ Login successful - found success indicator")
                                return True
                            elif 'login' in page_text.lower() and 'error' in page_text.lower():
                                logger.error("❌ Login failed - error message detected")
                                return False
                    except:
                        pass
                    
                    if attempt < 2:  # Don't wait on last attempt
                        await asyncio.sleep(2)
                        
                except Exception as nav_error:
                    logger.warning(f"Navigation attempt {attempt + 1} error: {nav_error}")
                    if attempt < 2:
                        await asyncio.sleep(2)
            
            # Final check
            final_url = self.page.url
            logger.info(f"Final URL after all attempts: {final_url}")
            
            if "login" not in final_url or "client" in final_url:
                logger.info("✅ Login appears successful")
                return True
            else:
                logger.error("❌ Login failed after all attempts")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    async def check_for_messages(self) -> list:
        """Simple message check"""
        try:
            # Go to SMS page
            await self.page.goto(self.sms_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(1)
            
            # Get table data
            table = await self.page.query_selector('table')
            if not table:
                return []
            
            rows = await table.query_selector_all('tbody tr')
            if not rows:
                return []
            
            messages = []
            for row in rows[:10]:  # Only check first 10 rows
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 5:
                        row_data = []
                        for cell in cells:
                            text = await cell.text_content()
                            row_data.append(text.strip() if text else '')
                        messages.append(row_data)
                except:
                    continue
            
            self.last_successful_check = datetime.now()
            return messages
            
        except Exception as e:
            logger.warning(f"⚠️ Check failed: {e}")
            return []
    
    def extract_otp_data(self, row_data: list) -> Dict[str, Any]:
        """Extract OTP from row data"""
        try:
            if len(row_data) < 5:
                return None
            
            time_str = row_data[0]
            number = row_data[1]
            message = row_data[4]
            
            # Find OTP code
            otp_match = re.search(r'\b(\d{4,8})\b', message)
            if not otp_match:
                return None
            
            otp_code = otp_match.group(1)
            
            # Detect service
            service = "Unknown"
            message_lower = message.lower()
            if 'whatsapp' in message_lower:
                service = 'WhatsApp'
            elif 'telegram' in message_lower:
                service = 'Telegram'
            elif 'facebook' in message_lower:
                service = 'Facebook'
            elif 'google' in message_lower:
                service = 'Google'
            
            return {
                'time': time_str,
                'number': number,
                'message': message,
                'otp_code': otp_code,
                'service': service
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Extract error: {e}")
            return None
    
    def get_message_hash(self, message: str) -> str:
        """Generate hash for duplicate detection"""
        return hashlib.md5(message.encode()).hexdigest()
    
    async def send_to_telegram(self, otp_data: Dict[str, Any]) -> bool:
        """Send OTP to Telegram channel and users"""
        try:
            # Format message
            message = f"""🔔 **OTP Alert**

📞 Number: `{otp_data['number']}`
🔐 Code: `{otp_data['otp_code']}`
💬 Service: {otp_data['service']}
⏰ Time: {otp_data['time']}

```
{otp_data['message']}
```"""
            
            # Send to channel
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Notify individual users (non-blocking)
            if self.number_bot:
                asyncio.create_task(self.number_bot.notify_user_otp(
                    otp_data['number'],
                    otp_data['otp_code'],
                    otp_data['service'],
                    otp_data['message']
                ))
            
            logger.info(f"✅ OTP {otp_data['otp_code']} sent → {otp_data['service']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Send failed: {e}")
            return False
    
    async def simple_monitoring_loop(self):
        """Simple monitoring - no unnecessary restarts"""
        logger.info("🚀 Starting SIMPLE monitoring...")
        
        consecutive_failures = 0
        max_failures = 20  # Only restart after 20 consecutive failures
        
        while True:
            try:
                # Check for messages
                messages = await self.check_for_messages()
                
                if messages:
                    consecutive_failures = 0  # Reset failure counter on success
                    
                    # Process new messages
                    for row_data in messages:
                        otp_data = self.extract_otp_data(row_data)
                        if otp_data:
                            # Check for duplicates
                            message_hash = self.get_message_hash(otp_data['message'])
                            if message_hash not in self.processed_hashes:
                                self.processed_hashes.add(message_hash)
                                
                                # Send OTP (non-blocking)
                                asyncio.create_task(self.send_to_telegram(otp_data))
                    
                    # Clean old hashes (keep memory usage low)
                    if len(self.processed_hashes) > 1000:
                        old_hashes = list(self.processed_hashes)[:500]
                        self.processed_hashes = set(old_hashes)
                
                else:
                    consecutive_failures += 1
                    
                    # Only restart if too many consecutive failures
                    if consecutive_failures >= max_failures:
                        logger.warning(f"⚠️ {consecutive_failures} consecutive failures - restarting...")
                        
                        try:
                            await self.restart_system()
                            consecutive_failures = 0
                        except:
                            logger.error("❌ Restart failed, continuing...")
                
                # Simple sleep - no complex timing
                await asyncio.sleep(1.0)
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"❌ Monitoring error: {e}")
                
                if consecutive_failures >= max_failures:
                    logger.warning("⚠️ Too many errors - restarting...")
                    try:
                        await self.restart_system()
                        consecutive_failures = 0
                    except:
                        logger.error("❌ Restart failed, continuing...")
                
                await asyncio.sleep(3)
    
    async def restart_system(self):
        """Only restart when really needed"""
        logger.info("🔄 System restart...")
        
        try:
            # Close browser
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            # Setup again
            if await self.setup_browser():
                if await self.login_once():
                    logger.info("✅ System restarted successfully")
                    return True
            
            logger.error("❌ System restart failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Restart error: {e}")
            return False
    
    async def run(self):
        """Run the simple OTP bot"""
        try:
            logger.info("🚀 SIMPLE OTP BOT STARTING...")
            
            # Initial setup
            if not await self.setup_browser():
                return False
            
            if not await self.login_once():
                return False
            
            logger.info("✅ Simple OTP Bot ready!")
            logger.info("📱 Monitoring for new OTPs...")
            
            # Start simple monitoring
            await self.simple_monitoring_loop()
            
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            return False
        finally:
            # Cleanup
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

async def main():
    """Main entry point"""
    bot = SimpleOTPBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
