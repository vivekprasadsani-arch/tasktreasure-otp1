#!/usr/bin/env python3
"""
Install Playwright browsers for deployment
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_browsers():
    """Install Playwright browsers"""
    try:
        logger.info("Installing Playwright browsers...")
        
        # Install all browsers first
        logger.info("Running: playwright install")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], capture_output=True, text=True, timeout=600)
        
        logger.info(f"Playwright install stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Playwright install stderr: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Failed to install all browsers, trying chromium only...")
            
            # Fallback: Install chromium only
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True, timeout=300)
            
            logger.info(f"Chromium install stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Chromium install stderr: {result.stderr}")
                
            if result.returncode != 0:
                logger.error("Failed to install chromium browser")
                return False
        
        logger.info("Browser installation completed")
        
        # Install system dependencies
        logger.info("Installing system dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install-deps"
        ], capture_output=True, text=True, timeout=300)
        
        logger.info(f"Install-deps stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Install-deps stderr: {result.stderr}")
        
        if result.returncode != 0:
            logger.warning("System dependencies installation had issues, but continuing...")
            
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Browser installation timed out")
        return False
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {e}")
        return False

if __name__ == "__main__":
    success = install_browsers()
    if success:
        logger.info("✅ Playwright setup completed successfully")
    else:
        logger.error("❌ Playwright setup failed")
        sys.exit(1)
