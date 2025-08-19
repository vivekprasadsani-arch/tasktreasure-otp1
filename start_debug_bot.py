#!/usr/bin/env python3
"""
Start ONLY the Telegram Debug Bot for Render
Simple, focused debugging for Telegram response issues
"""

import os
import asyncio
import logging
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        status = f"""
        <html><head><title>Debug Bot Status</title></head><body>
        <h1>🔧 Telegram Debug Bot</h1>
        <p><strong>Status:</strong> ✅ Running</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Purpose:</strong> Debugging Telegram Response Issues</p>
        <p><strong>Bot Token:</strong> {'✅ Set' if os.getenv('BOT_TOKEN') else '❌ Missing'}</p>
        </body></html>
        """
        self.wfile.write(status.encode('utf-8'))
        
    def log_message(self, format, *args):
        pass

def start_health_server():
    """Start health server"""
    try:
        port = int(os.getenv('PORT', 10000))
        server = HTTPServer(('0.0.0.0', port), QuickHealthHandler)
        logger.info(f"🌐 Health server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

async def main():
    """Main function - run only debug bot"""
    logger.info("🔧 STARTING TELEGRAM DEBUG BOT ONLY")
    logger.info("=" * 50)
    
    try:
        # Import and run debug bot
        from render_debug_bot import DebugBot
        
        bot = DebugBot()
        logger.info("✅ Debug bot created")
        
        await bot.run_bot()
        
    except Exception as e:
        logger.error(f"❌ Debug bot failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🔧 Starting Debug Bot Only...")
    
    # Start health server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    time.sleep(1)
    
    # Start debug bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Debug bot stopped")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
