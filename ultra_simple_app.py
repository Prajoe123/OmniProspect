from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LinkedIn Scraper - Live!</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { color: #0077b5; text-align: center; margin-bottom: 30px; }
            .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
            .btn { background: #0077b5; color: white; padding: 12px 24px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px; }
            .btn:hover { background: #005582; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 LinkedIn Scraper</h1>
                <h2>Successfully Deployed on Render.com!</h2>
            </div>
            
            <div class="success">
                <strong>✅ Deployment Successful!</strong> Your LinkedIn scraper application is now live and accessible from anywhere in the world.
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🔍 Smart Scraping</h3>
                    <p>Find LinkedIn prospects based on your criteria</p>
                </div>
                <div class="feature">
                    <h3>📊 Lead Management</h3>
                    <p>Organize and track your prospects</p>
                </div>
                <div class="feature">
                    <h3>📱 CSV Export</h3>
                    <p>Export to Google Sheets easily</p>
                </div>
                <div class="feature">
                    <h3>☁️ Cloud Hosted</h3>
                    <p>Access from anywhere, anytime</p>
                </div>
            </div>
            
            <div style="text-align: center;">
                <a href="/demo" class="btn">View Demo</a>
                <a href="/health" class="btn">System Status</a>
            </div>
            
            <div style="margin-top: 40px; text-align: center; color: #666;">
                <p><strong>Next Steps:</strong></p>
                <p>• Add database functionality</p>
                <p>• Implement user authentication</p>
                <p>• Connect LinkedIn scraping engine</p>
                <p>• Deploy advanced features</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/demo')
def demo():
    return '''
    <h1>Demo Page</h1>
    <p>Sample lead data and features will be displayed here.</p>
    <a href="/">← Back to Home</a>
    '''

@app.route('/health')
def health():
    return {
        "status": "healthy", 
        "message": "LinkedIn Scraper is running successfully",
        "version": "1.0.0",
        "deployed": "Render.com"
    }

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)