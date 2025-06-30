import csv
import io
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, make_response, session
from app import app, db
from models import LinkedInCredentials, ScrapeSession, Lead, ScrapingSettings
from scraper import LinkedInScraper
from utils import export_leads_to_csv, check_daily_lead_limit
from replit_auth import require_login, make_replit_blueprint
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# Register authentication blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Dashboard with overview statistics or landing page for logged out users"""
    if not current_user.is_authenticated:
        # Show landing page for logged out users
        return render_template('landing.html')
    
    # Show dashboard for logged in users
    total_leads = Lead.query.count()
    total_sessions = ScrapeSession.query.count()
    recent_sessions = ScrapeSession.query.order_by(ScrapeSession.created_at.desc()).limit(5).all()
    
    # Get completion stats
    completed_sessions = ScrapeSession.query.filter_by(status='completed').count()
    failed_sessions = ScrapeSession.query.filter_by(status='failed').count()
    
    return render_template('index.html', 
                         total_leads=total_leads,
                         total_sessions=total_sessions,
                         completed_sessions=completed_sessions,
                         failed_sessions=failed_sessions,
                         recent_sessions=recent_sessions)

@app.route('/leads')
@require_login
def leads():
    """View all leads with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query with filters
    query = Lead.query
    
    # Filter by company
    company_filter = request.args.get('company')
    if company_filter:
        query = query.filter(Lead.company.ilike(f'%{company_filter}%'))
    
    # Filter by role
    role_filter = request.args.get('role')
    if role_filter:
        query = query.filter(Lead.role.ilike(f'%{role_filter}%'))
    
    # Filter by contacted status
    contacted_filter = request.args.get('contacted')
    if contacted_filter == 'true':
        query = query.filter_by(contacted=True)
    elif contacted_filter == 'false':
        query = query.filter_by(contacted=False)
    
    leads_pagination = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique companies and roles for filter dropdowns
    companies = db.session.query(Lead.company).distinct().filter(Lead.company.isnot(None)).all()
    roles = db.session.query(Lead.role).distinct().filter(Lead.role.isnot(None)).all()
    
    return render_template('leads.html', 
                         leads=leads_pagination.items,
                         pagination=leads_pagination,
                         companies=[c[0] for c in companies],
                         roles=[r[0] for r in roles],
                         filters={
                             'company': company_filter,
                             'role': role_filter,
                             'contacted': contacted_filter
                         })

@app.route('/scrape', methods=['GET', 'POST'])
@require_login
def scrape():
    """Configure and start scraping session"""
    if request.method == 'POST':
        try:
            # Check daily limit first
            settings = ScrapingSettings.query.first()
            daily_limit = settings.max_leads_per_day if settings else 40
            limit_check = check_daily_lead_limit(daily_limit)
            
            if limit_check['limit_reached']:
                flash(f'Daily limit of {daily_limit} leads reached. You have scraped {limit_check["leads_today"]} leads today. Please try again tomorrow.', 'error')
                return redirect(url_for('scrape'))
            
            # Get form data
            search_query = request.form.get('search_query', '').strip()
            role_filter = request.form.get('role_filter', '').strip()
            company_filter = request.form.get('company_filter', '').strip()
            location_filter = request.form.get('location_filter', '').strip()
            max_results = int(request.form.get('max_results', 50))
            
            if not search_query:
                flash('Search query is required', 'error')
                return redirect(url_for('scrape'))
            
            # Enforce daily limit on max_results
            remaining_today = limit_check['remaining']
            if max_results > remaining_today:
                max_results = remaining_today
                flash(f'Adjusted results to {max_results} to stay within daily limit of {daily_limit} leads.', 'warning')
            
            # Create search filters object
            filters = {
                'role': role_filter,
                'company': company_filter,
                'location': location_filter,
                'max_results': max_results
            }
            
            # Create new scrape session
            session = ScrapeSession(
                search_query=search_query,
                search_filters=json.dumps(filters),
                status='pending'
            )
            db.session.add(session)
            db.session.commit()
            
            # Start scraping in background (for now, run synchronously)
            scraper = LinkedInScraper()
            success = scraper.scrape_prospects(session.id, search_query, filters)
            
            if success:
                flash(f'Scraping completed successfully! Session ID: {session.id}', 'success')
            else:
                flash('Scraping failed. Check logs for details.', 'error')
            
            return redirect(url_for('leads'))
            
        except Exception as e:
            logger.error(f"Error starting scrape session: {e}")
            flash(f'Error starting scraping: {str(e)}', 'error')
            return redirect(url_for('scrape'))
    
    # GET request - show scrape form
    # Check daily limit for display
    settings = ScrapingSettings.query.first()
    daily_limit = settings.max_leads_per_day if settings else 40
    limit_check = check_daily_lead_limit(daily_limit)
    
    return render_template('scrape.html', 
                         daily_limit=daily_limit,
                         limit_check=limit_check)

@app.route('/export_csv')
@require_login
def export_csv():
    """Export all leads to CSV"""
    try:
        # Get filter parameters
        company_filter = request.args.get('company')
        role_filter = request.args.get('role')
        contacted_filter = request.args.get('contacted')
        
        # Build query with filters
        query = Lead.query
        
        if company_filter:
            query = query.filter(Lead.company.ilike(f'%{company_filter}%'))
        if role_filter:
            query = query.filter(Lead.role.ilike(f'%{role_filter}%'))
        if contacted_filter == 'true':
            query = query.filter_by(contacted=True)
        elif contacted_filter == 'false':
            query = query.filter_by(contacted=False)
        
        leads = query.all()
        
        # Create CSV response
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Role', 'Company', 'Location', 'Industry', 
                        'Profile URL', 'Connections', 'Contacted', 'Connected', 'Notes', 'Created At'])
        
        # Write data
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.role or '',
                lead.company or '',
                lead.location or '',
                lead.industry or '',
                lead.profile_url or '',
                lead.connections or '',
                'Yes' if lead.contacted else 'No',
                'Yes' if lead.connected else 'No',
                lead.notes or '',
                lead.created_at.strftime('%Y-%m-%d %H:%M:%S') if lead.created_at else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=linkedin_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        flash(f'Error exporting CSV: {str(e)}', 'error')
        return redirect(url_for('leads'))

@app.route('/settings', methods=['GET', 'POST'])
@require_login
def settings():
    """Manage LinkedIn credentials and scraping settings"""
    if request.method == 'POST':
        try:
            form_type = request.form.get('form_type')
            
            if form_type == 'credentials':
                # Handle LinkedIn credentials
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '').strip()
                
                if not email or not password:
                    flash('Email and password are required', 'error')
                    return redirect(url_for('settings'))
                
                # Deactivate existing credentials
                LinkedInCredentials.query.update({'is_active': False})
                
                # Add new credentials
                credentials = LinkedInCredentials(email=email, password=password)
                db.session.add(credentials)
                db.session.commit()
                
                flash('LinkedIn credentials updated successfully', 'success')
                
            elif form_type == 'scraping_settings':
                # Handle scraping settings
                min_delay = float(request.form.get('min_delay', 2.0))
                max_delay = float(request.form.get('max_delay', 5.0))
                max_requests_per_hour = int(request.form.get('max_requests_per_hour', 30))
                max_leads_per_day = int(request.form.get('max_leads_per_day', 40))
                
                # Enforce maximum limits for safety
                max_leads_per_day = min(max_leads_per_day, 40)  # Hard limit at 40
                
                headless_mode = 'headless_mode' in request.form
                use_proxy = 'use_proxy' in request.form
                proxy_url = request.form.get('proxy_url', '').strip()
                
                # Get or create settings
                settings = ScrapingSettings.query.first()
                if not settings:
                    settings = ScrapingSettings()
                    db.session.add(settings)
                
                settings.min_delay = min_delay
                settings.max_delay = max_delay
                settings.max_requests_per_hour = max_requests_per_hour
                settings.max_leads_per_day = max_leads_per_day
                settings.headless_mode = headless_mode
                settings.use_proxy = use_proxy
                settings.proxy_url = proxy_url if use_proxy else None
                settings.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash('Scraping settings updated successfully', 'success')
            
            return redirect(url_for('settings'))
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            flash(f'Error updating settings: {str(e)}', 'error')
            return redirect(url_for('settings'))
    
    # GET request - show settings form
    active_credentials = LinkedInCredentials.query.filter_by(is_active=True).first()
    scraping_settings = ScrapingSettings.query.first()
    
    if not scraping_settings:
        scraping_settings = ScrapingSettings()
    
    return render_template('settings.html', 
                         credentials=active_credentials,
                         settings=scraping_settings)

@app.route('/update_lead/<int:lead_id>', methods=['POST'])
@require_login
def update_lead(lead_id):
    """Update lead status and notes"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        contacted = 'contacted' in request.form
        connected = 'connected' in request.form
        notes = request.form.get('notes', '').strip()
        
        lead.contacted = contacted
        lead.connected = connected
        lead.notes = notes
        lead.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Lead updated successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        flash(f'Error updating lead: {str(e)}', 'error')
    
    return redirect(url_for('leads'))

@app.route('/delete_lead/<int:lead_id>', methods=['POST'])
@require_login
def delete_lead(lead_id):
    """Delete a lead"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        db.session.delete(lead)
        db.session.commit()
        flash('Lead deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        flash(f'Error deleting lead: {str(e)}', 'error')
    
    return redirect(url_for('leads'))

@app.route('/sessions')
@require_login
def sessions():
    """View scraping sessions"""
    sessions = ScrapeSession.query.order_by(ScrapeSession.created_at.desc()).all()
    return render_template('sessions.html', sessions=sessions)
