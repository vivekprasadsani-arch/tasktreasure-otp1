#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTP Telegram Bot
Monitors website for incoming OTP messages and forwards them to Telegram channel
"""

import asyncio
import logging
import time
import re
import os
import hashlib
import psutil
from datetime import datetime
from typing import Set, Dict, Any
import json


import requests
from playwright.async_api import async_playwright
import telegram
from telegram.constants import ParseMode
from supabase import create_client, Client

# Import our number bot for user notifications
try:
    from telegram_number_bot import TelegramNumberBot
    NUMBER_BOT_AVAILABLE = True
except ImportError:
    NUMBER_BOT_AVAILABLE = False
    logger.warning("⚠️ telegram_number_bot not available - user notifications disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('otp_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class OTPTelegramBot:
    def __init__(self):
        # Website credentials and URLs
        self.username = "Roni_dada"
        self.password = "Roni_dada"
        self.login_url = "http://94.23.120.156/ints/login"
        self.sms_url = "http://94.23.120.156/ints/client/SMSCDRStats"
        
        # Telegram Bot credentials
        self.bot_token = "8354306480:AAGmQbuElJ3iZV4iHiMPHvLpSo7UxrStbY0"
        self.channel_id = "-1002724043027"
        
        # Initialize Telegram bot
        self.bot = telegram.Bot(token=self.bot_token)
        
        # Supabase configuration
        self.supabase_url = "https://wddcrtrgirhcemmobgcc.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkZGNydHJnaXJoY2VtbW9iZ2NjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjA1NTYsImV4cCI6MjA3MDkzNjU1Nn0.K5vpqoc_zakEwBd96aC-drJ5OoInTSFcrMlWy7ShIyI"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Playwright browser and page
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Track last processed message time to avoid old messages
        self.last_check_time = datetime.now()
        
        # Navigation lock to prevent concurrent page operations
        self.navigation_lock = asyncio.Lock()
        
        # Initialize number bot for user notifications
        self.number_bot = None
        if NUMBER_BOT_AVAILABLE:
            try:
                self.number_bot = TelegramNumberBot()
                logger.info("✅ Number bot initialized for user notifications")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize number bot: {e}")
        
    async def init_database(self):
        """Initialize the database table for storing processed message hashes"""
        try:
            logger.info("Initializing Supabase database...")
            
            # Create table if it doesn't exist
            # This will be a simple table with just the message hash and timestamp
            result = self.supabase.table('processed_messages').select('*').limit(1).execute()
            logger.info("Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # We'll continue without database for fallback
            return False
    
    async def is_message_processed(self, message_hash: str) -> bool:
        """Check if a message hash has already been processed"""
        try:
            result = self.supabase.table('processed_messages').select('hash').eq('hash', message_hash).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking message hash in database: {e}")
            # Fallback: assume not processed to avoid missing messages
            return False
    
    async def mark_message_processed(self, message_hash: str) -> bool:
        """Mark a message hash as processed in the database"""
        try:
            current_time = datetime.now().isoformat()
            result = self.supabase.table('processed_messages').insert({
                'hash': message_hash,
                'processed_at': current_time
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking message as processed in database: {e}")
            return False
    
    async def cleanup_old_hashes(self):
        """Clean up old message hashes to prevent database bloat (keep last 30 days)"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            result = self.supabase.table('processed_messages').delete().lt('processed_at', cutoff_date).execute()
            if result.data:
                logger.info(f"Cleaned up {len(result.data)} old message hashes")
        except Exception as e:
            logger.error(f"Error cleaning up old hashes: {e}")
    
    async def restart_browser(self):
        """Restart browser to prevent memory leaks"""
        try:
            logger.info("Restarting browser to free memory...")
            
            # Close current browser
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            # Small delay to ensure cleanup
            await asyncio.sleep(1)
            
            # Restart browser
            if not await self.setup_browser():
                logger.error("Failed to restart browser")
                return False
            
            # Re-login to website
            if not await self.login_to_website():
                logger.error("Failed to re-login after browser restart")
                return False
            
            logger.info("Browser restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error restarting browser: {e}")
            return False
    
    def log_memory_usage(self):
        """Log current memory usage for monitoring"""
        try:
            # Get current process memory info
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            system_used_mb = (system_memory.total - system_memory.available) / 1024 / 1024
            
            logger.info(f"Memory Usage - Process: {memory_mb:.1f}MB, System: {system_used_mb:.1f}MB ({system_memory.percent:.1f}%)")
            
            # Warning if memory usage is high
            if memory_mb > 150:  # 150MB threshold
                logger.warning(f"High memory usage detected: {memory_mb:.1f}MB")
                return True  # Signal that memory is high
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return False
        
    async def ensure_browsers_installed(self):
        """Ensure Playwright browsers are installed"""
        try:
            logger.info("Checking if Playwright browsers are installed...")
            
            # Try to start playwright and check if chromium is available
            test_playwright = await async_playwright().start()
            
            try:
                # Try to launch chromium to check if it's installed
                test_browser = await test_playwright.chromium.launch(headless=True)
                await test_browser.close()
                logger.info("Playwright browsers are already installed")
                return True
            except Exception as browser_error:
                logger.warning(f"Browser not available: {browser_error}")
                
                # Install browsers
                logger.info("Installing Playwright browsers...")
                import subprocess
                import sys
                
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info("Playwright chromium installed successfully")
                    return True
                else:
                    logger.error(f"Failed to install browsers: {result.stderr}")
                    return False
            finally:
                await test_playwright.stop()
                    
        except Exception as e:
            logger.error(f"Error ensuring browsers installed: {e}")
            return False
    
    async def setup_browser(self):
        """Setup Playwright browser with appropriate options"""
        logger.info("Setting up Playwright browser...")
        
        # Ensure browsers are installed first
        if not await self.ensure_browsers_installed():
            logger.error("Failed to ensure browsers are installed")
            return False
        
        self.playwright = await async_playwright().start()
        
        # Launch browser with options
        try:
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--ignore-certificate-errors-invalid-ca',
                    '--disable-setuid-sandbox',
                    '--memory-pressure-off',
                    '--max_old_space_size=256',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
        except Exception as launch_error:
            logger.error(f"Failed to launch browser: {launch_error}")
            logger.info("Trying to install browsers again...")
            
            # Last resort: try to install browsers again
            import subprocess
            import sys
            
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Browsers reinstalled, trying launch again...")
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--allow-running-insecure-content',
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--ignore-certificate-errors-spki-list',
                        '--ignore-certificate-errors-invalid-ca',
                        '--disable-setuid-sandbox',
                    ]
                )
            else:
                logger.error("Failed to reinstall browsers")
                return False
        
        # Create new page with user agent and memory optimizations
        self.page = await self.browser.new_page(
            user_agent='Mozilla/5.0 (Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Set page timeout to prevent hanging
        self.page.set_default_timeout(30000)  # 30 seconds - increased for stability
        
        # Disable images and CSS to save memory (we only need table data)
        await self.page.route("**/*.{png,jpg,jpeg,gif,css,woff,woff2}", lambda route: route.abort())
        
        logger.info("Playwright browser setup successful with memory optimizations")
        return True
    
    async def solve_captcha(self, page_content: str) -> int:
        """Solve simple math captcha"""
        try:
            # Look for captcha pattern in page content
            captcha_match = re.search(r'What is (\d+) \+ (\d+) = \?', page_content)
            if captcha_match:
                num1, num2 = map(int, captcha_match.groups())
                result = num1 + num2
                logger.info(f"Solved captcha: {num1} + {num2} = {result}")
                return result
        except Exception as e:
            logger.error(f"Error solving captcha: {e}")
        
        return 0
    
    async def login_to_website(self) -> bool:
        """Login to the website with captcha solving"""
        try:
            logger.info("Starting login process...")
            
            # Navigate to login page
            await self.page.goto(self.login_url, wait_until='load', timeout=30000)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Get page content for debugging
            page_content = await self.page.content()
            page_title = await self.page.title()
            current_url = self.page.url
            
            logger.info(f"Page title: {page_title}")
            logger.info(f"Current URL: {current_url}")
            
            # Handle SSL warning if present
            if "not secure" in page_title.lower() or "privacy error" in page_content.lower():
                logger.info("Detected SSL warning page, attempting to bypass...")
                
                # Try to click Advanced button
                try:
                    advanced_button = await self.page.query_selector('#details-button')
                    if advanced_button:
                        await advanced_button.click()
                        await asyncio.sleep(2)
                        
                        # Try to click proceed link
                        proceed_link = await self.page.query_selector('#proceed-link')
                        if proceed_link:
                            await proceed_link.click()
                            await asyncio.sleep(3)
                            logger.info("SSL warning bypassed successfully")
                        
                except Exception as ssl_error:
                    logger.warning(f"SSL bypass failed: {ssl_error}")
                    # Try direct navigation
                    await self.page.goto(self.login_url, wait_until='load', timeout=30000)
                    await asyncio.sleep(3)
            
            # Wait for login form elements
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Get updated page content
            page_content = await self.page.content()
            page_title = await self.page.title()
            current_url = self.page.url
            
            logger.info(f"After SSL handling - Title: {page_title}")
            logger.info(f"After SSL handling - URL: {current_url}")
            
            # Find and fill username field
            username_field = None
            username_selectors = [
                'input[name="username"]',
                'input[id="username"]', 
                'input[type="text"]',
                'input[name*="user"]'
            ]
            
            for selector in username_selectors:
                try:
                    username_field = await self.page.query_selector(selector)
                    if username_field:
                        logger.info(f"Found username field using selector: {selector}")
                        break
                except:
                    continue
            
            if not username_field:
                logger.error("Could not find username field")
                logger.info(f"Page content excerpt: {page_content[:500]}")
                return False
            
            # Clear and fill username
            await username_field.click(click_count=3)  # Triple click to select all
            await username_field.fill(self.username)
            logger.info("Username entered successfully")
            
            # Find and fill password field
            password_field = None
            password_selectors = [
                'input[name="password"]',
                'input[id="password"]',
                'input[type="password"]',
                'input[name*="pass"]'
            ]
            
            for selector in password_selectors:
                try:
                    password_field = await self.page.query_selector(selector)
                    if password_field:
                        logger.info(f"Found password field using selector: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Clear and fill password
            await password_field.click(click_count=3)  # Triple click to select all
            await password_field.fill(self.password)
            logger.info("Password entered successfully")
            
            # Solve captcha
            captcha_answer = await self.solve_captcha(page_content)
            if captcha_answer > 0:
                captcha_field = None
                captcha_selectors = [
                    'input[name="capt"]',
                    'input[id="capt"]',
                    'input[type="number"]',
                    'input[name*="capt"]'
                ]
                
                for selector in captcha_selectors:
                    try:
                        captcha_field = await self.page.query_selector(selector)
                        if captcha_field:
                            logger.info(f"Found captcha field using selector: {selector}")
                            break
                    except:
                        continue
                
                if captcha_field:
                    await captcha_field.click(click_count=3)  # Triple click to select all
                    await captcha_field.fill(str(captcha_answer))
                    logger.info(f"Captcha solved and entered: {captcha_answer}")
                else:
                    logger.warning("Could not find captcha field")
            
            # Submit form
            submit_button = None
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button',
                'input[value*="Login"]',
                'button:has-text("Login")'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = await self.page.query_selector(selector)
                    if submit_button:
                        logger.info(f"Found submit button using selector: {selector}")
                        break
                except:
                    continue
            
            if not submit_button:
                logger.error("Could not find submit button")
                return False
            
            # Click submit
            await submit_button.click()
            logger.info("Clicked submit button")
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(3)
            
            # Check if login was successful
            current_url = self.page.url
            logger.info(f"After login URL: {current_url}")
            
            if "client" in current_url.lower() and "login" not in current_url.lower():
                logger.info("Login successful!")
                return True
            else:
                logger.error(f"Login failed - unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_country_info(self, phone_number: str) -> Dict[str, str]:
        """Get country name and flag based on phone number"""
        country_codes = {
            # Major countries
            '1': {'name': 'USA/Canada', 'flag': '🇺🇸'},
            '7': {'name': 'Russia', 'flag': '🇷🇺'},
            '20': {'name': 'Egypt', 'flag': '🇪🇬'},
            '27': {'name': 'South Africa', 'flag': '🇿🇦'},
            '30': {'name': 'Greece', 'flag': '🇬🇷'},
            '31': {'name': 'Netherlands', 'flag': '🇳🇱'},
            '32': {'name': 'Belgium', 'flag': '🇧🇪'},
            '33': {'name': 'France', 'flag': '🇫🇷'},
            '34': {'name': 'Spain', 'flag': '🇪🇸'},
            '36': {'name': 'Hungary', 'flag': '🇭🇺'},
            '39': {'name': 'Italy', 'flag': '🇮🇹'},
            '40': {'name': 'Romania', 'flag': '🇷🇴'},
            '41': {'name': 'Switzerland', 'flag': '🇨🇭'},
            '43': {'name': 'Austria', 'flag': '🇦🇹'},
            '44': {'name': 'United Kingdom', 'flag': '🇬🇧'},
            '45': {'name': 'Denmark', 'flag': '🇩🇰'},
            '46': {'name': 'Sweden', 'flag': '🇸🇪'},
            '47': {'name': 'Norway', 'flag': '🇳🇴'},
            '48': {'name': 'Poland', 'flag': '🇵🇱'},
            '49': {'name': 'Germany', 'flag': '🇩🇪'},
            '51': {'name': 'Peru', 'flag': '🇵🇪'},
            '52': {'name': 'Mexico', 'flag': '🇲🇽'},
            '53': {'name': 'Cuba', 'flag': '🇨🇺'},
            '54': {'name': 'Argentina', 'flag': '🇦🇷'},
            '55': {'name': 'Brazil', 'flag': '🇧🇷'},
            '56': {'name': 'Chile', 'flag': '🇨🇱'},
            '57': {'name': 'Colombia', 'flag': '🇨🇴'},
            '58': {'name': 'Venezuela', 'flag': '🇻🇪'},
            '60': {'name': 'Malaysia', 'flag': '🇲🇾'},
            '61': {'name': 'Australia', 'flag': '🇦🇺'},
            '62': {'name': 'Indonesia', 'flag': '🇮🇩'},
            '63': {'name': 'Philippines', 'flag': '🇵🇭'},
            '64': {'name': 'New Zealand', 'flag': '🇳🇿'},
            '65': {'name': 'Singapore', 'flag': '🇸🇬'},
            '66': {'name': 'Thailand', 'flag': '🇹🇭'},
            '81': {'name': 'Japan', 'flag': '🇯🇵'},
            '82': {'name': 'South Korea', 'flag': '🇰🇷'},
            '84': {'name': 'Vietnam', 'flag': '🇻🇳'},
            '86': {'name': 'China', 'flag': '🇨🇳'},
            '90': {'name': 'Turkey', 'flag': '🇹🇷'},
            '91': {'name': 'India', 'flag': '🇮🇳'},
            '92': {'name': 'Pakistan', 'flag': '🇵🇰'},
            '93': {'name': 'Afghanistan', 'flag': '🇦🇫'},
            '94': {'name': 'Sri Lanka', 'flag': '🇱🇰'},
            '95': {'name': 'Myanmar', 'flag': '🇲🇲'},
            '98': {'name': 'Iran', 'flag': '🇮🇷'},
            '212': {'name': 'Morocco', 'flag': '🇲🇦'},
            '213': {'name': 'Algeria', 'flag': '🇩🇿'},
            '216': {'name': 'Tunisia', 'flag': '🇹🇳'},
            '218': {'name': 'Libya', 'flag': '🇱🇾'},
            '220': {'name': 'Gambia', 'flag': '🇬🇲'},
            '221': {'name': 'Senegal', 'flag': '🇸🇳'},
            '222': {'name': 'Mauritania', 'flag': '🇲🇷'},
            '223': {'name': 'Mali', 'flag': '🇲🇱'},
            '224': {'name': 'Guinea', 'flag': '🇬🇳'},
            '225': {'name': 'Ivory Coast', 'flag': '🇨🇮'},
            '226': {'name': 'Burkina Faso', 'flag': '🇧🇫'},
            '227': {'name': 'Niger', 'flag': '🇳🇪'},
            '228': {'name': 'Togo', 'flag': '🇹🇬'},
            '229': {'name': 'Benin', 'flag': '🇧🇯'},
            '230': {'name': 'Mauritius', 'flag': '🇲🇺'},
            '231': {'name': 'Liberia', 'flag': '🇱🇷'},
            '232': {'name': 'Sierra Leone', 'flag': '🇸🇱'},
            '233': {'name': 'Ghana', 'flag': '🇬🇭'},
            '234': {'name': 'Nigeria', 'flag': '🇳🇬'},
            '235': {'name': 'Chad', 'flag': '🇹🇩'},
            '236': {'name': 'Central African Republic', 'flag': '🇨🇫'},
            '237': {'name': 'Cameroon', 'flag': '🇨🇲'},
            '238': {'name': 'Cape Verde', 'flag': '🇨🇻'},
            '239': {'name': 'Sao Tome and Principe', 'flag': '🇸🇹'},
            '240': {'name': 'Equatorial Guinea', 'flag': '🇬🇶'},
            '241': {'name': 'Gabon', 'flag': '🇬🇦'},
            '242': {'name': 'Republic of Congo', 'flag': '🇨🇬'},
            '243': {'name': 'Democratic Republic of Congo', 'flag': '🇨🇩'},
            '244': {'name': 'Angola', 'flag': '🇦🇴'},
            '245': {'name': 'Guinea-Bissau', 'flag': '🇬🇼'},
            '246': {'name': 'British Indian Ocean Territory', 'flag': '🇮🇴'},
            '248': {'name': 'Seychelles', 'flag': '🇸🇨'},
            '249': {'name': 'Sudan', 'flag': '🇸🇩'},
            '250': {'name': 'Rwanda', 'flag': '🇷🇼'},
            '251': {'name': 'Ethiopia', 'flag': '🇪🇹'},
            '252': {'name': 'Somalia', 'flag': '🇸🇴'},
            '253': {'name': 'Djibouti', 'flag': '🇩🇯'},
            '254': {'name': 'Kenya', 'flag': '🇰🇪'},
            '255': {'name': 'Tanzania', 'flag': '🇹🇿'},
            '256': {'name': 'Uganda', 'flag': '🇺🇬'},
            '257': {'name': 'Burundi', 'flag': '🇧🇮'},
            '258': {'name': 'Mozambique', 'flag': '🇲🇿'},
            '260': {'name': 'Zambia', 'flag': '🇿🇲'},
            '261': {'name': 'Madagascar', 'flag': '🇲🇬'},
            '262': {'name': 'Reunion', 'flag': '🇷🇪'},
            '263': {'name': 'Zimbabwe', 'flag': '🇿🇼'},
            '264': {'name': 'Namibia', 'flag': '🇳🇦'},
            '265': {'name': 'Malawi', 'flag': '🇲🇼'},
            '266': {'name': 'Lesotho', 'flag': '🇱🇸'},
            '267': {'name': 'Botswana', 'flag': '🇧🇼'},
            '268': {'name': 'Swaziland', 'flag': '🇸🇿'},
            '269': {'name': 'Comoros', 'flag': '🇰🇲'},
            '290': {'name': 'Saint Helena', 'flag': '🇸🇭'},
            '291': {'name': 'Eritrea', 'flag': '🇪🇷'},
            '297': {'name': 'Aruba', 'flag': '🇦🇼'},
            '298': {'name': 'Faroe Islands', 'flag': '🇫🇴'},
            '299': {'name': 'Greenland', 'flag': '🇬🇱'},
            '350': {'name': 'Gibraltar', 'flag': '🇬🇮'},
            '351': {'name': 'Portugal', 'flag': '🇵🇹'},
            '352': {'name': 'Luxembourg', 'flag': '🇱🇺'},
            '353': {'name': 'Ireland', 'flag': '🇮🇪'},
            '354': {'name': 'Iceland', 'flag': '🇮🇸'},
            '355': {'name': 'Albania', 'flag': '🇦🇱'},
            '356': {'name': 'Malta', 'flag': '🇲🇹'},
            '357': {'name': 'Cyprus', 'flag': '🇨🇾'},
            '358': {'name': 'Finland', 'flag': '🇫🇮'},
            '359': {'name': 'Bulgaria', 'flag': '🇧🇬'},
            '370': {'name': 'Lithuania', 'flag': '🇱🇹'},
            '371': {'name': 'Latvia', 'flag': '🇱🇻'},
            '372': {'name': 'Estonia', 'flag': '🇪🇪'},
            '373': {'name': 'Moldova', 'flag': '🇲🇩'},
            '374': {'name': 'Armenia', 'flag': '🇦🇲'},
            '375': {'name': 'Belarus', 'flag': '🇧🇾'},
            '376': {'name': 'Andorra', 'flag': '🇦🇩'},
            '377': {'name': 'Monaco', 'flag': '🇲🇨'},
            '378': {'name': 'San Marino', 'flag': '🇸🇲'},
            '380': {'name': 'Ukraine', 'flag': '🇺🇦'},
            '381': {'name': 'Serbia', 'flag': '🇷🇸'},
            '382': {'name': 'Montenegro', 'flag': '🇲🇪'},
            '383': {'name': 'Kosovo', 'flag': '🇽🇰'},
            '385': {'name': 'Croatia', 'flag': '🇭🇷'},
            '386': {'name': 'Slovenia', 'flag': '🇸🇮'},
            '387': {'name': 'Bosnia and Herzegovina', 'flag': '🇧🇦'},
            '389': {'name': 'North Macedonia', 'flag': '🇲🇰'},
            '420': {'name': 'Czech Republic', 'flag': '🇨🇿'},
            '421': {'name': 'Slovakia', 'flag': '🇸🇰'},
            '423': {'name': 'Liechtenstein', 'flag': '🇱🇮'},
            '500': {'name': 'Falkland Islands', 'flag': '🇫🇰'},
            '501': {'name': 'Belize', 'flag': '🇧🇿'},
            '502': {'name': 'Guatemala', 'flag': '🇬🇹'},
            '503': {'name': 'El Salvador', 'flag': '🇸🇻'},
            '504': {'name': 'Honduras', 'flag': '🇭🇳'},
            '505': {'name': 'Nicaragua', 'flag': '🇳🇮'},
            '506': {'name': 'Costa Rica', 'flag': '🇨🇷'},
            '507': {'name': 'Panama', 'flag': '🇵🇦'},
            '508': {'name': 'Saint Pierre and Miquelon', 'flag': '🇵🇲'},
            '509': {'name': 'Haiti', 'flag': '🇭🇹'},
        }
        
        # Clean phone number
        cleaned_number = re.sub(r'[^\d]', '', phone_number)
        
        # Find matching country code (longest match first)
        for code in sorted(country_codes.keys(), key=len, reverse=True):
            if cleaned_number.startswith(code):
                return country_codes[code]
        
        return {'name': 'Unknown', 'flag': '🌍'}
    
    def extract_sms_data(self, row_data: list) -> Dict[str, Any]:
        """Extract and format SMS data from table row - with timestamp filtering"""
        try:
            sms_data = {
                'time': 'Unknown',
                'number': 'Unknown', 
                'country': 'Unknown',
                'country_flag': '🌍',
                'service': 'Unknown',
                'otp_code': 'Unknown',
                'message': 'No message'
            }
            
            # Column mapping: Date, Range, Number, CLI, SMS
            if len(row_data) >= 5:
                sms_data['time'] = row_data[0].strip() if row_data[0] else 'Unknown'
                
                # Check if this message is newer than our last check
                try:
                    message_time = datetime.strptime(sms_data['time'], '%Y-%m-%d %H:%M:%S')
                    
                    # Only process messages from the last 30 minutes to avoid old messages
                    time_diff = datetime.now() - message_time
                    if time_diff.total_seconds() > 1800:  # 30 minutes
                        logger.info(f"Skipping old message from {sms_data['time']} (age: {time_diff.total_seconds():.0f}s)")
                        return None
                        
                except Exception as time_parse_error:
                    logger.warning(f"Could not parse message time: {sms_data['time']}")
                    # Continue processing if time parsing fails
                sms_data['number'] = row_data[2].strip() if row_data[2] else 'Unknown'
                sms_data['service'] = row_data[3].strip() if row_data[3] else 'Unknown'
                sms_data['message'] = row_data[4].strip() if row_data[4] else 'No message'
                
                # Get country info from phone number
                if sms_data['number'] != 'Unknown':
                    country_info = self.get_country_info(sms_data['number'])
                    sms_data['country'] = country_info['name']
                    sms_data['country_flag'] = country_info['flag']
                
                # Extract OTP code from message
                otp_patterns = [
                    r'code[:\s]*(\d{2,3}[-\s]\d{2,3})',
                    r'otp[:\s]*(\d{2,3}[-\s]\d{2,3})',
                    r'verification[:\s]*(\d{2,3}[-\s]\d{2,3})',
                    r'code[:\s]*(\d{3,8})',
                    r'otp[:\s]*(\d{3,8})',
                    r'verification[:\s]*(\d{3,8})',
                    r'(\d{2,3}[-\s]\d{2,3})',
                    r'\b(\d{4,8})\b'
                ]
                
                for pattern in otp_patterns:
                    match = re.search(pattern, sms_data['message'], re.IGNORECASE)
                    if match:
                        sms_data['otp_code'] = match.group(1)
                        break
            
            return sms_data
            
        except Exception as e:
            logger.error(f"Error extracting SMS data: {e}")
            return None
    
    def escape_markdown_v2(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def format_message(self, sms_data: Dict[str, Any]) -> str:
        """Format SMS data into Telegram message"""
        try:
            country_name = sms_data.get('country', 'Unknown')
            country_flag = sms_data.get('country_flag', '🌍')
            service = sms_data.get('service', 'Unknown')
            otp_code = sms_data.get('otp_code', 'Unknown')
            
            # Escape special characters for MarkdownV2
            safe_time = self.escape_markdown_v2(sms_data.get('time', 'Unknown'))
            safe_number = self.escape_markdown_v2(sms_data.get('number', 'Unknown'))
            safe_country = self.escape_markdown_v2(country_name)
            safe_service = self.escape_markdown_v2(service)
            safe_message = sms_data.get('message', 'No message')
            
            # Make OTP clickable
            clickable_otp = f"`{otp_code}`" if otp_code != 'Unknown' else 'Unknown'
            
            message = f"""🔔{safe_country} {country_flag} {safe_service} Otp Code Received Successfully\\.

⏰Time: {safe_time}
📱Number: {safe_number}
🌍Country: {safe_country} {country_flag}
💬Service: {safe_service}
🔐Otp Code: {clickable_otp}
📝Message:
```
{safe_message}
```

Powered by @tasktreasur\\_support"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return "Error formatting message"
    
    def get_message_hash(self, message: str) -> str:
        """Generate hash for message to prevent duplicates"""
        return hashlib.md5(message.encode()).hexdigest()
    
    async def test_telegram_connection(self):
        """Test Telegram bot connection"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Bot info: {bot_info.first_name} (@{bot_info.username})")
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text="🤖 OTP Bot started successfully!",
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
            logger.info("Telegram connection test successful")
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    async def send_to_telegram(self, message: str, sms_data: dict = None) -> bool:
        """Send message to Telegram channel and notify users"""
        try:
            message_hash = self.get_message_hash(message)
            
            # Check if message was already processed using Supabase
            if await self.is_message_processed(message_hash):
                logger.info("Message already sent, skipping duplicate")
                return False
            
            # Try MarkdownV2 first, then fallback
            try:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    connect_timeout=30,
                    read_timeout=30,
                    write_timeout=30
                )
            except Exception as parse_error:
                logger.warning(f"MarkdownV2 failed, trying Markdown: {parse_error}")
                try:
                    await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        connect_timeout=30,
                        read_timeout=30,
                        write_timeout=30
                    )
                except Exception as markdown_error:
                    logger.warning(f"All markdown parsing failed, sending as plain text: {markdown_error}")
                    await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=message,
                        connect_timeout=30,
                        read_timeout=30,
                        write_timeout=30
                    )
            
            # Mark message as processed in database
            await self.mark_message_processed(message_hash)
            logger.info("Message sent to Telegram successfully")
            
            # Also notify individual users if they have this number
            if self.number_bot and sms_data:
                try:
                    number = sms_data.get('number', '')
                    otp_code = sms_data.get('otp_code', '')
                    service = sms_data.get('service', '')
                    full_message = sms_data.get('message', '')
                    
                    if number and otp_code:
                        logger.info(f"🔔 ATTEMPTING USER NOTIFICATION: Number={number}, OTP={otp_code}, Service={service}")
                        logger.info(f"🔔 NUMBER BOT SESSIONS: {len(self.number_bot.user_sessions)} active users")
                        
                        await self.number_bot.notify_user_otp(number, otp_code, service, full_message)
                        logger.info(f"📱 User notification process completed for number {number}")
                    else:
                        logger.warning(f"⚠️ Invalid data for notification: number={number}, otp={otp_code}")
                except Exception as notify_error:
                    logger.error(f"❌ User notification failed: {notify_error}")
                    import traceback
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False
    
    async def check_for_new_messages(self) -> list:
        """Check for new SMS messages on the website - WITH SESSION RECOVERY"""
        async with self.navigation_lock:  # Prevent concurrent navigation
            try:
                # Try to navigate with retry mechanism
                for attempt in range(3):
                    try:
                        logger.info(f"Navigation attempt {attempt + 1}/3")
                        await self.page.goto(self.sms_url, wait_until='domcontentloaded', timeout=40000)
                        break
                    except Exception as nav_error:
                        logger.warning(f"Navigation attempt {attempt + 1} failed: {nav_error}")
                        if attempt == 2:  # Last attempt - force re-login
                            logger.warning("All 3 navigation attempts failed, forcing re-login...")
                            try:
                                # Force browser restart and re-login
                                logger.info("Restarting browser and re-logging in...")
                                if await self.restart_browser():
                                    logger.info("Browser restarted successfully, attempting final navigation...")
                                    await self.page.goto(self.sms_url, wait_until='domcontentloaded', timeout=45000)
                                    break
                                else:
                                    logger.error("Browser restart failed")
                                    return []
                            except Exception as recovery_error:
                                logger.error(f"Recovery login failed: {recovery_error}")
                                return []
                        await asyncio.sleep(2)  # Wait before retry
                
                # Minimal wait for table to appear
                await asyncio.sleep(1)
                
                # Look for table with headers
                table = await self.page.query_selector('table')
                if not table:
                    logger.warning("No table found on SMS page")
                    return []
                
                # Get all table rows
                rows = await table.query_selector_all('tbody tr')
                if not rows:
                    logger.warning("No table rows found")
                    return []
                
                messages = []
                for row in rows:
                    try:
                        # Get all cells in the row
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 5:
                            row_data = []
                            for cell in cells:
                                cell_text = await cell.inner_text()
                                row_data.append(cell_text.strip())
                            
                            # Check if row contains SMS-related keywords
                            row_text = ' '.join(row_data).lower()
                            if any(keyword in row_text for keyword in ['whatsapp', 'code', 'verification', 'sms', 'otp']) and len(row_data[0]) > 0:
                                messages.append(row_data)
                                logger.info(f"Found SMS row: {row_data[:5]}...")
                            
                    except Exception as row_error:
                        logger.warning(f"Error processing table row: {row_error}")
                        continue
                
                logger.info(f"Found {len(messages)} SMS messages from table")
                return messages
                
            except Exception as e:
                logger.error(f"Error checking for messages: {e}")
                return []
    
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        try:
            logger.info("Starting OTP monitoring bot...")
            
            # Initialize database
            await self.init_database()
            
            # Setup browser
            if not await self.setup_browser():
                logger.error("Failed to setup browser")
                return
            
            # Test Telegram connection
            if not await self.test_telegram_connection():
                logger.error("Failed to connect to Telegram")
                return
            
            # Login to website
            if not await self.login_to_website():
                logger.error("Failed to login to website")
                return
            
            logger.info("Starting INSTANT monitoring loop (rapid check → refresh → repeat)...")
            
            # Counters for periodic maintenance
            loop_count = 0
            browser_restart_count = 0
            
            while True:
                try:
                    logger.info("RAPID checking for new SMS messages...")
                    
                    # Check for new messages
                    messages = await self.check_for_new_messages()
                    logger.info(f"Found {len(messages)} total messages on page")
                    
                    # Process each message
                    new_messages_found = False
                    processed_count = 0
                    skipped_count = 0
                    
                    for row_data in messages:
                        sms_data = self.extract_sms_data(row_data)
                        if sms_data:
                            processed_count += 1
                            formatted_message = self.format_message(sms_data)
                            sent = await self.send_to_telegram(formatted_message, sms_data)
                            if sent:
                                logger.info(f"INSTANT OTP sent: {sms_data.get('country', 'Unknown')} - {sms_data.get('otp_code', 'Unknown')}")
                                new_messages_found = True
                        else:
                            skipped_count += 1
                    
                    logger.info(f"Message processing: {processed_count} processed, {skipped_count} skipped (old/invalid)")
                    
                    # If no new messages, use smart refresh strategy
                    if not new_messages_found:
                        # Don't do aggressive refresh every loop - this causes timeouts
                        if loop_count % 5 == 0:  # Only refresh every 5 loops (5 seconds)
                            logger.info("Performing strategic page refresh...")
                            try:
                                async with self.navigation_lock:
                                    await self.page.reload(wait_until="domcontentloaded", timeout=35000)
                                    await asyncio.sleep(1)
                            except Exception as refresh_error:
                                logger.warning(f"Page refresh failed: {refresh_error}")
                                # Continue without refresh - next check_for_new_messages will handle navigation
                    
                    # Increment counters
                    loop_count += 1
                    browser_restart_count += 1
                    
                    # Periodic database cleanup (every 500 loops - reduced frequency)
                    if loop_count % 500 == 0:
                        logger.info("Performing periodic database cleanup...")
                        await self.cleanup_old_hashes()
                    
                    # Memory monitoring and health check (every 10 loops for efficiency)
                    if loop_count % 10 == 0:
                        high_memory = self.log_memory_usage()
                        
                        # Check for persistent timeout errors (sign of session/network issues)
                        if loop_count % 50 == 0:  # Every 50 loops = every 50 seconds
                            logger.info("Performing health check and session validation...")
                            try:
                                # Quick session test
                                current_url = self.page.url
                                if 'login' in current_url.lower():
                                    logger.warning("Session expired detected during health check")
                                    await self.login_to_website()
                            except Exception as health_error:
                                logger.warning(f"Health check failed: {health_error}")
                        
                        # Restart browser if high memory OR after 600 loops (10 minutes for stability)
                        if high_memory or browser_restart_count >= 600:
                            if high_memory:
                                logger.info("Performing emergency browser restart due to high memory...")
                            else:
                                logger.info("Performing scheduled browser restart to prevent memory leaks...")
                            await self.restart_browser()
                            browser_restart_count = 0
                    
                    # Small delay for instant response (1 second for better stability)
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error in monitoring loop: {error_msg}")
                    
                    # Handle specific timeout errors
                    if 'timeout' in error_msg.lower() or 'err_aborted' in error_msg.lower():
                        logger.info("Detected timeout/abort error, attempting recovery...")
                        try:
                            # Force browser restart on persistent timeouts
                            await self.restart_browser()
                            browser_restart_count = 0
                            logger.info("Recovery browser restart completed")
                        except Exception as recovery_error:
                            logger.error(f"Recovery failed: {recovery_error}")
                    
                    await asyncio.sleep(3)  # Longer pause on error for stability
                    
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            # Cleanup
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

async def main():
    """Main async function for bot operation"""
    bot = OTPTelegramBot()
    await bot.run_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())