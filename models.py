from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class LinkedInCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Should be encrypted in production
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

class ScrapeSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(500), nullable=False)
    search_filters = db.Column(db.Text)  # JSON string of filters
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    total_leads = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # Relationship to leads
    leads = db.relationship('Lead', backref='session', lazy=True, cascade='all, delete-orphan')

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
    
    # Foreign key to scrape session
    session_id = db.Column(db.Integer, db.ForeignKey('scrape_session.id'), nullable=False)
    
    # Status tracking
    contacted = db.Column(db.Boolean, default=False)
    connected = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    min_delay = db.Column(db.Float, default=2.0)  # Minimum delay between requests
    max_delay = db.Column(db.Float, default=5.0)  # Maximum delay between requests
    max_requests_per_hour = db.Column(db.Integer, default=30)
    max_leads_per_day = db.Column(db.Integer, default=40)  # Daily limit for compliance
    use_proxy = db.Column(db.Boolean, default=False)
    proxy_url = db.Column(db.String(500))
    headless_mode = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
