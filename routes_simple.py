import csv
import io
import json
from datetime import datetime
from flask import render_template_string, request, redirect, url_for, flash, make_response, session
from full_app import app, db
from models_simple import LinkedInCredentials, ScrapeSession, Lead, ScrapingSettings
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# Simple HTML templates
LANDING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Scraper - Professional Lead Generation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-body text-center p-5">
                        <h1 class="display-4 text-primary mb-4">LinkedIn Scraper</h1>
                        <p class="lead mb-4">Professional lead generation and prospect management platform</p>
                        
                        <div class="row mt-4">
                            <div class="col-md-4">
                                <div class="text-primary mb-3">
                                    <i class="fas fa-search fa-3x"></i>
                                </div>
                                <h5>Smart Scraping</h5>
                                <p>Find prospects based on your criteria</p>
                            </div>
                            <div class="col-md-4">
                                <div class="text-success mb-3">
                                    <i class="fas fa-database fa-3x"></i>
                                </div>
                                <h5>Lead Management</h5>
                                <p>Organize and track your leads</p>
                            </div>
                            <div class="col-md-4">
                                <div class="text-info mb-3">
                                    <i class="fas fa-file-export fa-3x"></i>
                                </div>
                                <h5>CSV Export</h5>
                                <p>Export to Google Sheets</p>
                            </div>
                        </div>
                        
                        <div class="mt-5">
                            <a href="/demo" class="btn btn-primary btn-lg me-3">View Demo</a>
                            <a href="/features" class="btn btn-outline-primary btn-lg">Learn More</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://kit.fontawesome.com/your-fontawesome-kit.js"></script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - LinkedIn Scraper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">LinkedIn Scraper</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/leads">Leads</a>
                <a class="nav-link" href="/scrape">Scrape</a>
                <a class="nav-link" href="/settings">Settings</a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="row">
            <div class="col-md-12">
                <h1>Dashboard</h1>
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-primary">{{ total_leads }}</h3>
                                <p>Total Leads</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-success">{{ total_sessions }}</h3>
                                <p>Scrape Sessions</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-info">{{ completed_sessions }}</h3>
                                <p>Completed</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h3 class="text-warning">{{ failed_sessions }}</h3>
                                <p>Failed</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h3>Quick Actions</h3>
                    <a href="/scrape" class="btn btn-primary me-2">Start Scraping</a>
                    <a href="/leads" class="btn btn-success me-2">View Leads</a>
                    <a href="/export_csv" class="btn btn-info">Export CSV</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

LEADS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Leads - LinkedIn Scraper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">LinkedIn Scraper</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link active" href="/leads">Leads</a>
                <a class="nav-link" href="/scrape">Scrape</a>
                <a class="nav-link" href="/settings">Settings</a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Leads ({{ leads|length }})</h1>
            <a href="/export_csv" class="btn btn-success">Export CSV</a>
        </div>
        
        {% if leads %}
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Role</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Contacted</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lead in leads %}
                    <tr>
                        <td>{{ lead.name }}</td>
                        <td>{{ lead.role or '-' }}</td>
                        <td>{{ lead.company or '-' }}</td>
                        <td>{{ lead.location or '-' }}</td>
                        <td>
                            {% if lead.contacted %}
                                <span class="badge bg-success">Yes</span>
                            {% else %}
                                <span class="badge bg-secondary">No</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if lead.profile_url %}
                                <a href="{{ lead.profile_url }}" target="_blank" class="btn btn-sm btn-outline-primary">View Profile</a>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="alert alert-info">
            <h4>No leads found</h4>
            <p>Start scraping to find prospects and build your lead database.</p>
            <a href="/scrape" class="btn btn-primary">Start Scraping</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Dashboard with overview statistics or landing page"""
    # Show dashboard since we're not using complex auth for now
    total_leads = Lead.query.count()
    total_sessions = ScrapeSession.query.count()
    completed_sessions = ScrapeSession.query.filter_by(status='completed').count()
    failed_sessions = ScrapeSession.query.filter_by(status='failed').count()
    
    return render_template_string(DASHBOARD_TEMPLATE,
                         total_leads=total_leads,
                         total_sessions=total_sessions,
                         completed_sessions=completed_sessions,
                         failed_sessions=failed_sessions)

@app.route('/leads')
def leads():
    """View all leads with filtering and pagination"""
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
    
    leads = query.order_by(Lead.created_at.desc()).all()
    
    return render_template_string(LEADS_TEMPLATE, leads=leads)

@app.route('/export_csv')
def export_csv():
    """Export all leads to CSV"""
    try:
        leads = Lead.query.all()
        
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

@app.route('/demo')
def demo():
    """Demo page showing sample data"""
    # Create sample leads for demo
    sample_leads = [
        {'name': 'John Smith', 'role': 'Software Engineer', 'company': 'Tech Corp', 'location': 'San Francisco, CA'},
        {'name': 'Sarah Johnson', 'role': 'Marketing Manager', 'company': 'Growth Inc', 'location': 'New York, NY'},
        {'name': 'Mike Davis', 'role': 'Sales Director', 'company': 'Sales Pro', 'location': 'Chicago, IL'},
    ]
    
    return render_template_string(LEADS_TEMPLATE.replace('{{ leads|length }}', str(len(sample_leads))), leads=sample_leads)

@app.route('/features')
def features():
    """Features page"""
    return render_template_string("""
    <div class="container py-5">
        <h1>Features</h1>
        <div class="row">
            <div class="col-md-6">
                <h3>Smart Lead Generation</h3>
                <p>Find prospects based on your specific criteria including role, company, and location.</p>
                
                <h3>Automated Data Collection</h3>
                <p>Automatically extract contact information, job titles, and company details.</p>
                
                <h3>Export Capabilities</h3>
                <p>Export your leads to CSV format for easy import into Google Sheets or CRM systems.</p>
            </div>
            <div class="col-md-6">
                <h3>Compliance Built-in</h3>
                <p>Respects rate limits and follows best practices for ethical data collection.</p>
                
                <h3>Real-time Tracking</h3>
                <p>Monitor your scraping sessions and track lead generation progress.</p>
                
                <h3>User-friendly Interface</h3>
                <p>Easy-to-use dashboard for managing leads and scraping sessions.</p>
            </div>
        </div>
        <div class="mt-4">
            <a href="/" class="btn btn-primary">Get Started</a>
        </div>
    </div>
    """)

@app.route('/scrape')
def scrape():
    """Scraping configuration page (placeholder)"""
    return render_template_string("""
    <div class="container py-5">
        <h1>Start Scraping</h1>
        <div class="alert alert-info">
            <h4>Scraping Feature</h4>
            <p>The full scraping functionality is being deployed. For now, you can:</p>
            <ul>
                <li>View the demo leads</li>
                <li>Test the CSV export feature</li>
                <li>Explore the dashboard</li>
            </ul>
            <p>Full LinkedIn scraping will be available soon!</p>
        </div>
        <a href="/demo" class="btn btn-primary">View Demo Data</a>
        <a href="/" class="btn btn-secondary">Back to Dashboard</a>
    </div>
    """)

@app.route('/settings')
def settings():
    """Settings page (placeholder)"""
    return render_template_string("""
    <div class="container py-5">
        <h1>Settings</h1>
        <div class="alert alert-info">
            <h4>Configuration Options</h4>
            <p>Settings panel for configuring:</p>
            <ul>
                <li>LinkedIn credentials</li>
                <li>Scraping parameters</li>
                <li>Export preferences</li>
                <li>Rate limiting options</li>
            </ul>
            <p>Full settings panel coming soon!</p>
        </div>
        <a href="/" class="btn btn-secondary">Back to Dashboard</a>
    </div>
    """)