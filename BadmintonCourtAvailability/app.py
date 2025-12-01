"""
Simple local web app for checking badminton court availability.
Run this and access from your iPhone on the same WiFi network.
"""
from flask import Flask, render_template, jsonify, copy_current_request_context
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

# Cache for scraped results (for cloud deployment)
cached_results = None
cache_timestamp = None
cache_lock = threading.Lock()
cache_ttl = 300  # Cache for 5 minutes
cache_building = False  # Track if cache is being built

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
            # Check if we're in cloud (timeout handling needed)
            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
            if not is_cloud:
                # Local: no timeout needed, just call the function
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    import traceback
                    print(f"Error in {func.__name__}: {str(e)}", flush=True)
                    print(traceback.format_exc(), flush=True)
                    return jsonify({
                        'success': False,
                        'error': str(e),
                        'timestamp': get_est_timestamp()
                    }), 500
            
            # Cloud: use threading timeout with Flask app context
            result = [None]
            exception = [None]
            
            @copy_current_request_context
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
                    import traceback
                    print(f"Error in {func.__name__} (thread): {str(e)}", flush=True)
                    print(traceback.format_exc(), flush=True)
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout_seconds)
            
            if thread.is_alive():
                # Timeout occurred
                print(f"Request timed out after {timeout_seconds} seconds", flush=True)
                return jsonify({
                    'success': False,
                    'error': f'Request timed out after {timeout_seconds} seconds',
                    'timestamp': get_est_timestamp()
                }), 504  # Gateway Timeout
            
            if exception[0]:
                # Exception occurred in thread - return error response instead of raising
                return jsonify({
                    'success': False,
                    'error': str(exception[0]),
                    'timestamp': get_est_timestamp()
                }), 500
            
            if result[0] is None:
                # Function didn't return anything (shouldn't happen, but handle it)
                return jsonify({
                    'success': False,
                    'error': 'No response from server',
                    'timestamp': get_est_timestamp()
                }), 500
            
            return result[0]
        return wrapper
    return decorator

def refresh_cache_background():
    """Background function to refresh the cache periodically."""
    global scraper, cached_results, cache_timestamp, cache_lock, cache_building
    import os
    is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    
    if not is_cloud:
        return  # Only use caching in cloud
    
    print("Background cache thread started", flush=True)
    
    # Initial delay to let app start up
    time.sleep(3)
    
    while True:
        try:
            with cache_lock:
                cache_building = True
            
            print("Background: Starting cache build/refresh...", flush=True)
            
            if scraper is None:
                print("Background: Creating scraper instance...", flush=True)
                scraper = CourtAvailabilityScraper()
            
            print("Background: Calling check_all_websites() with NO timeout...", flush=True)
            results = scraper.check_all_websites(use_timeout=False)  # No timeout in background!
            print(f"Background: Got results: {len(results) if results else 0} websites", flush=True)
            
            with cache_lock:
                cached_results = results
                cache_timestamp = time.time()
                cache_building = False
            
            print(f"Background: Cache refreshed successfully at {get_est_timestamp()}", flush=True)
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Background: ERROR refreshing cache: {error_msg}", flush=True)
            print(traceback.format_exc(), flush=True)
            with cache_lock:
                cache_building = False
                # Store error in cache so API can return it
                cached_results = [{
                    'website': 'Error',
                    'status': 'error',
                    'message': f'Cache build failed: {error_msg}',
                    'timestamp': get_est_timestamp()
                }]
                cache_timestamp = time.time()
        
        # Wait before next refresh (refresh every 4 minutes, cache is valid for 5 minutes)
        print("Background: Waiting 4 minutes before next refresh...", flush=True)
        time.sleep(240)  # 4 minutes

@app.route('/api/availability')
def get_availability():
    """API endpoint to get current availability."""
    global scraper, cached_results, cache_timestamp, cache_lock, cache_building
    import os
    is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    
    update_activity()
    
    # In cloud: return cached results immediately, NEVER block on scraping
    if is_cloud:
        # Check cache status inside lock to prevent race conditions
        should_trigger_refresh = False
        should_start_build = False
        cache_age = float('inf')
        stale_data = None
        
        with cache_lock:
            cache_age = time.time() - cache_timestamp if cache_timestamp else float('inf')
            
            # If cache exists and is fresh, return it immediately
            if cached_results is not None and cache_age < cache_ttl:
                return jsonify({
                    'success': True,
                    'data': cached_results,
                    'timestamp': get_est_timestamp(),
                    'cached': True,
                    'cache_age_seconds': int(cache_age)
                })
            
            # If cache is stale but exists, return it anyway and trigger background refresh
            if cached_results is not None:
                stale_data = cached_results  # Store data to return
                # Trigger background refresh if not already building
                if not cache_building:
                    cache_building = True
                    should_trigger_refresh = True
                    print("API: Cache stale, triggering background refresh...", flush=True)
                return jsonify({
                    'success': True,
                    'data': stale_data,
                    'timestamp': get_est_timestamp(),
                    'cached': True,
                    'cache_age_seconds': int(cache_age),
                    'refreshing': should_trigger_refresh
                })
            
            # No cache at all - trigger immediate build if not already building
            if not cache_building:
                cache_building = True
                should_start_build = True
                print("API: No cache found, triggering immediate background build...", flush=True)
        
        # Start refresh thread outside the lock (if needed)
        if should_trigger_refresh:
            def refresh_cache_now():
                global scraper, cached_results, cache_timestamp, cache_building
                try:
                    print("Stale cache refresh: Starting...", flush=True)
                    if scraper is None:
                        scraper = CourtAvailabilityScraper()
                    results = scraper.check_all_websites(use_timeout=False)
                    with cache_lock:
                        cached_results = results
                        cache_timestamp = time.time()
                        cache_building = False
                    print("Stale cache refresh: Success!", flush=True)
                except Exception as e:
                    import traceback
                    print(f"Stale cache refresh: ERROR - {str(e)}", flush=True)
                    print(traceback.format_exc(), flush=True)
                    with cache_lock:
                        cache_building = False
            
            threading.Thread(target=refresh_cache_now, daemon=True).start()
        
        # Start build thread outside the lock (if needed)
        if should_start_build:
            def build_cache_now():
                global scraper, cached_results, cache_timestamp, cache_building
                try:
                    print("Immediate build: Starting...", flush=True)
                    if scraper is None:
                        scraper = CourtAvailabilityScraper()
                    results = scraper.check_all_websites(use_timeout=False)  # No timeout in background!
                    with cache_lock:
                        cached_results = results
                        cache_timestamp = time.time()
                        cache_building = False
                    print("Immediate build: Success!", flush=True)
                except Exception as e:
                    import traceback
                    print(f"Immediate build: ERROR - {str(e)}", flush=True)
                    print(traceback.format_exc(), flush=True)
                    with cache_lock:
                        cache_building = False
                        cached_results = [{
                            'website': 'Error',
                            'status': 'error',
                            'message': f'Build failed: {str(e)}',
                            'timestamp': get_est_timestamp()
                        }]
                        cache_timestamp = time.time()
            
            threading.Thread(target=build_cache_now, daemon=True).start()
        
        # Return message that cache is building
        return jsonify({
            'success': False,
            'error': 'Cache is being built. This may take 20-30 seconds. Please wait and refresh.',
            'timestamp': get_est_timestamp(),
            'building': True
        }), 202  # Accepted - request is being processed
    
    # Local: no caching, scrape on demand
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
    else:
        # In cloud: start background cache refresh thread immediately
        print("="*60, flush=True)
        print("Starting background cache refresh thread...", flush=True)
        cache_refresh_thread = threading.Thread(target=refresh_cache_background, daemon=True)
        cache_refresh_thread.start()
        print("Background cache refresh thread started (will begin building cache in 3 seconds)", flush=True)
        print("="*60, flush=True)
    
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
