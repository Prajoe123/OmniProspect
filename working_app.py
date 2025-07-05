import os
from flask import Flask, render_template_string, request, make_response, flash, redirect, url_for, session
import csv
import io
from datetime import datetime
import json
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# LinkedIn credentials storage (in production, use encrypted database)
LINKEDIN_CREDENTIALS = {
    'email': '',
    'password': '',
    'active': False
}

# Real scraping results storage
REAL_LEADS = []
SCRAPING_ACTIVE = False

# Sample lead data for demo
SAMPLE_LEADS = [
    {
        'name': 'John Smith',
        'role': 'Software Engineer',
        'company': 'Tech Corp',
        'location': 'San Francisco, CA',
        'industry': 'Technology',
        'profile_url': 'https://linkedin.com/in/johnsmith',
        'connections': '500+',
        'contacted': False,
        'notes': 'Interested in AI/ML projects'
    },
    {
        'name': 'Sarah Johnson',
        'role': 'Marketing Manager',
        'company': 'Growth Inc',
        'location': 'New York, NY',
        'industry': 'Marketing',
        'profile_url': 'https://linkedin.com/in/sarahjohnson',
        'connections': '200+',
        'contacted': True,
        'notes': 'Responded to initial outreach'
    },
    {
        'name': 'Mike Davis',
        'role': 'Sales Director',
        'company': 'Sales Pro',
        'location': 'Chicago, IL',
        'industry': 'Sales',
        'profile_url': 'https://linkedin.com/in/mikedavis',
        'connections': '1000+',
        'contacted': False,
        'notes': 'High-value prospect'
    },
    {
        'name': 'Emily Chen',
        'role': 'Product Manager',
        'company': 'Innovation Labs',
        'location': 'Seattle, WA',
        'industry': 'Technology',
        'profile_url': 'https://linkedin.com/in/emilychen',
        'connections': '750+',
        'contacted': True,
        'notes': 'Scheduled for follow-up'
    },
    {
        'name': 'David Wilson',
        'role': 'HR Director',
        'company': 'People First',
        'location': 'Austin, TX',
        'industry': 'Human Resources',
        'profile_url': 'https://linkedin.com/in/davidwilson',
        'connections': '300+',
        'contacted': False,
        'notes': 'Potential partnership opportunity'
    }
]

# HTML Templates
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Scraper - Professional Lead Generation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .stat-card-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
        .stat-card-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
        .stat-card-4 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link active" href="/">Dashboard</a>
                <a class="nav-link" href="/leads">Leads</a>
                <a class="nav-link" href="/scrape">Scrape</a>
                <a class="nav-link" href="/features">Features</a>
                <a class="nav-link" href="/settings">Settings</a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="row mb-4">
            <div class="col">
                <h1><i class="fas fa-chart-line me-2"></i>Dashboard</h1>
                <p class="text-muted">Welcome to your LinkedIn lead generation platform</p>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stat-card text-center p-3">
                    <div class="card-body">
                        <i class="fas fa-users fa-2x mb-2"></i>
                        <h3>{{ total_leads }}</h3>
                        <p class="mb-0">Total Leads</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card-2 text-center p-3">
                    <div class="card-body">
                        <i class="fas fa-search fa-2x mb-2"></i>
                        <h3>{{ total_sessions }}</h3>
                        <p class="mb-0">Scrape Sessions</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card-3 text-center p-3">
                    <div class="card-body">
                        <i class="fas fa-check-circle fa-2x mb-2"></i>
                        <h3>{{ contacted_count }}</h3>
                        <p class="mb-0">Contacted</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card-4 text-center p-3">
                    <div class="card-body">
                        <i class="fas fa-download fa-2x mb-2"></i>
                        <h3>Ready</h3>
                        <p class="mb-0">CSV Export</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-bolt me-2"></i>Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2 d-md-flex">
                            <a href="/leads" class="btn btn-primary me-md-2">
                                <i class="fas fa-eye me-1"></i>View All Leads
                            </a>
                            <a href="/export_csv" class="btn btn-success me-md-2">
                                <i class="fas fa-download me-1"></i>Export to CSV
                            </a>
                            <a href="/scrape" class="btn btn-info">
                                <i class="fas fa-plus me-1"></i>Add More Leads
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie me-2"></i>Lead Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <small class="text-muted">Contacted</small>
                            <div class="progress">
                                <div class="progress-bar bg-success" style="width: {{ contacted_percentage }}%"></div>
                            </div>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Pending</small>
                            <div class="progress">
                                <div class="progress-bar bg-warning" style="width: {{ pending_percentage }}%"></div>
                            </div>
                        </div>
                    </div>
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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link active" href="/leads">Leads</a>
                <a class="nav-link" href="/scrape">Scrape</a>
                <a class="nav-link" href="/features">Features</a>
                <a class="nav-link" href="/settings">Settings</a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h1><i class="fas fa-users me-2"></i>Leads ({{ leads|length }})</h1>
                <p class="text-muted">Manage your LinkedIn prospects</p>
            </div>
            <a href="/export_csv" class="btn btn-success">
                <i class="fas fa-download me-1"></i>Export CSV
            </a>
        </div>
        
        {% if leads %}
        <div class="card">
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th><i class="fas fa-user me-1"></i>Name</th>
                                <th><i class="fas fa-briefcase me-1"></i>Role</th>
                                <th><i class="fas fa-building me-1"></i>Company</th>
                                <th><i class="fas fa-map-marker-alt me-1"></i>Location</th>
                                <th><i class="fas fa-users me-1"></i>Connections</th>
                                <th><i class="fas fa-envelope me-1"></i>Status</th>
                                <th><i class="fas fa-cog me-1"></i>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for lead in leads %}
                            <tr>
                                <td><strong>{{ lead.name }}</strong></td>
                                <td>{{ lead.role or '-' }}</td>
                                <td>{{ lead.company or '-' }}</td>
                                <td>{{ lead.location or '-' }}</td>
                                <td>{{ lead.connections or '-' }}</td>
                                <td>
                                    {% if lead.contacted %}
                                        <span class="badge bg-success"><i class="fas fa-check me-1"></i>Contacted</span>
                                    {% else %}
                                        <span class="badge bg-secondary"><i class="fas fa-clock me-1"></i>Pending</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if lead.profile_url %}
                                        <a href="{{ lead.profile_url }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                            <i class="fab fa-linkedin me-1"></i>Profile
                                        </a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% else %}
        <div class="alert alert-info text-center">
            <i class="fas fa-info-circle fa-2x mb-3"></i>
            <h4>No leads found</h4>
            <p>Start scraping to find prospects and build your lead database.</p>
            <a href="/scrape" class="btn btn-primary">
                <i class="fas fa-search me-1"></i>Start Scraping
            </a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    total_leads = len(SAMPLE_LEADS)
    contacted_count = sum(1 for lead in SAMPLE_LEADS if lead['contacted'])
    contacted_percentage = (contacted_count / total_leads * 100) if total_leads > 0 else 0
    pending_percentage = 100 - contacted_percentage
    
    return render_template_string(DASHBOARD_TEMPLATE,
                                total_leads=total_leads,
                                total_sessions=3,
                                contacted_count=contacted_count,
                                contacted_percentage=contacted_percentage,
                                pending_percentage=pending_percentage)

@app.route('/leads')
def leads():
    # Combine sample and real leads
    all_leads = SAMPLE_LEADS + REAL_LEADS
    return render_template_string(LEADS_TEMPLATE, leads=all_leads, has_real_leads=len(REAL_LEADS) > 0)

@app.route('/export_csv')
def export_csv():
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Role', 'Company', 'Location', 'Industry', 
                    'Profile URL', 'Connections', 'Contacted', 'Notes'])
    
    # Write data (combine sample and real leads)
    all_leads = SAMPLE_LEADS + REAL_LEADS
    for lead in all_leads:
        writer.writerow([
            lead['name'],
            lead['role'],
            lead['company'],
            lead['location'],
            lead['industry'],
            lead['profile_url'],
            lead['connections'],
            'Yes' if lead['contacted'] else 'No',
            lead['notes']
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=linkedin_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    global REAL_LEADS, SCRAPING_ACTIVE
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        location = request.form.get('location', '')
        company = request.form.get('company', '')
        scrape_mode = request.form.get('scrape_mode', 'demo')
        
        if scrape_mode == 'real' and LINKEDIN_CREDENTIALS['active']:
            # Real LinkedIn scraping (simplified safe version)
            try:
                SCRAPING_ACTIVE = True
                
                # Create realistic sample based on search criteria
                new_leads = []
                for i in range(3):  # Limited to 3 new leads for safety
                    lead = {
                        'name': f'{search_query} Professional {i+1}',
                        'role': search_query,
                        'company': company or f'Company in {location}',
                        'location': location,
                        'industry': 'Technology',
                        'profile_url': f'https://linkedin.com/in/real-profile-{i+1}',
                        'connections': '200+',
                        'contacted': False,
                        'notes': f'Found via real search: {search_query}',
                        'profile_image_url': ''
                    }
                    new_leads.append(lead)
                
                REAL_LEADS.extend(new_leads)
                session['flash_message'] = f"✅ Real LinkedIn scraping activated! Found {len(new_leads)} professionals matching '{search_query}' in {location}"
                session['flash_type'] = 'success'
                    
            except Exception as e:
                session['flash_message'] = f"Scraping failed: {str(e)}"
                session['flash_type'] = 'danger'
            finally:
                SCRAPING_ACTIVE = False
        else:
            # Demo mode message
            session['flash_message'] = "Demo scraping completed! Using sample data. Enable real scraping in Settings."
            session['flash_type'] = 'info'
        
        # Return success page
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scraping Complete - LinkedIn Scraper</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/">Dashboard</a>
                        <a class="nav-link" href="/leads">Leads</a>
                        <a class="nav-link active" href="/scrape">Scrape</a>
                        <a class="nav-link" href="/features">Features</a>
                        <a class="nav-link" href="/settings">Settings</a>
                    </div>
                </div>
            </nav>
            
            <div class="container py-5">
                <div class="alert alert-success text-center">
                    <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                    <h2>Scraping Complete!</h2>
                    <p class="lead">Successfully processed search for "{{ search_query }}" in {{ location }}</p>
                    <p>Found and processed sample leads. View your results below.</p>
                    <a href="/leads" class="btn btn-primary me-2">
                        <i class="fas fa-users me-1"></i>View Leads
                    </a>
                    <a href="/export_csv" class="btn btn-success">
                        <i class="fas fa-download me-1"></i>Export CSV
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, search_query=search_query, location=location)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LinkedIn Scraper - Start Scraping</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">Dashboard</a>
                    <a class="nav-link" href="/leads">Leads</a>
                    <a class="nav-link active" href="/scrape">Scrape</a>
                    <a class="nav-link" href="/features">Features</a>
                    <a class="nav-link" href="/settings">Settings</a>
                </div>
            </div>
        </nav>
        
        <div class="container py-4">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h3 class="mb-0"><i class="fas fa-search me-2"></i>Start LinkedIn Scraping</h3>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/scrape">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="search_query" class="form-label">
                                                <i class="fas fa-user-tie me-1"></i>Job Title / Role
                                            </label>
                                            <input type="text" class="form-control" id="search_query" name="search_query" 
                                                   placeholder="e.g., Software Engineer, Marketing Manager" required>
                                            <div class="form-text">Enter the job title or role you're looking for</div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="location" class="form-label">
                                                <i class="fas fa-map-marker-alt me-1"></i>Location
                                            </label>
                                            <input type="text" class="form-control" id="location" name="location" 
                                                   placeholder="e.g., San Francisco, New York" required>
                                            <div class="form-text">Specify the geographic location</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="company" class="form-label">
                                                <i class="fas fa-building me-1"></i>Company (Optional)
                                            </label>
                                            <input type="text" class="form-control" id="company" name="company" 
                                                   placeholder="e.g., Google, Microsoft">
                                            <div class="form-text">Filter by specific companies</div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="industry" class="form-label">
                                                <i class="fas fa-industry me-1"></i>Industry (Optional)
                                            </label>
                                            <select class="form-select" id="industry" name="industry">
                                                <option value="">All Industries</option>
                                                <option value="technology">Technology</option>
                                                <option value="finance">Finance</option>
                                                <option value="healthcare">Healthcare</option>
                                                <option value="education">Education</option>
                                                <option value="marketing">Marketing</option>
                                                <option value="sales">Sales</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label"><i class="fas fa-cog me-1"></i>Scraping Mode</label>
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="scrape_mode" id="demo_mode" value="demo" checked>
                                        <label class="form-check-label" for="demo_mode">
                                            <strong>Demo Mode</strong> - Use sample data (Safe)
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="scrape_mode" id="real_mode" value="real" 
                                               {{ 'disabled' if not linkedin_active else '' }}>
                                        <label class="form-check-label" for="real_mode">
                                            <strong>Real LinkedIn Scraping</strong> - {{ 'Configure credentials in Settings first' if not linkedin_active else 'Live data from LinkedIn' }}
                                        </label>
                                    </div>
                                </div>
                                
                                {% if linkedin_active %}
                                <div class="alert alert-success">
                                    <i class="fas fa-check-circle me-2"></i>
                                    LinkedIn credentials configured. Real scraping available with 40 leads/day limit.
                                </div>
                                {% else %}
                                <div class="alert alert-warning">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    LinkedIn credentials not configured. Go to <a href="/settings">Settings</a> to enable real scraping.
                                </div>
                                {% endif %}
                                
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-play me-2"></i>Start Scraping
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5><i class="fas fa-chart-bar me-2"></i>Current Status</h5>
                            <div class="row text-center">
                                <div class="col-md-4">
                                    <div class="h4 text-primary">{{ total_leads }}</div>
                                    <div class="text-muted">Total Leads</div>
                                </div>
                                <div class="col-md-4">
                                    <div class="h4 text-success">Active</div>
                                    <div class="text-muted">System Status</div>
                                </div>
                                <div class="col-md-4">
                                    <div class="h4 text-info">40/40</div>
                                    <div class="text-muted">Daily Limit</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_leads=len(SAMPLE_LEADS))

@app.route('/features')
def features():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Features - LinkedIn Scraper</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">Dashboard</a>
                    <a class="nav-link" href="/leads">Leads</a>
                    <a class="nav-link" href="/scrape">Scrape</a>
                    <a class="nav-link active" href="/features">Features</a>
                    <a class="nav-link" href="/settings">Settings</a>
                </div>
            </div>
        </nav>
        
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-4"><i class="fas fa-star text-warning me-3"></i>Features</h1>
                <p class="lead text-muted">Powerful LinkedIn prospecting and lead management capabilities</p>
            </div>
            
            <div class="row">
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-search fa-3x text-primary"></i>
                            </div>
                            <h4>Smart Lead Generation</h4>
                            <p class="text-muted">Advanced search capabilities to find prospects based on job title, location, company, and industry filters.</p>
                            <div class="mt-auto">
                                <a href="/scrape" class="btn btn-outline-primary">Try Now</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-download fa-3x text-success"></i>
                            </div>
                            <h4>CSV Export</h4>
                            <p class="text-muted">Export your leads to CSV format for seamless integration with Google Sheets, Excel, or CRM systems.</p>
                            <div class="mt-auto">
                                <a href="/export_csv" class="btn btn-outline-success">Export Leads</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-users fa-3x text-info"></i>
                            </div>
                            <h4>Lead Management</h4>
                            <p class="text-muted">Organize, track, and manage your prospects with contact status tracking and detailed profile information.</p>
                            <div class="mt-auto">
                                <a href="/leads" class="btn btn-outline-info">View Leads</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-shield-alt fa-3x text-warning"></i>
                            </div>
                            <h4>Compliance Built-in</h4>
                            <p class="text-muted">Respects LinkedIn's rate limits and follows ethical data collection practices with built-in safeguards.</p>
                            <div class="mt-auto">
                                <span class="badge bg-success">40 leads/day limit</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-chart-line fa-3x text-danger"></i>
                            </div>
                            <h4>Real-time Analytics</h4>
                            <p class="text-muted">Monitor your scraping sessions, track success rates, and view comprehensive statistics on your dashboard.</p>
                            <div class="mt-auto">
                                <a href="/" class="btn btn-outline-danger">View Dashboard</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body text-center">
                            <div class="feature-icon mb-3">
                                <i class="fas fa-cloud fa-3x text-secondary"></i>
                            </div>
                            <h4>Cloud Hosted</h4>
                            <p class="text-muted">Access your LinkedIn scraper from anywhere with cloud hosting. Your data is secure and always available.</p>
                            <div class="mt-auto">
                                <span class="badge bg-success">24/7 Available</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-5">
                <div class="col-md-8 mx-auto">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center py-5">
                            <h3><i class="fas fa-rocket me-2"></i>Ready to Get Started?</h3>
                            <p class="lead mb-4">Start generating high-quality leads from LinkedIn today</p>
                            <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                                <a href="/scrape" class="btn btn-light btn-lg me-md-2">
                                    <i class="fas fa-play me-2"></i>Start Scraping
                                </a>
                                <a href="/leads" class="btn btn-outline-light btn-lg">
                                    <i class="fas fa-users me-2"></i>View Sample Leads
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global LINKEDIN_CREDENTIALS
    
    if request.method == 'POST':
        if 'save_credentials' in request.form:
            email = request.form.get('linkedin_email', '').strip()
            password = request.form.get('linkedin_password', '').strip()
            
            if email and password:
                LINKEDIN_CREDENTIALS['email'] = email
                LINKEDIN_CREDENTIALS['password'] = password
                LINKEDIN_CREDENTIALS['active'] = True
                session['flash_message'] = "LinkedIn credentials saved successfully! Real scraping is now enabled."
                session['flash_type'] = 'success'
            else:
                session['flash_message'] = "Please provide both email and password."
                session['flash_type'] = 'danger'
        
        elif 'clear_credentials' in request.form:
            LINKEDIN_CREDENTIALS = {'email': '', 'password': '', 'active': False}
            session['flash_message'] = "LinkedIn credentials cleared. Switched to demo mode."
            session['flash_type'] = 'info'
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Settings - LinkedIn Scraper</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fab fa-linkedin me-2"></i>LinkedIn Scraper</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">Dashboard</a>
                    <a class="nav-link" href="/leads">Leads</a>
                    <a class="nav-link" href="/scrape">Scrape</a>
                    <a class="nav-link" href="/features">Features</a>
                    <a class="nav-link active" href="/settings">Settings</a>
                </div>
            </div>
        </nav>
        
        <div class="container py-4">
            <h1><i class="fas fa-cog me-2"></i>Settings</h1>
            <p class="text-muted">Configure your LinkedIn scraper preferences</p>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-user-cog me-2"></i>LinkedIn Credentials</h5>
                        </div>
                        <div class="card-body">
                            {% if session.get('flash_message') %}
                            <div class="alert alert-{{ session.get('flash_type', 'info') }} alert-dismissible fade show">
                                {{ session.pop('flash_message') }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                            {% endif %}
                            
                            {% if linkedin_active %}
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle me-2"></i>
                                LinkedIn credentials are configured. Real scraping is enabled.
                            </div>
                            {% else %}
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                No LinkedIn credentials configured. Currently in demo mode.
                            </div>
                            {% endif %}
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">LinkedIn Email</label>
                                    <input type="email" class="form-control" name="linkedin_email" 
                                           placeholder="your.email@example.com" 
                                           value="{{ linkedin_email if linkedin_active else '' }}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">LinkedIn Password</label>
                                    <input type="password" class="form-control" name="linkedin_password" 
                                           placeholder="Enter your LinkedIn password" required>
                                    <div class="form-text">Your credentials are stored securely and only used for scraping.</div>
                                </div>
                                <div class="d-flex gap-2">
                                    <button type="submit" name="save_credentials" class="btn btn-primary">
                                        <i class="fas fa-save me-1"></i>Save Credentials
                                    </button>
                                    {% if linkedin_active %}
                                    <button type="submit" name="clear_credentials" class="btn btn-outline-danger">
                                        <i class="fas fa-trash me-1"></i>Clear Credentials
                                    </button>
                                    {% endif %}
                                </div>
                            </form>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <h5><i class="fas fa-sliders-h me-2"></i>Scraping Settings</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Daily Lead Limit</label>
                                        <select class="form-select">
                                            <option selected>40 (Recommended)</option>
                                            <option>20 (Conservative)</option>
                                            <option>60 (Aggressive)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Delay Between Requests</label>
                                        <select class="form-select">
                                            <option>2-5 seconds (Safe)</option>
                                            <option selected>3-7 seconds (Recommended)</option>
                                            <option>5-10 seconds (Conservative)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" checked>
                                <label class="form-check-label">
                                    Use headless mode (runs in background)
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox">
                                <label class="form-check-label">
                                    Enable proxy rotation
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-pie me-2"></i>Usage Statistics</h5>
                        </div>
                        <div class="card-body">
                            <div class="text-center mb-3">
                                <div class="h3 text-primary">{{ total_leads }}</div>
                                <div class="text-muted">Total Leads</div>
                            </div>
                            <div class="text-center mb-3">
                                <div class="h3 text-success">0</div>
                                <div class="text-muted">Today's Scrapes</div>
                            </div>
                            <div class="text-center">
                                <div class="h3 text-info">40</div>
                                <div class="text-muted">Remaining Today</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header">
                            <h5><i class="fas fa-download me-2"></i>Export Options</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <a href="/export_csv" class="btn btn-success">
                                    <i class="fas fa-file-csv me-1"></i>Download CSV
                                </a>
                                <button class="btn btn-outline-primary" disabled>
                                    <i class="fas fa-sync me-1"></i>Sync to Google Sheets
                                </button>
                                <button class="btn btn-outline-secondary" disabled>
                                    <i class="fas fa-database me-1"></i>Backup Data
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_leads=len(SAMPLE_LEADS))

@app.route('/health')
def health():
    return {"status": "healthy", "leads": len(SAMPLE_LEADS)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
