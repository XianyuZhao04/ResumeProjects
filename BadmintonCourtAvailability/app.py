"""
Simple local web app for checking badminton court availability.
Run this and access from your iPhone on the same WiFi network.
"""
from flask import Flask, render_template, jsonify
from scraper import CourtAvailabilityScraper
from datetime import datetime
import os
import socket
import threading
import time
import sys
from functools import wraps

def get_est_timestamp():
    """Get current timestamp in EST timezone."""
    try:
        from zoneinfo import ZoneInfo
        est = ZoneInfo("America/New_York")
        return datetime.now(est).isoformat()
    except:
        # Fallback if zoneinfo not available (Python < 3.9)
        try:
            from datetime import timezone, timedelta
            try:
                import pytz
                est_tz = pytz.timezone('America/New_York')
                return datetime.now(est_tz).isoformat()
            except ImportError:
                # No pytz, use fixed offset (will be off during DST)
                est_offset = timedelta(hours=-5)  # EST is UTC-5
                est_tz = timezone(est_offset)
                return datetime.now(est_tz).isoformat()
        except:
            # Final fallback
            return datetime.now().isoformat()

app = Flask(__name__)
scraper = None
# Activity tracking only used for local development
last_activity = time.time()
shutdown_delay = 300  # 5 minutes of inactivity (only used locally)

def get_local_ip():
    """Get the local IP address for accessing from phone."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)  # Add timeout to prevent hanging
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def update_activity():
    """Update the last activity timestamp."""
    global last_activity
    last_activity = time.time()

def check_inactivity():
    """Check for inactivity and shut down if needed."""
    global last_activity
    while True:
        time.sleep(30)  # Check every 30 seconds
        if time.time() - last_activity > shutdown_delay:
            print("\n⏹️  No activity detected. Shutting down server...")
            os._exit(0)

@app.route('/')
def index():
    """Main mobile-friendly dashboard."""
    print("GET / request received", flush=True)  # Debug logging with flush
    try:
        update_activity()
        print("Rendering template...", flush=True)  # Debug logging
        result = render_template('mobile.html')
        print("Template rendered successfully", flush=True)  # Debug logging
        return result
    except Exception as e:
        import traceback
        print(f"Error rendering template: {e}", flush=True)  # Debug logging
        print(traceback.format_exc(), flush=True)
        return f"Error rendering template: {str(e)}", 500

@app.route('/test')
def test():
    """Simple test route to verify Flask is working."""
    print("GET /test request received", flush=True)
    return "Flask is working!"

@app.route('/simple')
def simple():
    """Ultra-simple route with no template."""
    print("GET /simple request received", flush=True)
    return """
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>If you see this, Flask is working!</h1>
        <p>Try <a href="/test">/test</a> or <a href="/">main page</a></p>
    </body>
    </html>
    """

def timeout_handler(timeout_seconds=30):
    """Decorator to handle timeouts for API endpoints."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            # Check if we're in cloud (timeout handling needed)
            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
            if not is_cloud:
                # Local: no timeout needed
                return func(*args, **kwargs)
            
            # Cloud: use threading timeout
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout_seconds)
            
            if thread.is_alive():
                # Timeout occurred
                return jsonify({
                    'success': False,
                    'error': f'Request timed out after {timeout_seconds} seconds',
                    'timestamp': get_est_timestamp()
                }), 504  # Gateway Timeout
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

@app.route('/api/availability')
@timeout_handler(timeout_seconds=25)  # 25s to stay well under Render's 30s limit
def get_availability():
    """API endpoint to get current availability."""
    global scraper
    update_activity()
    try:
        if scraper is None:
            scraper = CourtAvailabilityScraper()
        results = scraper.check_all_websites()
        return jsonify({
            'success': True,
            'data': results,
            'timestamp': get_est_timestamp()
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        # Log the full traceback for debugging
        print(f"Error in get_availability: {error_msg}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': get_est_timestamp()
        }), 500

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """Shutdown endpoint called when browser closes (only works locally, not in cloud)."""
    # Only allow shutdown if running locally (not in cloud)
    is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    if is_cloud:
        return jsonify({'success': False, 'message': 'Shutdown disabled in cloud hosting'}), 403
    
    def shutdown_server():
        time.sleep(2)  # Give time for response to be sent
        os._exit(0)
    threading.Thread(target=shutdown_server).start()
    return jsonify({'success': True, 'message': 'Shutting down...'})

if __name__ == '__main__':
    # Use PORT environment variable if available (for cloud hosting), otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    local_ip = get_local_ip()
    
    # Only start inactivity checker if running locally (not in cloud)
    is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    if not is_cloud:
        inactivity_thread = threading.Thread(target=check_inactivity, daemon=True)
        inactivity_thread.start()
    
    print("\n" + "="*60)
    print("🏸 Badminton Court Availability")
    print("="*60)
    
    if is_cloud:
        print(f"\n🌐 App is running on cloud hosting")
        print(f"💻 Access at: https://your-app-name.onrender.com (or your custom domain)")
    else:
        print(f"\n📱 To access from your iPhone:")
        print(f"   1. Make sure your phone is on the same WiFi network")
        print(f"   2. Open Safari and go to: http://{local_ip}:{port}")
        print(f"\n💻 Or access locally at: http://localhost:{port}")
        print(f"\n⏹️  Server will auto-shutdown after {shutdown_delay//60} minutes of inactivity")
        print("   (or when you close the browser tab)")
    
    print()
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
