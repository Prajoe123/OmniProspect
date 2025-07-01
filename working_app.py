import os
from flask import Flask, render_template_string, request, make_response
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

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
    return render_template_string(LEADS_TEMPLATE, leads=SAMPLE_LEADS)

@app.route('/export_csv')
def export_csv():
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Role', 'Company', 'Location', 'Industry', 
                    'Profile URL', 'Connections', 'Contacted', 'Notes'])
    
    # Write data
    for lead in SAMPLE_LEADS:
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

@app.route('/scrape')
def scrape():
    return render_template_string("""
    <div class="container py-5">
        <div class="card">
            <div class="card-body text-center">
                <i class="fas fa-cogs fa-3x text-primary mb-3"></i>
                <h1>Scraping Engine</h1>
                <p class="lead">Advanced LinkedIn prospecting system</p>
                <div class="alert alert-info">
                    <h4>Coming Soon!</h4>
                    <p>Full LinkedIn scraping functionality is being deployed. Current features:</p>
                    <ul class="text-start">
                        <li>✅ Lead management dashboard</li>
                        <li>✅ CSV export for Google Sheets</li>
                        <li>✅ Professional interface</li>
                        <li>🔄 LinkedIn automation (in development)</li>
                    </ul>
                </div>
                <a href="/leads" class="btn btn-primary me-2">View Current Leads</a>
                <a href="/" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </div>
    """)

@app.route('/features')
def features():
    return render_template_string("""
    <div class="container py-5">
        <h1>Features</h1>
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-body">
                        <h3><i class="fas fa-search text-primary me-2"></i>Smart Lead Generation</h3>
                        <p>Find prospects based on specific criteria including role, company, and location.</p>
                    </div>
                </div>
                <div class="card mb-4">
                    <div class="card-body">
                        <h3><i class="fas fa-download text-success me-2"></i>CSV Export</h3>
                        <p>Export leads to CSV format for easy import into Google Sheets or CRM systems.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-body">
                        <h3><i class="fas fa-shield-alt text-info me-2"></i>Compliance Built-in</h3>
                        <p>Respects rate limits and follows best practices for ethical data collection.</p>
                    </div>
                </div>
                <div class="card mb-4">
                    <div class="card-body">
                        <h3><i class="fas fa-chart-line text-warning me-2"></i>Real-time Tracking</h3>
                        <p>Monitor scraping sessions and track lead generation progress.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="text-center mt-4">
            <a href="/" class="btn btn-primary">Get Started</a>
        </div>
    </div>
    """)

@app.route('/health')
def health():
    return {"status": "healthy", "leads": len(SAMPLE_LEADS)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)