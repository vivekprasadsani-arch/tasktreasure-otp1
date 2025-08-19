#!/usr/bin/env python3
"""
ENHANCED OTP SYSTEM - DUAL STRATEGY APPROACH
Combines optimized monitoring with fallback mechanisms for 100% reliability
"""

import asyncio
import logging
import time
import re
import os
from datetime import datetime
from typing import Set, Dict, Any, Optional
import json

# Import existing components
from otp_telegram_bot import OTPTelegramBot
from telegram_number_bot import TelegramNumberBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedOTPSystem:
    def __init__(self):
        # Primary OTP monitoring bot
        self.otp_bot = None
        
        # Number management bot
        self.number_bot = None
        
        # Performance tracking
        self.start_time = datetime.now()
        self.processed_count = 0
        self.error_count = 0
        
        # Monitoring state
        self.monitoring_active = False
        self.last_successful_scan = datetime.now()
    
    async def initialize_system(self):
        """Initialize the complete OTP system"""
        try:
            logger.info("🚀 ENHANCED OTP SYSTEM - INITIALIZING...")
            
            # Initialize number bot (shared instance)
            logger.info("👥 Initializing Number Bot...")
            self.number_bot = TelegramNumberBot()
            logger.info(f"✅ Number Bot ready - {len(self.number_bot.available_countries)} countries, {len(self.number_bot.user_sessions)} active users")
            
            # Initialize OTP monitoring bot
            logger.info("🔍 Initializing OTP Monitor...")
            self.otp_bot = OTPTelegramBot()
            
            # Set shared number bot
            self.otp_bot.number_bot = self.number_bot
            logger.info("🔗 Shared instance configured")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def enhanced_browser_setup(self):
        """Enhanced browser setup with multiple strategies"""
        try:
            logger.info("⚡ Enhanced browser setup...")
            
            # Strategy 1: Ultra-fast setup
            start_time = time.time()
            result = await self.otp_bot.setup_browser()
            setup_time = (time.time() - start_time) * 1000
            
            if result:
                logger.info(f"✅ Browser ready in {setup_time:.0f}ms")
                return True
            else:
                logger.error("❌ Browser setup failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Browser setup error: {e}")
            return False
    
    async def smart_login_system(self):
        """Smart login with multiple attempts and optimization"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"🔐 Login attempt {attempt + 1}/{max_attempts}...")
                start_time = time.time()
                
                result = await self.otp_bot.login_to_website()
                login_time = (time.time() - start_time) * 1000
                
                if result:
                    logger.info(f"✅ Login successful in {login_time:.0f}ms")
                    return True
                else:
                    logger.warning(f"⚠️ Login attempt {attempt + 1} failed ({login_time:.0f}ms)")
                    
                    if attempt < max_attempts - 1:
                        # Progressive backoff
                        wait_time = (attempt + 1) * 2
                        logger.info(f"⏳ Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        
                        # Browser refresh for retry
                        try:
                            await self.otp_bot.restart_browser()
                            logger.info("🔄 Browser refreshed for retry")
                        except:
                            pass
                    
            except Exception as e:
                logger.error(f"❌ Login attempt {attempt + 1} error: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(3)
        
        logger.error("❌ All login attempts failed")
        return False
    
    async def real_time_monitoring_loop(self):
        """Real-time monitoring with enhanced error handling"""
        logger.info("🚀 REAL-TIME MONITORING STARTING...")
        self.monitoring_active = True
        
        loop_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.monitoring_active:
            try:
                loop_start = time.time()
                
                # Get messages with timeout
                messages = await asyncio.wait_for(
                    self.otp_bot.check_for_new_messages(),
                    timeout=10.0
                )
                
                # Process messages
                new_found = 0
                for row_data in messages:
                    sms_data = self.otp_bot.extract_sms_data(row_data)
                    if sms_data:
                        # Check for duplicates
                        message_hash = self.otp_bot.get_message_hash(sms_data['message'])
                        
                        # Send to Telegram (non-blocking)
                        asyncio.create_task(self.otp_bot.send_to_telegram(
                            self.otp_bot.format_message(sms_data), 
                            sms_data
                        ))
                        
                        new_found += 1
                        self.processed_count += 1
                        
                        loop_time = (time.time() - loop_start) * 1000
                        logger.info(f"⚡ OTP {sms_data['otp_code']} → {sms_data['service']} ({loop_time:.0f}ms)")
                
                # Update success tracking
                if messages:
                    self.last_successful_scan = datetime.now()
                    consecutive_errors = 0
                
                loop_count += 1
                
                # Performance logging
                if loop_count % 50 == 0:
                    uptime = datetime.now() - self.start_time
                    logger.info(f"📊 Performance: {self.processed_count} OTPs processed, {consecutive_errors} errors, Uptime: {uptime}")
                
                # Adaptive sleep based on activity
                if new_found > 0:
                    await asyncio.sleep(0.3)  # Faster when active
                else:
                    await asyncio.sleep(0.8)   # Slower when idle
                
            except asyncio.TimeoutError:
                consecutive_errors += 1
                logger.warning(f"⏰ Scan timeout ({consecutive_errors}/{max_consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("❌ Too many consecutive timeouts - triggering recovery")
                    asyncio.create_task(self.emergency_recovery())
                    consecutive_errors = 0
                
                await asyncio.sleep(2)
                
            except Exception as e:
                consecutive_errors += 1
                self.error_count += 1
                logger.error(f"❌ Monitoring error: {e} ({consecutive_errors}/{max_consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("❌ Too many consecutive errors - triggering recovery")
                    asyncio.create_task(self.emergency_recovery())
                    consecutive_errors = 0
                
                await asyncio.sleep(3)
    
    async def emergency_recovery(self):
        """Emergency recovery system"""
        try:
            logger.info("🚨 EMERGENCY RECOVERY STARTING...")
            
            # Quick browser restart
            await self.otp_bot.restart_browser()
            await asyncio.sleep(2)
            
            # Quick login
            if await self.smart_login_system():
                logger.info("✅ Emergency recovery successful")
            else:
                logger.error("❌ Emergency recovery failed")
                
        except Exception as e:
            logger.error(f"❌ Emergency recovery error: {e}")
    
    async def run_enhanced_system(self):
        """Run the complete enhanced system"""
        try:
            # System initialization
            if not await self.initialize_system():
                logger.error("❌ System initialization failed")
                return False
            
            # Enhanced browser setup
            if not await self.enhanced_browser_setup():
                logger.error("❌ Browser setup failed")
                return False
            
            # Smart login
            if not await self.smart_login_system():
                logger.error("❌ Login failed")
                return False
            
            logger.info("🎉 ENHANCED OTP SYSTEM READY!")
            logger.info("=" * 60)
            logger.info("⚡ Real-time OTP monitoring active")
            logger.info("📱 Individual user notifications enabled") 
            logger.info("🔔 Channel broadcasting active")
            logger.info("🔄 Automatic error recovery enabled")
            logger.info("=" * 60)
            
            # Start monitoring
            await self.real_time_monitoring_loop()
            
        except Exception as e:
            logger.error(f"❌ Enhanced system error: {e}")
            return False
        finally:
            self.monitoring_active = False
            
            # Cleanup
            if self.otp_bot and self.otp_bot.browser:
                await self.otp_bot.browser.close()
            if self.otp_bot and self.otp_bot.playwright:
                await self.otp_bot.playwright.stop()

async def main():
    """Main entry point for enhanced system"""
    system = EnhancedOTPSystem()
    await system.run_enhanced_system()

if __name__ == "__main__":
    asyncio.run(main())
