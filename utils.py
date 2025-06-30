import csv
import io
from datetime import datetime, timedelta
from models import Lead

def export_leads_to_csv(leads, filename=None):
    """Export leads to CSV format"""
    if not filename:
        filename = f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
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
    
    return output.getvalue()

def format_profile_url(url):
    """Clean and format LinkedIn profile URL"""
    if not url:
        return ''
    
    # Remove query parameters
    clean_url = url.split('?')[0]
    
    # Ensure it starts with https://
    if not clean_url.startswith('http'):
        clean_url = 'https://www.linkedin.com' + clean_url
    
    return clean_url

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_search_query(query):
    """Sanitize search query for LinkedIn"""
    if not query:
        return ''
    
    # Remove special characters that might cause issues
    import re
    sanitized = re.sub(r'[<>"\'\\\x00-\x1f\x7f-\x9f]', '', query)
    return sanitized.strip()

def check_daily_lead_limit(max_leads_per_day=40):
    """Check if daily lead limit has been reached"""
    from app import db
    
    # Get leads created today
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    leads_today = Lead.query.filter(
        Lead.created_at >= today_start,
        Lead.created_at <= today_end
    ).count()
    
    return {
        'leads_today': leads_today,
        'limit': max_leads_per_day,
        'remaining': max(0, max_leads_per_day - leads_today),
        'limit_reached': leads_today >= max_leads_per_day
    }
