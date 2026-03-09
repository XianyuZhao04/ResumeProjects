"""
Flask web app for checking badminton court availability.
Run locally with: python app.py
Deployed on Render.com via Dockerfile.
"""
from flask import Flask, render_template, jsonify
from scraper import CourtAvailabilityScraper
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import socket
import threading
import time

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
scraper = CourtAvailabilityScraper()

IS_CLOUD = bool(
    os.environ.get("RENDER") or
    os.environ.get("RAILWAY_ENVIRONMENT") or
    os.environ.get("FLY_APP_NAME")
)

def get_est_timestamp() -> str:
    try:
        return datetime.now(ZoneInfo("America/New_York")).isoformat()
    except Exception:
        import pytz
        return datetime.now(pytz.timezone("America/New_York")).isoformat()

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# ---------------------------------------------------------------------------
# Cache (cloud only — avoids re-scraping on every page refresh)
# ---------------------------------------------------------------------------

_cache: dict = {"results": None, "timestamp": 0, "building": False}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutes

def _build_cache():
    """Scrape both courts and store results in the cache."""
    with _cache_lock:
        _cache["building"] = True
    try:
        results = scraper.check_all_websites()
        with _cache_lock:
            _cache["results"] = results
            _cache["timestamp"] = time.time()
    except Exception as exc:
        with _cache_lock:
            _cache["results"] = [{
                "website": "Error",
                "status": "error",
                "message": str(exc),
                "timestamp": get_est_timestamp(),
            }]
            _cache["timestamp"] = time.time()
    finally:
        with _cache_lock:
            _cache["building"] = False

def _start_cache_refresh():
    """Kick off a background cache build if one isn't already running."""
    with _cache_lock:
        if _cache["building"]:
            return
    threading.Thread(target=_build_cache, daemon=True).start()

def _background_loop():
    """Periodically refresh the cache every 4 minutes on cloud."""
    time.sleep(5)  # Let the app fully start first
    while True:
        _build_cache()
        time.sleep(240)  # 4 minutes

# ---------------------------------------------------------------------------
# Auto-shutdown (local only — closes the server after 5 min of inactivity)
# ---------------------------------------------------------------------------

_last_activity = time.time()
SHUTDOWN_DELAY = 300  # 5 minutes

def _touch():
    global _last_activity
    _last_activity = time.time()

def _inactivity_watcher():
    while True:
        time.sleep(30)
        if time.time() - _last_activity > SHUTDOWN_DELAY:
            print("\n⏹️  No activity — shutting down.")
            os._exit(0)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    _touch()
    return render_template("mobile.html")

@app.route("/api/availability")
def get_availability():
    _touch()

    if IS_CLOUD:
        with _cache_lock:
            results  = _cache["results"]
            age      = time.time() - _cache["timestamp"]
            building = _cache["building"]

        if results is not None:
            # Return whatever we have; kick off a refresh if stale
            if age >= CACHE_TTL:
                _start_cache_refresh()
            return jsonify({
                "success": True,
                "data": results,
                "timestamp": get_est_timestamp(),
                "cached": True,
                "cache_age_seconds": int(age),
            })

        # No cache yet — tell the client to wait and try again
        if not building:
            _start_cache_refresh()
        return jsonify({
            "success": False,
            "error": "Data is loading, please refresh in a few seconds.",
            "building": True,
            "timestamp": get_est_timestamp(),
        }), 202

    # Local — scrape on demand (browser window will briefly appear)
    try:
        results = scraper.check_all_websites()
        return jsonify({"success": True, "data": results, "timestamp": get_est_timestamp()})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc), "timestamp": get_est_timestamp()}), 500

@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    if IS_CLOUD:
        return jsonify({"success": False, "message": "Disabled in cloud"}), 403
    threading.Thread(target=lambda: (time.sleep(2), os._exit(0)), daemon=True).start()
    return jsonify({"success": True, "message": "Shutting down..."})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    if IS_CLOUD:
        threading.Thread(target=_background_loop, daemon=True).start()
        print("🌐 Running on cloud — background cache started.")
    else:
        threading.Thread(target=_inactivity_watcher, daemon=True).start()
        ip = get_local_ip()
        print("\n" + "="*60)
        print("🏸 Badminton Court Availability")
        print("="*60)
        print(f"\n📱 iPhone: open Safari → http://{ip}:{port}")
        print(f"💻 Local:  http://localhost:{port}")
        print(f"\n⏹️  Auto-shutdown after {SHUTDOWN_DELAY // 60} min of inactivity")
        print()

    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)