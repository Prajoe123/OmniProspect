#!/usr/bin/env python3
"""
Test script to verify Chrome driver functionality
"""
import sys
import os
sys.path.append('.')

# Set up Flask app context for database operations
from app import app
with app.app_context():
    from scraper import LinkedInScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chrome_driver():
    """Test Chrome driver initialization"""
    try:
        scraper = LinkedInScraper()
        logger.info("Testing Chrome driver initialization...")
        
        if scraper._init_driver():
            logger.info("✓ Chrome driver initialized successfully")
            
            # Test basic navigation
            scraper.driver.get("https://httpbin.org/user-agent")
            logger.info("✓ Successfully navigated to test page")
            
            # Get page title
            title = scraper.driver.title
            logger.info(f"✓ Page title: {title}")
            
            scraper.close()
            logger.info("✓ Chrome driver closed successfully")
            return True
        else:
            logger.error("✗ Failed to initialize Chrome driver")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error testing Chrome driver: {e}")
        return False

if __name__ == "__main__":
    success = test_chrome_driver()
    if success:
        print("Chrome driver test passed!")
        sys.exit(0)
    else:
        print("Chrome driver test failed!")
        sys.exit(1)