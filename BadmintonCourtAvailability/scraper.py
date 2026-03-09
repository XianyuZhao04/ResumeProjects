"""
Web scraper for checking badminton court availability.
Uses Playwright (async) for fast, event-driven scraping — no arbitrary sleeps.
"""
import json
import re
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/New_York")
except Exception:
    import pytz as _pytz  # type: ignore
    _TZ = _pytz.timezone("America/New_York")

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_est_now() -> datetime:
    return datetime.now(_TZ)

def _get_est_timestamp() -> str:
    return _get_est_now().isoformat()


# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------

class CourtAvailabilityScraper:
    """Scraper for checking court availability from the Pitt EMS system."""

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
            raise FileNotFoundError(
                "config.json not found. Please create it from config.example.json"
            )

    # ------------------------------------------------------------------
    # Async Playwright scraping
    # ------------------------------------------------------------------

    async def _scrape_async(self, website_index: int, url: str) -> Dict:
        """
        Scrape a single court URL using async Playwright.

        Using async + await means we never blindly sleep — instead we
        await specific page events, so we proceed exactly when the browser
        is ready and not a millisecond sooner or later.

        Steps:
          1. Launch headless Chromium.
          2. await page.goto()                         — waits until the page is loaded.
          3. await page.wait_for_selector("#availability-tab")
                                                       — waits until the JS tab renders.
          4. await tab.click()                         — clicks when element is ready.
          5. await page.wait_for_selector(".v-b-date") — waits until calendar appears.
          6. Grab HTML, close browser, parse with BeautifulSoup.
        """
        site_name = self.config["websites"][website_index].get(
            "name", f"Website {website_index + 1}"
        )

        try:
            async with async_playwright() as pw:
                # Use headless=False locally to avoid EMS bot detection.
                # The server blocks headless Chromium but allows a real visible browser.
                # On cloud (Render/Linux), headless=True is fine since the server IP
                # is different and doesn't get blocked the same way.
                is_cloud = bool(
                    os.environ.get("RENDER") or
                    os.environ.get("RAILWAY_ENVIRONMENT") or
                    os.environ.get("FLY_APP_NAME")
                )
                browser = await pw.chromium.launch(
                    headless=is_cloud,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
                )
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )

                # Step 1: Navigate
                # "networkidle" means: wait until there are no more than 0
                # open network connections for at least 500ms. This ensures
                # the page's initial JS has finished running.
                await page.goto(url, wait_until="networkidle", timeout=30_000)

                # Step 2: Dismiss the cookie banner if it appears
                # The "Accept" button sits on top of the page and blocks clicks
                # on anything underneath it. We try to click it if present;
                # if it's not there (already accepted), we just move on.
                try:
                    accept_btn = await page.wait_for_selector(
                        "button:has-text('Accept')", timeout=5_000
                    )
                    await accept_btn.click()
                    # Wait for the modal to fully disappear before proceeding
                    await page.wait_for_selector(
                        "button:has-text('Accept')", state="hidden", timeout=5_000
                    )
                except Exception:
                    pass  # No cookie banner — that's fine, keep going

                # Step 3: Screenshot for debugging - see what page looks like after cookie dismiss
                await page.screenshot(path="debug_after_cookie.png", full_page=True)

                # Step 4: Wait for the Availability tab and click it
                tab = await page.wait_for_selector("#availability-tab", timeout=15_000)
                await tab.click()

                # Step 4: Wait for the calendar grid to appear
                # Knockout.js renders the calendar asynchronously after the
                # tab click. We await this exact element so we grab HTML
                # exactly when it's ready — not a moment before.
                await page.wait_for_selector(".v-b-date", timeout=15_000)

                # Step 5: Grab the fully-rendered HTML
                html = await page.content()
                await browser.close()

            soup = BeautifulSoup(html, "html.parser")
            return self._parse_calendar_html(soup, website_index, url)

        except Exception as exc:
            return {
                "website": site_name,
                "url": url,
                "timestamp": _get_est_timestamp(),
                "courts": [],
                "status": "error",
                "message": f"Playwright error: {exc}",
            }

    # ------------------------------------------------------------------
    # Sync wrapper — runs the async scraper from sync Flask code
    # ------------------------------------------------------------------

    def _scrape_with_playwright(self, url: str, website_index: int) -> Dict:
        """
        Synchronous entry point. Runs the async scraper in its own event
        loop so Flask (which is sync) can call it normally.
        """
        return asyncio.run(self._scrape_async(website_index, url))

    # ------------------------------------------------------------------
    # HTML parsing
    # ------------------------------------------------------------------

    def _parse_calendar_html(self, soup: BeautifulSoup, website_index: int, url: str) -> Dict:
        """Parse the rendered calendar HTML and return today's reserved slots."""
        site_name = self.config["websites"][website_index].get(
            "name", f"Website {website_index + 1}"
        )
        now               = _get_est_now()
        today_day_name    = now.strftime("%A")   # e.g. "Monday"
        today_day_short   = now.strftime("%a")   # e.g. "Mon"
        today_month       = now.strftime("%B")   # e.g. "March"
        today_month_short = now.strftime("%b")   # e.g. "Mar"
        today_num         = now.day              # e.g. 9

        time_pattern = re.compile(r"([1-9]|1[0-2]):(\d{2})\s*(AM|PM)")

        def to_24h(h, m, ap):
            if ap == "PM" and h != 12:
                return h + 12, m
            if ap == "AM" and h == 12:
                return 0, m
            return h, m

        reserved_slots = []

        for event in soup.find_all("div", class_="v-b-event"):
            aria = event.get("aria-label", "")
            if " To " not in aria:
                continue

            before, after = aria.split(" To ", 1)
            before, after = before.strip(), after.strip()

            # Last time match in `before` is the actual start time
            # (event names can contain digits/years before it)
            start_matches = list(time_pattern.finditer(before))
            end_match = time_pattern.search(after)
            if not start_matches or not end_match:
                continue

            sm, em = start_matches[-1], end_match
            s_h, s_m, s_ap = int(sm.group(1)), int(sm.group(2)), sm.group(3)
            e_h, e_m, e_ap = int(em.group(1)), int(em.group(2)), em.group(3)

            if s_h > 12 or s_m > 59 or e_h > 12 or e_m > 59:
                continue

            s_h24, s_m24 = to_24h(s_h, s_m, s_ap)
            event_name = before[: sm.start()].strip() or "Reserved"

            # Is this event for today?
            col = event.find_parent("div", class_="v-b-cal-column")
            if not col:
                continue
            date_div = col.find("div", class_="v-b-date")
            if not date_div:
                continue

            span = date_div.find("span", {"aria-hidden": "true"})
            day_text = span.get_text(strip=True) if span else date_div.get("aria-label", "")

            cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", day_text)
            cleaned = cleaned.replace(",", " ").lower()

            has_day_num  = str(today_num) in cleaned
            has_day_name = today_day_name.lower() in cleaned or today_day_short.lower() in cleaned
            has_month    = today_month.lower() in cleaned or today_month_short.lower() in cleaned
            is_today     = has_day_num and (has_day_name or has_month)

            if not is_today:
                continue

            reserved_slots.append({
                "name": f"{s_h}:{s_m:02d} {s_ap} to {e_h}:{e_m:02d} {e_ap} ({event_name})",
                "available": False,
                "_sort": (s_h24, s_m24),
            })

        reserved_slots.sort(key=lambda x: x.pop("_sort"))

        date_divs  = soup.find_all("div", class_="v-b-date")
        all_events = soup.find_all("div", class_="v-b-event")

        if reserved_slots:
            msg = f"Found {len(reserved_slots)} reserved slot(s) for today"
        elif date_divs:
            msg = f"No reservations for today ({today_day_name}, {today_month} {today_num}). Court appears available!"
            if all_events:
                msg += f" ({len(all_events)} reservation(s) on other days.)"
        else:
            msg = "Calendar structure not found. The URL may have expired or the page layout changed."

        return {
            "website": site_name,
            "url": url,
            "timestamp": _get_est_timestamp(),
            "courts": reserved_slots,
            "status": "success" if date_divs else "error",
            "message": msg,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape_website_1(self, url: str, **_) -> Dict:
        return self._scrape_with_playwright(url, website_index=0)

    def scrape_website_2(self, url: str, **_) -> Dict:
        return self._scrape_with_playwright(url, website_index=1)

    def check_all_websites(self, **_) -> List[Dict]:
        """
        Scrape all enabled courts concurrently using asyncio.gather(),
        then return results in config order.

        asyncio.gather() is the async equivalent of running threads in parallel —
        it runs all scrape coroutines concurrently in one event loop.
        """
        enabled = [
            (i, site)
            for i, site in enumerate(self.config["websites"])
            if site.get("enabled", True)
        ]

        async def run_all():
            tasks = [self._scrape_async(i, site["url"]) for i, site in enabled]
            return await asyncio.gather(*tasks)

        # asyncio.run() creates a fresh event loop, runs everything,
        # then closes it — safe to call from sync Flask code.
        raw_results = asyncio.run(run_all())

        # Map results back to config order
        results: List[Optional[Dict]] = [None] * len(self.config["websites"])
        for (i, _), result in zip(enabled, raw_results):
            results[i] = result

        return [r for r in results if r is not None]