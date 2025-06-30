#!/usr/bin/env python3
"""
Simple Chrome driver test without database dependencies
"""
import logging
import shutil
import os
from selenium import webdriver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chrome_simple():
    """Test Chrome driver initialization without database"""
    try:
        # Find Chrome binary
        chrome_binary = None
        possible_paths = [
            shutil.which('chromium'),
            shutil.which('google-chrome'),
            shutil.which('google-chrome-stable'),
            shutil.which('chromium-browser'),
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium'
        ]
        
        for path in possible_paths:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                chrome_binary = path
                logger.info(f"Found Chrome binary at: {chrome_binary}")
                break
        
        if not chrome_binary:
            logger.error("No Chrome binary found")
            return False
            
        options = webdriver.ChromeOptions()
        
        # Set binary location
        options.binary_location = chrome_binary
        
        # Add options for Replit compatibility
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless=new')
        options.add_argument('--disable-extensions')
        options.add_argument('--remote-debugging-port=9222')
        
        # Set user agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        logger.info("Initializing Chrome driver...")
        # Set ChromeDriver service with specific path
        from selenium.webdriver.chrome.service import Service
        chromedriver_path = shutil.which('chromedriver') or '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver'
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("Testing navigation...")
        driver.get("https://httpbin.org/user-agent")
        
        title = driver.title
        logger.info(f"Page title: {title}")
        
        driver.quit()
        logger.info("Chrome driver test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Chrome driver test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chrome_simple()
    if success:
        print("✓ Chrome driver test passed!")
    else:
        print("✗ Chrome driver test failed!")