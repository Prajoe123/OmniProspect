import os
from flask import Flask, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Scraper</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #0077b5; color: white; padding: 20px; border-radius: 8px; }
        .content { padding: 20px; background: #f8f9fa; border-radius: 8px; margin-top: 20px; }
        .success { color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 LinkedIn Scraper App</h1>
            <p>Successfully deployed on Render.com!</p>
        </div>
        <div class="content">
            <h2>✅ Deployment Successful</h2>
            <p>Your LinkedIn scraper application is now running in the cloud.</p>
            
            <h3>What's Working:</h3>
            <ul>
                <li>✓ Flask web server</li>
                <li>✓ Cloud hosting on Render.com</li>
                <li>✓ Ready for further development</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Add authentication features</li>
                <li>Set up database connection</li>
                <li>Implement scraping functionality</li>
                <li>Add user interface</li>
            </ol>
            
            <p class="success">🚀 Your app is live and accessible from anywhere!</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return {"status": "healthy", "message": "App is running successfully"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
