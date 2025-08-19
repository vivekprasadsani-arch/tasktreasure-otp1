#!/usr/bin/env python3
"""
ULTRA-FAST REAL-TIME OTP BOT
Optimized approach for instant OTP detection and delivery
"""

import asyncio
import logging
import time
import re
import os
import hashlib
from datetime import datetime
from typing import Set, Dict, Any, Optional
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

class OptimizedOTPBot:
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
        
        # Browser optimization
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Performance tracking
        self.last_check_time = datetime.now()
        self.processed_hashes: Set[str] = set()
        self.navigation_lock = asyncio.Lock()
        
        # User notification system
        self.number_bot = None
        self._init_number_bot()
    
    def _init_number_bot(self):
        """Initialize number bot for user notifications"""
        try:
            from telegram_number_bot import TelegramNumberBot
            self.number_bot = TelegramNumberBot()
            logger.info("✅ Number bot integrated")
        except Exception as e:
            logger.warning(f"⚠️ Number bot integration failed: {e}")
    
    async def ultra_fast_browser_setup(self):
        """Ultra-fast browser setup with aggressive optimizations"""
        try:
            logger.info("⚡ Ultra-fast browser setup...")
            
            self.playwright = await async_playwright().start()
            
            # Ultra-light browser config
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-images',
                    '--disable-javascript',  # Disable JS for speed
                    '--disable-plugins',
                    '--disable-extensions',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--memory-pressure-off',
                    '--max_old_space_size=512'  # Limit memory
                ]
            )
            
            # Ultra-fast page config
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(10000)  # Fast timeout
            
            # Block ALL unnecessary resources for maximum speed
            await self.page.route("**/*.{png,jpg,jpeg,gif,css,js,woff,woff2,svg,ico}", 
                                 lambda route: route.abort())
            
            logger.info("⚡ Ultra-fast browser ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def lightning_login(self):
        """Lightning-fast login with minimal waits"""
        try:
            logger.info("⚡ Lightning login...")
            
            # Fast navigation
            await self.page.goto(self.login_url, wait_until='domcontentloaded', timeout=8000)
            
            # Instant form fill
            await self.page.fill('input[name="username"]', self.username)
            await self.page.fill('input[name="password"]', self.password)
            
            # Auto-solve captcha
            captcha_text = await self.page.text_content('label[for="capt"]')
            if captcha_text:
                match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                if match:
                    result = int(match.group(1)) + int(match.group(2))
                    await self.page.fill('input[name="capt"]', str(result))
                    logger.info(f"⚡ Captcha solved: {result}")
            
            # Submit
            await self.page.click('input[type="submit"], button[type="submit"]')
            await asyncio.sleep(2)  # Minimal wait
            
            # Verify login
            current_url = self.page.url
            if "client" in current_url and "login" not in current_url:
                logger.info("⚡ Lightning login successful")
                return True
            else:
                logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Lightning login error: {e}")
            return False
    
    async def instant_message_scan(self) -> list:
        """Instant message scanning with minimal processing"""
        try:
            # Super-fast navigation
            await self.page.goto(self.sms_url, wait_until='domcontentloaded', timeout=5000)
            
            # Direct table scraping
            table_data = await self.page.evaluate('''
                () => {
                    const table = document.querySelector('table tbody');
                    if (!table) return [];
                    
                    const rows = Array.from(table.querySelectorAll('tr'));
                    return rows.slice(0, 20).map(row => {  // Only process first 20 rows
                        const cells = Array.from(row.querySelectorAll('td'));
                        return cells.map(cell => cell.innerText.trim());
                    }).filter(row => row.length >= 5);
                }
            ''')
            
            return table_data
            
        except Exception as e:
            logger.warning(f"⚠️ Scan error: {e}")
            return []
    
    def extract_otp_data(self, row_data: list) -> Optional[Dict[str, Any]]:
        """Ultra-fast OTP data extraction"""
        try:
            if len(row_data) < 5:
                return None
            
            time_str = row_data[0]
            number = row_data[1] 
            message = row_data[4]
            
            # Fast OTP extraction
            otp_match = re.search(r'\b(\d{4,8})\b', message)
            if not otp_match:
                return None
            
            otp_code = otp_match.group(1)
            
            # Fast service detection
            service = "Unknown"
            message_lower = message.lower()
            services = {
                'whatsapp': 'WhatsApp', 'telegram': 'Telegram', 'facebook': 'Facebook',
                'instagram': 'Instagram', 'google': 'Google', 'twitter': 'Twitter',
                'linkedin': 'LinkedIn', 'uber': 'Uber', 'netflix': 'Netflix'
            }
            
            for key, name in services.items():
                if key in message_lower:
                    service = name
                    break
            
            return {
                'time': time_str,
                'number': number,
                'message': message,
                'otp_code': otp_code,
                'service': service,
                'country': 'Auto-detected',
                'country_flag': '🌍'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Extract error: {e}")
            return None
    
    async def instant_telegram_send(self, sms_data: Dict[str, Any]) -> bool:
        """Instant Telegram message sending"""
        try:
            # Ultra-simple message format
            message = f"""🔔 **OTP Alert**

📞 Number: `{sms_data['number']}`
🔐 Code: `{sms_data['otp_code']}`
💬 Service: {sms_data['service']}
⏰ Time: {sms_data['time']}

```
{sms_data['message']}
```"""
            
            # Send to channel
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Instant user notification
            if self.number_bot:
                asyncio.create_task(self.notify_user_instantly(sms_data))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return False
    
    async def notify_user_instantly(self, sms_data: Dict[str, Any]):
        """Instant user notification without blocking"""
        try:
            await self.number_bot.notify_user_otp(
                sms_data['number'],
                sms_data['otp_code'], 
                sms_data['service'],
                sms_data['message']
            )
        except Exception as e:
            logger.warning(f"⚠️ User notify error: {e}")
    
    def get_message_hash(self, message: str) -> str:
        """Fast message hash generation"""
        return hashlib.md5(message.encode()).hexdigest()[:16]  # Shorter hash
    
    async def real_time_monitoring_loop(self):
        """Real-time monitoring with maximum speed"""
        logger.info("🚀 Starting REAL-TIME monitoring...")
        
        loop_count = 0
        last_messages = set()
        
        while True:
            try:
                start_time = time.time()
                
                # Instant scan
                messages = await self.instant_message_scan()
                
                # Process only new messages
                for row_data in messages:
                    if len(row_data) < 5:
                        continue
                    
                    # Create unique identifier
                    msg_id = f"{row_data[0]}_{row_data[1]}_{row_data[4][:50]}"
                    msg_hash = self.get_message_hash(msg_id)
                    
                    if msg_hash in last_messages:
                        continue
                    
                    last_messages.add(msg_hash)
                    
                    # Extract OTP
                    sms_data = self.extract_otp_data(row_data)
                    if sms_data:
                        # Instant send (non-blocking)
                        asyncio.create_task(self.instant_telegram_send(sms_data))
                        
                        scan_time = (time.time() - start_time) * 1000
                        logger.info(f"⚡ OTP {sms_data['otp_code']} → {sms_data['number']} ({scan_time:.0f}ms)")
                
                # Keep only recent hashes (memory optimization)
                if len(last_messages) > 1000:
                    last_messages = set(list(last_messages)[-500:])
                
                loop_count += 1
                
                # Performance metrics
                if loop_count % 100 == 0:
                    logger.info(f"⚡ Performance: {loop_count} loops, {len(last_messages)} tracked messages")
                
                # Ultra-fast loop - 200ms intervals
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                
                # Quick recovery
                try:
                    await self.page.reload(timeout=3000)
                    await asyncio.sleep(1)
                except:
                    # Background re-login if needed
                    asyncio.create_task(self.background_recovery())
                
                await asyncio.sleep(2)
    
    async def background_recovery(self):
        """Background recovery without blocking monitoring"""
        try:
            logger.info("🔄 Background recovery...")
            await self.lightning_login()
            logger.info("✅ Recovery complete")
        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")
    
    async def run_optimized_system(self):
        """Run the complete optimized system"""
        try:
            logger.info("🚀 OPTIMIZED OTP SYSTEM STARTING...")
            
            # Ultra-fast setup
            if not await self.ultra_fast_browser_setup():
                return False
            
            if not await self.lightning_login():
                return False
            
            logger.info("⚡ System ready - Starting real-time monitoring...")
            
            # Start real-time monitoring
            await self.real_time_monitoring_loop()
            
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
    bot = OptimizedOTPBot()
    await bot.run_optimized_system()

if __name__ == "__main__":
    asyncio.run(main())
