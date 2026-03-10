"""
Court availability scraper.
Calls the EMS AnonymousServersApi directly — no browser needed.
"""
import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/New_York")
except Exception:
    import pytz as _pytz  # type: ignore
    _TZ = _pytz.timezone("America/New_York")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_URL = "https://pitt.emscloudservice.com/web/AnonymousServersApi.aspx/GetLocationDetailsAvailability"

HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://pitt.emscloudservice.com/web/",
}

# Room IDs discovered by intercepting browser network traffic.
ROOM_IDS = [456, 457]  # 610A, 610B

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_est_now() -> datetime:
    return datetime.now(_TZ)

def _get_est_timestamp() -> str:
    return _get_est_now().isoformat()

def _week_window() -> tuple[str, str]:
    """Return UTC ISO strings for today midnight → +7 days, matching EMS format."""
    now       = _get_est_now()
    midnight  = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = midnight - midnight.utcoffset()
    end_utc   = start_utc + timedelta(days=7)
    fmt       = "%Y-%m-%dT%H:%M:%S.000Z"
    return start_utc.strftime(fmt), end_utc.strftime(fmt)

def _format_time(dt: datetime) -> str:
    """Format a datetime as '1:00 PM', stripping leading zero."""
    return dt.strftime("%I:%M %p").lstrip("0")

# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------

class CourtAvailabilityScraper:

    def __init__(self, config_path: str = "config.json"):
        if os.path.exists(config_path):
            with open(config_path) as f:
                self.config = json.load(f)
        elif os.environ.get("COURT_CONFIG"):
            self.config = json.loads(os.environ["COURT_CONFIG"])
        elif os.path.exists("config.example.json"):
            with open("config.example.json") as f:
                self.config = json.load(f)
        else:
            raise FileNotFoundError("config.json not found.")

    def _scrape_court(self, website_index: int) -> Dict:
        site      = self.config["websites"][website_index]
        site_name = site.get("name", f"Website {website_index + 1}")
        url       = site.get("url", "")
        room_id   = ROOM_IDS[website_index]
        start, end = _week_window()

        try:
            resp = requests.post(
                API_URL,
                headers={**HEADERS, "Referer": url},
                json={"roomId": room_id, "start": start, "end": end},
                timeout=15,
            )
            resp.raise_for_status()

            # Response is double-encoded JSON:
            # {"d": "{\"Success\":true, \"JsonData\": \"{\\\"bookings\\\":[...]}\"}" }
            outer    = resp.json()
            middle   = json.loads(outer["d"])

            if not middle.get("Success"):
                return self._error(site_name, url, middle.get("ErrorMessage") or "API returned Success=false")

            bookings = json.loads(middle["JsonData"])["bookings"]

        except Exception as exc:
            return self._error(site_name, url, f"API request failed: {exc}")

        # Group bookings by day (Start field is local EST: "2026-03-09T13:00:00")
        now       = _get_est_now()
        today_str = now.strftime("%Y-%m-%d")

        # Build a dict of date_str → list of slot dicts, for all 7 days
        days: Dict[str, List] = {}
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(7):
            day_dt  = start_date + timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            days[day_str] = []

        for booking in bookings:
            day_str = booking["Start"][:10]  # "2026-03-09"
            if day_str not in days:
                continue

            start_dt = datetime.fromisoformat(booking["Start"])
            end_dt   = datetime.fromisoformat(booking["End"])
            title    = booking.get("Title", "Reserved")

            days[day_str].append({
                "name": f"{_format_time(start_dt)} to {_format_time(end_dt)} ({title})",
                "available": False,
                "_sort": (start_dt.hour, start_dt.minute),
            })

        # Sort each day's slots by time and build the final days array
        days_list = []
        for day_str, slots in days.items():
            slots.sort(key=lambda x: x.pop("_sort"))
            day_dt   = datetime.fromisoformat(day_str)
            is_today = day_str == today_str
            days_list.append({
                "date":     day_str,
                "label":    f"{day_dt.strftime('%A')} {day_dt.month}/{day_dt.day}",  # e.g. "Monday 3/9"
                "is_today": is_today,
                "slots":    slots,
            })

        return {
            "website":   site_name,
            "url":       url,
            "timestamp": _get_est_timestamp(),
            "days":      days_list,
            "status":    "success",
            "message":   f"Showing availability for the next 7 days",
        }

    def _error(self, site_name: str, url: str, message: str) -> Dict:
        return {
            "website":   site_name,
            "url":       url,
            "timestamp": _get_est_timestamp(),
            "days":      [],
            "status":    "error",
            "message":   message,
        }

    def scrape_website_1(self, url: str = "", **_) -> Dict:
        return self._scrape_court(0)

    def scrape_website_2(self, url: str = "", **_) -> Dict:
        return self._scrape_court(1)

    def check_all_websites(self, **_) -> List[Dict]:
        enabled = [
            (i, site)
            for i, site in enumerate(self.config["websites"])
            if site.get("enabled", True)
        ]
        return [self._scrape_court(i) for i, _ in enabled]