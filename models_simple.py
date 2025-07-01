from datetime import datetime
from full_app import db
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# Simple User model for basic authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# OAuth model for authentication storage
class OAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    token = db.Column(db.Text)
    user = db.relationship(User)

# LinkedIn Credentials for scraping
class LinkedInCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

# Scraping Session tracking
class ScrapeSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(500), nullable=False)
    search_filters = db.Column(db.Text)  # JSON string of filters
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    total_leads = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    leads = db.relationship('Lead', backref='session', lazy=True, cascade='all, delete-orphan')

# Lead storage
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200))
    company = db.Column(db.String(200))
    profile_url = db.Column(db.String(500))
    location = db.Column(db.String(200))
    industry = db.Column(db.String(200))
    connections = db.Column(db.String(50))
    profile_image_url = db.Column(db.String(500))
    session_id = db.Column(db.Integer, db.ForeignKey('scrape_session.id'), nullable=False)
    contacted = db.Column(db.Boolean, default=False)
    connected = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Scraping Settings
class ScrapingSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    min_delay = db.Column(db.Float, default=2.0)
    max_delay = db.Column(db.Float, default=5.0)
    max_requests_per_hour = db.Column(db.Integer, default=30)
    max_leads_per_day = db.Column(db.Integer, default=40)
    use_proxy = db.Column(db.Boolean, default=False)
    proxy_url = db.Column(db.String(500))
    headless_mode = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)