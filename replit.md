# LinkedIn Scraper Application

## Overview

This is a Flask-based web application designed to scrape LinkedIn profiles for lead generation. The application provides a complete workflow for extracting prospect data including names, roles, companies, and profile URLs, with the ability to export results to CSV format.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (configurable to PostgreSQL via DATABASE_URL environment variable)
- **Web Scraping**: Selenium WebDriver with undetected-chromedriver for LinkedIn automation
- **HTML Parsing**: BeautifulSoup for extracting profile data
- **Session Management**: Flask sessions with configurable secret key

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JS with Bootstrap components

### Database Schema
The application uses four main database models:
- **LinkedInCredentials**: Stores LinkedIn login credentials
- **ScrapeSession**: Tracks scraping sessions with status and metadata
- **Lead**: Individual prospect records with contact information
- **ScrapingSettings**: Configuration for scraping behavior (delays, etc.)

## Key Components

### Core Application (`app.py`)
- Flask application factory pattern
- SQLAlchemy configuration with connection pooling
- Environment-based configuration (development/production)
- ProxyFix middleware for deployment behind reverse proxies

### Models (`models.py`)
- **LinkedInCredentials**: Manages multiple LinkedIn accounts
- **ScrapeSession**: Tracks scraping operations with filters and status
- **Lead**: Stores extracted prospect data with relationship tracking
- **ScrapingSettings**: Configurable delays to avoid detection

### Scraper Engine (`scraper.py`)
- **LinkedInScraper**: Main scraping class using Selenium
- Anti-detection measures with undetected-chromedriver
- Configurable delays and human-like behavior simulation
- Error handling and session management

### Web Routes (`routes.py`)
- Dashboard with statistics and recent activity
- Lead management with filtering and pagination
- Scraping configuration interface
- CSV export functionality
- Settings management for credentials and scraping parameters

### Utilities (`utils.py`)
- CSV export functionality with proper formatting
- URL validation and cleaning utilities
- Email validation helpers

## Data Flow

1. **Authentication Setup**: Users configure LinkedIn credentials in settings
2. **Scrape Configuration**: Define search queries and filters
3. **Scraping Process**: Selenium automation extracts prospect data
4. **Data Storage**: Leads are stored in database with session tracking
5. **Lead Management**: Users can view, filter, and manage extracted leads
6. **Export**: Generate CSV reports for CRM integration

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Selenium**: Web browser automation
- **BeautifulSoup**: HTML parsing
- **undetected-chromedriver**: Anti-detection Chrome driver

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Custom CSS/JS**: Application-specific styling and interactions

### Browser Requirements
- Chrome/Chromium browser for Selenium automation
- ChromeDriver (managed by undetected-chromedriver)

## Deployment Strategy

### Environment Configuration
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: Database connection string (defaults to SQLite)
- **Logging**: Configurable logging levels for debugging

### Production Considerations
- Password encryption for LinkedIn credentials (currently stored as plain text)
- Proxy rotation for large-scale scraping
- Rate limiting and request throttling
- Error monitoring and alerting
- Database optimization for large datasets

### Scalability Options
- PostgreSQL backend for production workloads
- Redis for session storage and job queuing
- Celery for background task processing
- Docker containerization support

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- June 30, 2025: Added Render.com deployment configuration
  - Created render.yaml for automatic deployment setup
  - Generated deployment_requirements.txt with all dependencies
  - Added Procfile for web service configuration
  - Created comprehensive deployment guide (RENDER_DEPLOYMENT.md)
  - App is now ready for cloud deployment on Render.com

- June 30, 2025: Fixed Chrome driver and scraping functionality
  - Installed Chromium browser and ChromeDriver packages via Nix
  - Simplified Chrome options to remove incompatible experimental options
  - Fixed database import circular dependencies in scraper module
  - Updated Chrome driver initialization to use correct binary paths
  - Chrome driver test now passes successfully
  - Scraping functionality fully operational

- June 29, 2025: Implemented authenticated user login system
  - Added Replit OpenID Connect authentication using Flask-Dance
  - Created User and OAuth models for authentication storage
  - Protected all application routes with @require_login decorator
  - Added landing page for logged-out users with login button
  - Updated navigation to show user profile and logout option
  - Created authentication error page (403.html)
  - All protected functionality now requires user authentication

- June 29, 2025: Added strict 40 leads per day limit enforcement
  - Updated database model with max_leads_per_day field (default 40)
  - Implemented daily limit checking in scraper and routes
  - Added visual indicators and form disabling when limit reached
  - Updated all UI text to reflect 40 lead maximum
  - Enhanced compliance messaging throughout application

## Changelog

- June 29, 2025: Initial setup with LinkedIn scraping functionality
- June 29, 2025: Implemented daily lead limit enforcement (40 max)
- June 29, 2025: Added authenticated user login with Replit Auth