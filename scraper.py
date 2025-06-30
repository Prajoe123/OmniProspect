import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
try:
    import undetected_chromedriver as uc
except ImportError:
    # Fallback to regular Chrome driver if undetected is not available
    uc = None
from models import LinkedInCredentials, ScrapeSession, Lead, ScrapingSettings

logger = logging.getLogger(__name__)

# Import database context
def get_db():
    from app import db
    return db

# Initialize db reference at module level to avoid repeated imports
db = None

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.db = None
        # Initialize database and settings
        self._init_db()
        self.settings = ScrapingSettings.query.first()
        if not self.settings:
            self.settings = ScrapingSettings()
    
    def _init_db(self):
        """Initialize database connection"""
        if not self.db:
            global db
            if not db:
                db = get_db()
            self.db = db
        
    def _init_driver(self):
        """Initialize Chrome driver with proper options"""
        try:
            import shutil
            import os
            
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
                '/snap/bin/chromium',
                '/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium'
            ]
            
            for path in possible_paths:
                if path and os.path.isfile(path) and os.access(path, os.X_OK):
                    chrome_binary = path
                    logger.info(f"Found Chrome binary at: {chrome_binary}")
                    break
            
            options = webdriver.ChromeOptions()
            
            # Set binary location if found
            if chrome_binary:
                options.binary_location = chrome_binary
            
            # Essential options for Replit compatibility
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--remote-debugging-port=0')
            
            if self.settings and self.settings.headless_mode:
                options.add_argument('--headless=new')
            else:
                # Always run headless in cloud environments
                options.add_argument('--headless=new')
            
            # Set user agent
            options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Initialize driver with ChromeDriver service
            from selenium.webdriver.chrome.service import Service
            chromedriver_path = '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver'
            service = Service(chromedriver_path)
            
            logger.info("Initializing Chrome driver with simplified configuration")
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide automation
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except:
                pass  # Ignore if this fails
                
            logger.info("Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return False
    
    def _random_delay(self):
        """Add random delay between actions"""
        delay = random.uniform(self.settings.min_delay, self.settings.max_delay)
        time.sleep(delay)
    
    def login(self):
        """Login to LinkedIn"""
        try:
            credentials = LinkedInCredentials.query.filter_by(is_active=True).first()
            if not credentials:
                logger.error("No active LinkedIn credentials found")
                return False
            
            if not self.driver:
                if not self._init_driver():
                    return False
            
            logger.info("Attempting to login to LinkedIn")
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            
            # Enter email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            for char in credentials.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Human-like typing
            
            self._random_delay()
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            for char in credentials.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._random_delay()
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait briefly for redirect 
            time.sleep(2)
            
            # Check if we're logged in with shorter timeout to prevent worker timeout
            wait = WebDriverWait(self.driver, 8)  # Reduced from 30 seconds
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "global-nav")),
                    EC.presence_of_element_located((By.CLASS_NAME, "feed-container")),
                    EC.url_contains("linkedin.com/feed")
                ))
                self.is_logged_in = True
                credentials.last_used = datetime.utcnow()
                self.db.session.commit()
                logger.info("Successfully logged in to LinkedIn")
                return True
                
            except TimeoutException:
                logger.error("Login failed - timeout waiting for main page")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def search_prospects(self, search_query, filters=None):
        """Search for prospects on LinkedIn"""
        try:
            if not self.is_logged_in:
                if not self.login():
                    return []
            
            # Build search URL
            base_url = "https://www.linkedin.com/search/results/people/"
            params = f"?keywords={search_query.replace(' ', '%20')}"
            
            # Add filters if provided
            if filters:
                if filters.get('location'):
                    params += f"&geoUrn={filters['location']}"
                if filters.get('company'):
                    params += f"&currentCompany={filters['company']}"
            
            search_url = base_url + params
            logger.info(f"Searching with URL: {search_url}")
            
            self.driver.get(search_url)
            self._random_delay()
            
            # Scroll to load more results
            max_scrolls = min(5, filters.get('max_results', 50) // 10)
            for i in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay()
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            prospects = self._parse_search_results(soup)
            
            # Limit results
            max_results = filters.get('max_results', 50) if filters else 50
            return prospects[:max_results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _parse_search_results(self, soup):
        """Parse LinkedIn search results from BeautifulSoup"""
        prospects = []
        
        try:
            # Look for search result containers
            result_containers = soup.find_all('div', class_='entity-result__item')
            
            if not result_containers:
                # Try alternative selectors
                result_containers = soup.find_all('li', class_='reusable-search__result-container')
            
            logger.info(f"Found {len(result_containers)} prospect containers")
            
            for container in result_containers:
                try:
                    prospect = self._extract_prospect_data(container)
                    if prospect and prospect.get('name'):
                        prospects.append(prospect)
                except Exception as e:
                    logger.warning(f"Failed to parse prospect container: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")
        
        return prospects
    
    def _extract_prospect_data(self, container):
        """Extract prospect data from a result container"""
        prospect = {}
        
        try:
            # Name and profile URL
            name_link = container.find('a', class_='app-aware-link') or container.find('a', href=lambda x: x and '/in/' in x)
            if name_link:
                prospect['name'] = name_link.get_text(strip=True)
                prospect['profile_url'] = name_link.get('href', '').split('?')[0]
            
            # Role/Title
            role_elem = container.find('div', class_='entity-result__primary-subtitle') or \
                       container.find('div', class_='entity-result__summary')
            if role_elem:
                prospect['role'] = role_elem.get_text(strip=True)
            
            # Company
            company_elem = container.find('div', class_='entity-result__secondary-subtitle')
            if company_elem:
                prospect['company'] = company_elem.get_text(strip=True)
            
            # Location (if available)
            location_elem = container.find('div', class_='entity-result__location')
            if location_elem:
                prospect['location'] = location_elem.get_text(strip=True)
            
            # Profile image
            img_elem = container.find('img', class_='presence-entity__image')
            if img_elem:
                prospect['profile_image_url'] = img_elem.get('src', '')
            
            return prospect
            
        except Exception as e:
            logger.warning(f"Failed to extract prospect data: {e}")
            return {}
    
    def scrape_prospects(self, session_id, search_query, filters=None):
        """Main scraping method"""
        try:
            # Update session status
            session = self.db.session.get(ScrapeSession, session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            session.status = 'running'
            self.db.session.commit()
            
            logger.info(f"Starting scrape session {session_id} with query: {search_query}")
            
            # Check daily limit before scraping
            from utils import check_daily_lead_limit
            settings = ScrapingSettings.query.first()
            daily_limit = settings.max_leads_per_day if settings else 40
            limit_check = check_daily_lead_limit(daily_limit)
            
            if limit_check['limit_reached']:
                session.status = 'failed'
                session.error_message = f'Daily limit of {daily_limit} leads reached. Already scraped {limit_check["leads_today"]} leads today.'
                session.completed_at = datetime.utcnow()
                db.session.commit()
                logger.warning(f"Daily limit reached: {limit_check['leads_today']}/{daily_limit}")
                return False
            
            # Adjust max_results to respect daily limit
            if filters:
                remaining_today = limit_check['remaining']
                if filters.get('max_results', 50) > remaining_today:
                    filters['max_results'] = remaining_today
                    logger.info(f"Adjusted max_results to {remaining_today} to respect daily limit")
            
            # Check if LinkedIn credentials are configured before attempting login
            credentials = self.db.session.query(LinkedInCredentials).filter_by(is_active=True).first()
            if not credentials:
                logger.error("No LinkedIn credentials configured")
                session.status = 'failed'
                session.error_message = "LinkedIn credentials not configured. Please add your LinkedIn login details in Settings."
                self.db.session.commit()
                return False

            # Initialize driver if not already done
            if not self.driver:
                if not self._init_driver():
                    session.status = 'failed'
                    session.error_message = "Failed to initialize browser driver"
                    self.db.session.commit()
                    return False

            # Search for prospects with timeout protection
            try:
                prospects = self.search_prospects(search_query, filters)
            except Exception as search_error:
                logger.error(f"Search failed: {search_error}")
                session.status = 'failed'
                session.error_message = f"Search failed: {str(search_error)}"
                self.db.session.commit()
                return False
            
            if not prospects:
                session.status = 'completed'
                session.error_message = 'No prospects found or search failed'
                session.completed_at = datetime.utcnow()
                db.session.commit()
                return False
            
            # Save prospects to database with daily limit enforcement
            saved_count = 0
            for prospect_data in prospects:
                try:
                    # Double-check daily limit during processing
                    current_limit_check = check_daily_lead_limit(daily_limit)
                    if current_limit_check['limit_reached']:
                        logger.warning(f"Daily limit reached during processing. Stopping at {saved_count} leads.")
                        break
                    
                    # Check if lead already exists
                    existing_lead = Lead.query.filter_by(
                        profile_url=prospect_data.get('profile_url')
                    ).first()
                    
                    if existing_lead:
                        logger.info(f"Lead already exists: {prospect_data.get('name')}")
                        continue
                    
                    lead = Lead(
                        name=prospect_data.get('name', ''),
                        role=prospect_data.get('role', ''),
                        company=prospect_data.get('company', ''),
                        profile_url=prospect_data.get('profile_url', ''),
                        location=prospect_data.get('location', ''),
                        profile_image_url=prospect_data.get('profile_image_url', ''),
                        session_id=session_id
                    )
                    
                    self.db.session.add(lead)
                    saved_count += 1
                    
                    # Commit after each lead to update the count
                    self.db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to save lead: {e}")
                    continue
            
            # Update session
            session.status = 'completed'
            session.total_leads = saved_count
            session.completed_at = datetime.utcnow()
            self.db.session.commit()
            
            logger.info(f"Scrape session {session_id} completed. Saved {saved_count} leads.")
            return True
            
        except Exception as e:
            logger.error(f"Scrape session {session_id} failed: {e}")
            
            # Update session with error
            session = ScrapeSession.query.get(session_id)
            if session:
                session.status = 'failed'
                session.error_message = str(e)
                session.completed_at = datetime.utcnow()
                db.session.commit()
            
            return False
        
        finally:
            # Always close the driver
            self.close()
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                logger.info("Browser driver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
