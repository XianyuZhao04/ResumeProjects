"""
Web scraper for checking badminton court availability.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import json
from datetime import datetime
import os
import re
import threading
import time
from zoneinfo import ZoneInfo

# Lock for ChromeDriver installation to prevent concurrent downloads
_chromedriver_lock = threading.Lock()

# Try to import Selenium (optional - only needed if JS rendering is required)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class CourtAvailabilityScraper:
    """Scraper for checking court availability from multiple sources."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize scraper with configuration."""
        # Try to load from file first, then try environment variable, then fallback to example
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        elif os.environ.get('COURT_CONFIG'):
            # Load from environment variable (useful for cloud hosting)
            self.config = json.loads(os.environ.get('COURT_CONFIG'))
        elif os.path.exists('config.example.json'):
            # Fallback to example (for first-time setup)
            with open('config.example.json', 'r') as f:
                self.config = json.load(f)
        else:
            raise FileNotFoundError("config.json not found. Please create it from config.example.json")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def _get_est_timestamp(self):
        """Get current timestamp in EST timezone."""
        try:
            est = ZoneInfo("America/New_York")
            return datetime.now(est).isoformat()
        except:
            # Fallback if zoneinfo not available (Python < 3.9)
            try:
                from datetime import timezone, timedelta
                # Account for DST - EST is UTC-5, EDT is UTC-4
                # Simple approach: check if we're in DST (roughly March-November)
                now_utc = datetime.utcnow()
                # EST/EDT is roughly March 2nd Sunday to November 1st Sunday
                # For simplicity, use UTC-5 for now, or better: use pytz if available
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
    
    def _safe_quit_driver(self, driver):
        """Safely quit a driver, handling invalid session errors."""
        if not driver:
            return
        try:
            # Check if session is still valid before quitting
            try:
                driver.current_url  # This will raise if session is invalid
                driver.quit()
            except:
                # Session already invalid, try to quit anyway (might work)
                try:
                    driver.quit()
                except:
                    pass  # Session already closed, ignore
        except:
            pass  # Driver already closed or invalid
    
    def _scrape_with_selenium(self, url: str, website_index: int, retry_count: int = 0) -> Dict:
        """Scrape using Selenium to render JavaScript with improved stability."""
        # Use fewer retries in cloud to avoid timeouts
        import os
        is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
        max_retries = 0 if is_cloud else 3  # No retries in cloud to save time
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional options for cloud/Linux environments - improved stability
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        # Remove --single-process as it can cause issues, use --remote-debugging-port=0 for random port
        options.add_argument('--remote-debugging-port=0')
        
        # Set page load strategy to eager (don't wait for all resources)
        options.page_load_strategy = 'eager'
        
        driver = None
        try:
            # Exponential backoff for retries
            if retry_count > 0:
                wait_time = min(2 ** retry_count, 5)  # Max 5 seconds
                time.sleep(wait_time)
            
            # Try to use webdriver-manager if available, otherwise use system ChromeDriver
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                import os
                import shutil
                
                # Use lock to prevent concurrent ChromeDriver downloads (which can cause corruption)
                with _chromedriver_lock:
                    # Try to install ChromeDriver with error handling
                    try:
                        service = Service(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=options)
                        # Set timeouts to prevent hanging
                        # Shorter timeout in cloud
                        import os
                        is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                        timeout = 15 if is_cloud else 30
                        driver.set_page_load_timeout(timeout)
                        driver.implicitly_wait(5)
                    except Exception as wdm_error:
                        # If webdriver-manager fails (e.g., corrupted cache), try clearing cache and retrying
                        if "zip" in str(wdm_error).lower() or "not a zip" in str(wdm_error).lower():
                            # Clear webdriver-manager cache
                            try:
                                cache_path = os.path.join(os.path.expanduser("~"), ".wdm")
                                if os.path.exists(cache_path):
                                    shutil.rmtree(cache_path, ignore_errors=True)
                                # Retry installation
                                service = Service(ChromeDriverManager().install())
                                driver = webdriver.Chrome(service=service, options=options)
                                # Shorter timeout in cloud
                                import os
                                is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                                timeout = 15 if is_cloud else 30
                                driver.set_page_load_timeout(timeout)
                                driver.implicitly_wait(5)
                            except Exception as retry_error:
                                # If retry fails, fall back to system ChromeDriver
                                driver = webdriver.Chrome(options=options)
                                # Shorter timeout in cloud
                                import os
                                is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                                timeout = 15 if is_cloud else 30
                                driver.set_page_load_timeout(timeout)
                                driver.implicitly_wait(5)
                        else:
                            # For other errors, fall back to system ChromeDriver
                            driver = webdriver.Chrome(options=options)
                            # Shorter timeout in cloud
                            import os
                            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                            timeout = 15 if is_cloud else 30
                            driver.set_page_load_timeout(timeout)
                            driver.implicitly_wait(5)
            except ImportError:
                # Fall back to system ChromeDriver if webdriver-manager not available
                driver = webdriver.Chrome(options=options)
                import os
                is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                timeout = 15 if is_cloud else 30
                driver.set_page_load_timeout(timeout)
                driver.implicitly_wait(5)
            
            # Validate driver before proceeding
            try:
                _ = driver.current_url
            except:
                raise Exception("Driver session invalid immediately after creation")
            
            driver.get(url)
            
            # Wait for page to load with better error handling
            try:
                # Check if session is still valid
                _ = driver.current_url
                # Use shorter timeout since we're using eager page load strategy
                import os
                is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                page_load_timeout = 3 if is_cloud else 5
                WebDriverWait(driver, page_load_timeout).until(
                    lambda d: d.execute_script('return document.readyState') in ['complete', 'interactive']
                )
            except Exception as session_error:
                error_str = str(session_error).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    # Session invalid - retry if we haven't exceeded max retries
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise Exception(f"Session failed after {max_retries + 1} attempts: {str(session_error)}")
                # For other errors, continue with a short wait
                time.sleep(0.3)
            
            # Find and click the "availability" tab
            tab_clicked = False
            try:
                # Wait a bit for tabs to render (reduced wait time)
                time.sleep(0.3)
                
                # Look for the availability tab - try multiple strategies
                availability_tab = None
                
                # Strategy 1: Try specific selectors (corrected based on actual HTML)
                selectors = [
                    (By.ID, "availability-tab"),  # FIXED: Actual ID is "availability-tab", not "room-availability-tab"
                    (By.CSS_SELECTOR, "a[href='#room-availability']"),
                    (By.CSS_SELECTOR, "#availability-tab"),  # Also try as CSS selector
                    (By.CSS_SELECTOR, "a[data-toggle='tab'][href*='availability']"),
                    (By.CSS_SELECTOR, "a[href*='availability']"),
                    (By.XPATH, "//a[@id='availability-tab']"),  # Explicit XPath for the ID
                    (By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'availability')]"),
                    (By.XPATH, "//li/a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'availability')]"),
                    (By.XPATH, "//*[@role='tab' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'availability')]"),
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        # Check if session is still valid
                        _ = driver.current_url
                        availability_tab = driver.find_element(selector_type, selector_value)
                        if availability_tab and availability_tab.is_displayed():
                            # Scroll into view and click
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", availability_tab)
                            import os
                            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                            scroll_wait = 0.1 if is_cloud else 0.2
                            time.sleep(scroll_wait)
                            # Try JavaScript click first (more reliable)
                            try:
                                driver.execute_script("arguments[0].click();", availability_tab)
                            except:
                                availability_tab.click()
                            # Wait for tab content to load (shorter in cloud)
                            import os
                            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                            wait_time = 0.3 if is_cloud else 1.0  # Very short in cloud
                            time.sleep(wait_time)
                            
                            # Verify the tab was actually clicked by checking if calendar is visible
                            # Skip verification in cloud to save time
                            if not is_cloud:
                                try:
                                    # Check if the room-availability tab panel is now active
                                    tab_panel = driver.find_element(By.ID, "room-availability")
                                    is_active = "active" in tab_panel.get_attribute("class") or tab_panel.is_displayed()
                                    if is_active:
                                        tab_clicked = True
                                    else:
                                        # Wait a bit more and check again
                                        time.sleep(1.0)
                                        is_active = "active" in tab_panel.get_attribute("class") or tab_panel.is_displayed()
                                        if is_active:
                                            tab_clicked = True
                                except:
                                    # Assume it worked and continue
                                    tab_clicked = True
                            else:
                                # In cloud, assume it worked
                                tab_clicked = True
                            
                            if tab_clicked:
                                break
                    except Exception as e:
                        error_str = str(e).lower()
                        if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                            if retry_count < max_retries:
                                self._safe_quit_driver(driver)
                                return self._scrape_with_selenium(url, website_index, retry_count + 1)
                            else:
                                raise
                        continue
                
                # Strategy 2: Find all clickable elements and look for "availability"
                if not tab_clicked:
                    try:
                        # Find all links and buttons
                        all_clickables = driver.find_elements(By.TAG_NAME, "a")
                        all_clickables.extend(driver.find_elements(By.TAG_NAME, "button"))
                        all_clickables.extend(driver.find_elements(By.CSS_SELECTOR, "[role='tab']"))
                        all_clickables.extend(driver.find_elements(By.CSS_SELECTOR, "[role='button']"))
                        
                        for element in all_clickables:
                            try:
                                text = element.text.lower()
                                href = element.get_attribute('href') or ''
                                aria_label = element.get_attribute('aria-label') or ''
                                
                                if 'availability' in text or 'availability' in href.lower() or 'availability' in aria_label.lower():
                                    if element.is_displayed():
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                        time.sleep(0.3)
                                        try:
                                            driver.execute_script("arguments[0].click();", element)
                                        except:
                                            element.click()
                                        # Shorter wait in cloud
                                        import os
                                        is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                                        wait_after_tab = 0.3 if is_cloud else 1.0  # Very short in cloud
                                        time.sleep(wait_after_tab)
                                        tab_clicked = True
                                        break
                            except:
                                continue
                    except:
                        pass
                        
            except Exception as e:
                # If we can't find the tab, continue anyway (maybe it's already active)
                pass
            
            # Wait for calendar to load - wait for v-b-date first
            # But also check if tab was clicked - if not, calendar won't load
            calendar_found = False
            if not tab_clicked:
                # Try one more time to click the tab
                try:
                    tab = driver.find_element(By.ID, "availability-tab")
                    if tab:
                        driver.execute_script("arguments[0].click();", tab)
                        time.sleep(1.0)
                        tab_clicked = True
                except:
                    pass
            
            try:
                # Check if session is still valid
                _ = driver.current_url
                # Use shorter timeout in cloud
                import os
                is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
                wait_timeout = 3 if is_cloud else 10  # Very short in cloud
                WebDriverWait(driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "v-b-date"))
                )
                calendar_found = True
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                # Calendar might not be visible yet - try waiting a bit more (reduced wait)
                time.sleep(1.0)
                try:
                    _ = driver.current_url  # Check session
                    driver.find_element(By.CLASS_NAME, "v-b-date")
                    calendar_found = True
                except Exception as e2:
                    error_str = str(e2).lower()
                    if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                        if retry_count < max_retries:
                            self._safe_quit_driver(driver)
                            return self._scrape_with_selenium(url, website_index, retry_count + 1)
                        else:
                            raise
                    pass
            
            # If calendar not found and tab wasn't clicked, maybe the tab is already active
            # Or maybe we need to try clicking any tab to trigger the calendar
            if not calendar_found and not tab_clicked:
                # Try clicking tabs to find the one that shows the calendar
                try:
                    # Get all possible tab elements
                    tabs = driver.find_elements(By.CSS_SELECTOR, ".nav-tabs a, .nav-pills a, [role='tab'], li a[data-toggle='tab']")
                    if not tabs:
                        # Try broader search
                        tabs = driver.find_elements(By.CSS_SELECTOR, "ul.nav li a, .tab-content + ul a")
                    
                    if tabs:
                        # Try clicking each tab until we find the calendar
                        for i, tab in enumerate(tabs[:5]):  # Try first 5 tabs
                            try:
                                tab_text = (tab.text or '').strip()
                                # Skip if it's clearly not availability (like "Details", "Map", etc.)
                                if tab_text and tab_text.lower() in ['details', 'map', 'photos', 'reviews']:
                                    continue
                                
                                if tab.is_displayed():
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                                    time.sleep(0.3)
                                    driver.execute_script("arguments[0].click();", tab)
                                    time.sleep(1.5)  # Reduced from 3s to 1.5s
                                    # Check if calendar appeared
                                    try:
                                        driver.find_element(By.CLASS_NAME, "v-b-date")
                                        calendar_found = True
                                        tab_clicked = True
                                        break
                                    except:
                                        pass
                            except:
                                continue
                except:
                    pass
            
            # If calendar not found and tab wasn't clicked, try clicking tab again
            if not calendar_found and not tab_clicked:
                # Try one more time to find and click the tab - be more aggressive
                time.sleep(1)  # Reduced from 2s to 1s
                try:
                    # Try all possible tab elements - also check for tabs/pills
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    all_links.extend(driver.find_elements(By.TAG_NAME, "button"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, "[role='tab']"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, "[role='button']"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, "li a"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, ".nav-link"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, ".tab"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, ".nav-tabs a"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, ".nav-pills a"))
                    all_links.extend(driver.find_elements(By.CSS_SELECTOR, "[data-toggle='tab']"))
                    
                    # Remove duplicates
                    seen = set()
                    unique_links = []
                    for link in all_links:
                        try:
                            link_id = id(link)
                            if link_id not in seen:
                                seen.add(link_id)
                                unique_links.append(link)
                        except:
                            pass
                    
                    for link in unique_links:
                        try:
                            text = (link.text or '').lower()
                            href = (link.get_attribute('href') or '').lower()
                            aria_label = (link.get_attribute('aria-label') or '').lower()
                            class_name = (link.get_attribute('class') or '').lower()
                            data_target = (link.get_attribute('data-target') or '').lower()
                            
                            if ('availability' in text or 'availability' in href or 
                                'availability' in aria_label or 'availability' in class_name or
                                'availability' in data_target):
                                try:
                                    _ = driver.current_url  # Validate session
                                    if link.is_displayed():
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                                        time.sleep(0.3)
                                        try:
                                            driver.execute_script("arguments[0].click();", link)
                                        except:
                                            link.click()
                                        time.sleep(1.5)  # Reduced from 3s to 1.5s
                                        tab_clicked = True
                                        # Check again for calendar
                                        try:
                                            _ = driver.current_url  # Validate session
                                            driver.find_element(By.CLASS_NAME, "v-b-date")
                                            calendar_found = True
                                        except Exception as e2:
                                            if "invalid session" in str(e2).lower() or "session id" in str(e2).lower():
                                                if retry_count < max_retries:
                                                    self._safe_quit_driver(driver)
                                                    return self._scrape_with_selenium(url, website_index, retry_count + 1)
                                                else:
                                                    raise
                                            pass
                                        break
                                except Exception as e:
                                    if "invalid session" in str(e).lower() or "session id" in str(e).lower():
                                        if retry_count < max_retries:
                                            self._safe_quit_driver(driver)
                                            return self._scrape_with_selenium(url, website_index, retry_count + 1)
                                        else:
                                            raise
                        except Exception as e:
                            if "invalid session" in str(e).lower() or "session id" in str(e).lower():
                                if retry_count < max_retries:
                                    self._safe_quit_driver(driver)
                                    return self._scrape_with_selenium(url, website_index, retry_count + 1)
                                else:
                                    raise
                            continue
                except:
                    pass
            
            # Wait for JavaScript to fully render - events may load via AJAX
            # Wait for page to be ready (reduced timeout)
            try:
                _ = driver.current_url  # Validate session
                WebDriverWait(driver, 3).until(  # Reduced timeout
                    lambda d: d.execute_script('return document.readyState') in ['complete', 'interactive']
                )
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                pass
            
            # Wait for any AJAX/jQuery calls to complete (reduced timeout)
            try:
                _ = driver.current_url  # Validate session
                WebDriverWait(driver, 2).until(  # Reduced timeout
                    lambda d: d.execute_script('return typeof jQuery !== "undefined" && jQuery.active == 0') or True
                )
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                pass
            
            # Give time for events to load via AJAX (shorter in cloud)
            import os
            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
            ajax_wait = 0.3 if is_cloud else 1.5  # Very short in cloud
            time.sleep(ajax_wait)
            
            # Scroll to calendar area and try to navigate to today's date
            try:
                _ = driver.current_url  # Validate session
                calendar_element = driver.find_element(By.ID, "room-availability-control")
                driver.execute_script("arguments[0].scrollIntoView(true);", calendar_element)
                scroll_wait = 0.2 if is_cloud else 0.8  # Very short in cloud
                time.sleep(scroll_wait)
                
                # In cloud: skip scrolling to today to save time - just parse whatever is visible
                # In local: try to scroll to today for better accuracy
                if not is_cloud:
                    # Try to scroll calendar horizontally to find today's date
                    # The calendar might start showing future dates, so we need to scroll left
                    try:
                        # Get today's date info
                        from zoneinfo import ZoneInfo
                        try:
                            est = ZoneInfo("America/New_York")
                            today = datetime.now(est)
                        except:
                            import pytz
                            est_tz = pytz.timezone('America/New_York')
                            today = datetime.now(est_tz)
                        
                        today_day_num = today.day
                        today_day_name_short = today.strftime('%a')  # e.g., "Thu"
                        
                        # Try to find today's date column and scroll to it
                        date_elements = driver.find_elements(By.CLASS_NAME, "v-b-date")
                        found_today = False
                        for date_elem in date_elements[:10]:  # Check first 10 dates
                            try:
                                date_span = date_elem.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']")
                                date_text = date_span.text if date_span else ""
                                if str(today_day_num) in date_text and today_day_name_short in date_text:
                                    # Found today! Scroll it into view
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'center'});", date_elem)
                                    time.sleep(1.5)  # Wait for events to load after scrolling
                                    found_today = True
                                    break
                            except:
                                continue
                        
                        # If today not found in visible dates, try scrolling the calendar container
                        if not found_today:
                            # Scroll the calendar container left to find today
                            driver.execute_script("""
                                var container = arguments[0];
                                container.scrollLeft = 0;
                            """, calendar_element)
                            time.sleep(1.5)  # Wait for events to load after scrolling
                    except:
                        pass  # If scrolling fails, continue anyway
                else:
                    # In cloud: minimal wait after scrolling to calendar
                    time.sleep(0.2)
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                pass
            
            # Try to wait for events specifically (but don't fail if none found)
            # Events may load asynchronously via AJAX, so wait a bit
            import os
            is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
            
            # Wait for events to load (minimal in cloud to save time)
            if not is_cloud:
                # Local: proper event detection
                events_found = False
                for attempt in range(3):
                    try:
                        _ = driver.current_url  # Validate session
                        events_elements = driver.find_elements(By.CLASS_NAME, "v-b-event")
                        if events_elements and len(events_elements) > 0:
                            events_found = True
                            break
                        if attempt < 2:  # Don't wait on last attempt
                            time.sleep(1.5)
                    except Exception as e:
                        error_str = str(e).lower()
                        if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                            if retry_count < max_retries:
                                self._safe_quit_driver(driver)
                                return self._scrape_with_selenium(url, website_index, retry_count + 1)
                            else:
                                raise
                        if attempt < 2:
                            time.sleep(1.5)
                
                # One more short wait to ensure everything is rendered
                time.sleep(0.5)
            else:
                # Cloud: minimal wait, just check once and move on
                try:
                    _ = driver.current_url  # Validate session
                except Exception as e:
                    error_str = str(e).lower()
                    if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                        if retry_count < max_retries:
                            self._safe_quit_driver(driver)
                            return self._scrape_with_selenium(url, website_index, retry_count + 1)
                        else:
                            raise
                # Minimal wait in cloud - events may not be fully loaded, but we'll parse what we can
                time.sleep(0.2)
            
            # Get the rendered HTML - check session first
            try:
                _ = driver.current_url  # Validate session
                html = driver.page_source
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                raise
            soup = BeautifulSoup(html, 'html.parser')
            
            # Debug: Save page source for 610B if calendar not found (to see what's different)
            if website_index == 1 and not calendar_found:
                debug_page_file = f'debug_page_source_610B.html'
                with open(debug_page_file, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            # Debug: Check how many events we found - validate session first
            try:
                _ = driver.current_url  # Validate session
                events_before_parse = driver.find_elements(By.CLASS_NAME, "v-b-event")
                date_divs_selenium = driver.find_elements(By.CLASS_NAME, "v-b-date")
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]):
                    if retry_count < max_retries:
                        self._safe_quit_driver(driver)
                        return self._scrape_with_selenium(url, website_index, retry_count + 1)
                    else:
                        raise
                events_before_parse = []
                date_divs_selenium = []
            
            # Now parse using the same logic
            result = self._parse_calendar_html(soup, website_index, url)
            
            # Add debug info about tab click and calendar detection
            debug_parts = []
            if tab_clicked:
                debug_parts.append("Tab clicked successfully")
            else:
                debug_parts.append("Tab click may have failed")
            
            if calendar_found:
                debug_parts.append(f"Calendar found ({len(date_divs_selenium)} date divs)")
            else:
                debug_parts.append("Calendar not found")
            
            if len(events_before_parse) > 0:
                debug_parts.append(f"Selenium found {len(events_before_parse)} events")
            
            # Check what tabs are available on the page
            try:
                all_tabs = driver.find_elements(By.CSS_SELECTOR, "a, button, [role='tab']")
                tab_texts = []
                for tab in all_tabs[:10]:  # First 10 tabs
                    try:
                        text = tab.text.strip()
                        if text:
                            tab_texts.append(text[:30])  # First 30 chars
                    except:
                        pass
                if tab_texts:
                    debug_parts.append(f"Found tabs: {', '.join(tab_texts[:5])}")
            except:
                pass
            
            # If no events found but Selenium found some, add debug info
            if len(events_before_parse) > 0 and len(result.get('courts', [])) == 0:
                result['message'] = f'Selenium found {len(events_before_parse)} events but parser found 0. This is a parsing issue. Debug: {", ".join(debug_parts)}'
            elif len(result.get('courts', [])) == 0 and not calendar_found:
                # No calendar found - add debug info
                result['message'] = f"{result.get('message', '')} Debug: {', '.join(debug_parts)}"
            
            return result
            
        except Exception as e:
            # Check if it's an invalid session error and we can retry
            error_str = str(e).lower()
            if any(phrase in error_str for phrase in ["invalid session", "session id", "disconnected", "unable to connect"]) and retry_count < max_retries:
                self._safe_quit_driver(driver)
                return self._scrape_with_selenium(url, website_index, retry_count + 1)
            
            # If Selenium fails, return error
            return {
                'website': self.config['websites'][website_index].get('name', f'Website {website_index + 1}'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': [],
                'status': 'error',
                'message': f'Selenium error: {str(e)}. Make sure ChromeDriver is installed.'
            }
        finally:
            self._safe_quit_driver(driver)
    
    def _parse_calendar_html(self, soup: BeautifulSoup, website_index: int, url: str) -> Dict:
        """Parse calendar HTML to find RESERVED/OCCUPIED times (not available)."""
        reserved_slots = []
        
        # Get today's date info for filtering - use EST timezone
        try:
            est = ZoneInfo("America/New_York")
            today = datetime.now(est)
        except:
            try:
                import pytz
                est_tz = pytz.timezone('America/New_York')
                today = datetime.now(est_tz)
            except:
                # Fallback to UTC if timezone libraries not available
                today = datetime.now()
        
        today_day_name = today.strftime('%A')  # e.g., "Friday"
        today_day_name_short = today.strftime('%a')  # e.g., "Fri"
        today_day_num = today.day  # e.g., 7
        today_month_name = today.strftime('%B')  # e.g., "November"
        today_month_name_short = today.strftime('%b')  # e.g., "Nov"
        
        # Debug: Track what dates we find
        found_dates = []
        events_checked = 0
        
        # Look for ALL v-b-event divs directly (these are the reserved times)
        # Don't need to find by date first - just get all events
        # Try multiple ways to find events (class might be a list or string)
        events = soup.find_all('div', class_='v-b-event')
        if not events:
            # Try with lambda in case class is a list
            events = soup.find_all('div', class_=lambda x: x and ('v-b-event' in str(x) if x else False))
        
        # Debug: Also check for any divs with v-b in the class
        all_vb_divs = soup.find_all('div', class_=lambda x: x and 'v-b' in str(x))
        
        # Debug: Log how many events we found
        events_found_count = len(events) if events else 0
        
        if events:
            for event in events:
                event_aria = event.get('aria-label', '')
                # Debug: log all events found
                if not event_aria:
                    continue
                if ' To ' in event_aria or event_aria.endswith(' To'):
                    # Parse: "Event Name10:30 AM To 11:45 AM"
                    # Split by " To " (with spaces) to avoid splitting "Tournament" or other words
                    if ' To ' in event_aria:
                        parts = event_aria.split(' To ', 1)  # Split only on first occurrence
                    else:
                        # Handle case where it ends with " To" (no space after)
                        parts = event_aria.rsplit(' To', 1)
                    if len(parts) == 2:
                        start_part = parts[0].strip()
                        end_part = parts[1].strip()
                        
                        # Find event name (text before the time)
                        # Pattern: hour must be 1-12, can have space or no space before (handles "event10:30" or "event 10:30")
                        time_pattern = r'([1-9]|1[0-2]):(\d{2})\s*(AM|PM)'
                        
                        # Extract event name - find the LAST time match (in case event name has numbers)
                        event_name_match = None
                        for match in re.finditer(time_pattern, start_part):
                            event_name_match = match
                        # Use the last match as the actual time
                        if event_name_match:
                            # Get text before the time (could be "event10:30" or "event 10:30" or "Fall 20256:00")
                            event_name = start_part[:event_name_match.start()].strip()
                            # If the last character before time is a digit, we need to separate it
                            # e.g., "Fall 20256:00" -> we want "Fall 2025" and "6:00"
                            # The regex already matched the time correctly, so we just need to clean the event name
                            # Try to find where the event name should end (before digits that are part of time)
                            # For now, just keep it as is - the time extraction will handle it
                        else:
                            event_name = "Reserved"
                        
                        # Extract start and end times - use the last match for start_part
                        start_match = None
                        for match in re.finditer(time_pattern, start_part):
                            start_match = match
                        end_match = re.search(time_pattern, end_part)
                        
                        if start_match and end_match:
                            start_hour = int(start_match.group(1))
                            start_min = int(start_match.group(2))
                            start_am_pm = start_match.group(3)
                            
                            end_hour = int(end_match.group(1))
                            end_min = int(end_match.group(2))
                            end_am_pm = end_match.group(3)
                            
                            # Validate times are reasonable (hour 1-12, minute 0-59)
                            if start_hour > 12 or start_min > 59 or end_hour > 12 or end_min > 59:
                                continue  # Skip this event if times are invalid
                            
                            # Convert to 24-hour format for sorting
                            if start_am_pm == 'PM' and start_hour != 12:
                                start_hour_24 = start_hour + 12
                            elif start_am_pm == 'AM' and start_hour == 12:
                                start_hour_24 = 0
                            else:
                                start_hour_24 = start_hour
                            
                            if end_am_pm == 'PM' and end_hour != 12:
                                end_hour_24 = end_hour + 12
                            elif end_am_pm == 'AM' and end_hour == 12:
                                end_hour_24 = 0
                            else:
                                end_hour_24 = end_hour
                            
                            # Format time strings (keep original AM/PM format)
                            start_time_str = f"{start_hour}:{start_min:02d} {start_am_pm}"
                            end_time_str = f"{end_hour}:{end_min:02d} {end_am_pm}"
                            
                            # Try to find the date for this event
                            # Look for the nearest v-b-date parent
                            date_div = event.find_parent('div', class_='v-b-cal-column')
                            is_today = False
                            day_name = 'Unknown Day'
                            
                            if date_div:
                                date_elem = date_div.find('div', class_='v-b-date')
                                if date_elem:
                                    # Try span first (more reliable), then aria-label as fallback
                                    date_span = date_elem.find('span', {'aria-hidden': 'true'})
                                    if date_span:
                                        day_text = date_span.get_text(strip=True)
                                    else:
                                        # Fallback to aria-label
                                        day_text = date_elem.get('aria-label', '')
                                        # Extract just the date part (before "has X bookings")
                                        if 'has' in day_text:
                                            day_text = day_text.split('has')[0].strip()
                                    
                                    day_name = day_text
                                    
                                    # Track found dates for debugging (only unique ones)
                                    if day_text and day_text not in found_dates:
                                        found_dates.append(day_text)
                                    
                                    # Check if this is today's date
                                    # Format can be "Friday, November 7th" or "Fri, Nov 7th" (abbreviated)
                                    # Also handle "Friday,November 7th" (no space after comma)
                                    day_text_lower = day_text.replace(',', ' ').replace('  ', ' ').lower().strip()
                                    
                                    # Remove ordinal suffixes (st, nd, rd, th) from day number in text
                                    day_text_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', day_text_lower)
                                    
                                    # Debug: print what we're comparing
                                    
                                    # Try full day/month names (with or without space after comma)
                                    today_pattern1 = f"{today_day_name.lower()},?\\s*{today_month_name.lower()}\\s*{today_day_num}"
                                    today_pattern2 = f"{today_day_name.lower()}\\s+{today_month_name.lower()}\\s+{today_day_num}"
                                    
                                    # Try abbreviated day/month names (e.g., "Fri, Nov 7" or "Thu Nov 20")
                                    today_pattern3 = f"{today_day_name_short.lower()},?\\s*{today_month_name_short.lower()}\\s*{today_day_num}"
                                    today_pattern4 = f"{today_day_name_short.lower()}\\s+{today_month_name_short.lower()}\\s+{today_day_num}"
                                    
                                    # Try without month (just day name and number)
                                    today_pattern5 = f"{today_day_name.lower()}\\s+{today_day_num}"
                                    today_pattern6 = f"{today_day_name_short.lower()}\\s+{today_day_num}"
                                    
                                    # More flexible pattern: just check if day name and number are present
                                    # This handles "Thu, Nov 20th" -> "thu nov 20"
                                    if (re.search(today_pattern1, day_text_clean) or 
                                        re.search(today_pattern2, day_text_clean) or
                                        re.search(today_pattern3, day_text_clean) or
                                        re.search(today_pattern4, day_text_clean) or
                                        re.search(today_pattern5, day_text_clean) or
                                        re.search(today_pattern6, day_text_clean)):
                                        is_today = True
                                    # Also try matching just the day name (full or short) and number
                                    # This is the most flexible - just check if both are present
                                    elif ((today_day_name.lower() in day_text_clean or today_day_name_short.lower() in day_text_clean) and 
                                          str(today_day_num) in day_text_clean):
                                        is_today = True
                                    # Even more flexible: check if the day number matches and day name is present
                                    # This handles cases where format might be slightly different
                                    elif str(today_day_num) in day_text_clean:
                                        # Check if any day name variant is present
                                        if (today_day_name.lower() in day_text_clean or 
                                            today_day_name_short.lower() in day_text_clean or
                                            today_month_name.lower() in day_text_clean or
                                            today_month_name_short.lower() in day_text_clean):
                                            is_today = True
                                    
                                    # Debug: if date found but not matching today, log it
                                    if not is_today and day_text:
                                        # This helps us see if date matching is the issue
                                        # Store debug info for later with what we're comparing
                                        debug_info = f"{day_text} -> cleaned: '{day_text_clean}' vs today: '{today_day_name_short} {today_month_name_short} {today_day_num}'"
                                        found_dates.append(debug_info)
                                    
                                    events_checked += 1
                                else:
                                    # No date element found - this shouldn't happen but handle it
                                    events_checked += 1
                            else:
                                # No date_div found - still count the event
                                events_checked += 1
                            
                            # Only include events from today
                            if is_today:
                                slot_name = f"{start_time_str} to {end_time_str} ({event_name})"
                                reserved_slots.append({
                                    'name': slot_name, 
                                    'available': False,
                                    'sort_key': (start_hour_24, start_min)  # For sorting by time only
                                })
                            # Debug: if event wasn't included, check why
                            # (This will help us see if date matching is the issue)
        
        # Sort by time (only today's events, so no need to sort by day)
        if reserved_slots:
            reserved_slots.sort(key=lambda x: x.get('sort_key', (0, 0)))
            # Remove sort_key before returning
            for slot in reserved_slots:
                slot.pop('sort_key', None)
        
        # Return results - only show today's reservations
        if reserved_slots:
            return {
                'website': self.config['websites'][website_index].get('name', f'Website {website_index + 1}'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': reserved_slots,
                'status': 'success',
                'message': f'Found {len(reserved_slots)} reserved time slot(s) for today'
            }
        else:
            # Check if we found the calendar structure at all
            date_divs = soup.find_all('div', class_='v-b-date')
            if date_divs:
                # Calendar found but no reservations for today - this is normal!
                # Debug: show what dates were found
                found_date_texts = []
                for date_div in date_divs[:5]:  # First 5 dates
                    try:
                        date_span = date_div.find('span', {'aria-hidden': 'true'})
                        if date_span:
                            found_date_texts.append(date_span.get_text(strip=True))
                        else:
                            found_date_texts.append(date_div.get('aria-label', 'Unknown'))
                    except:
                        pass
                
                # Also check if we found events but they weren't for today
                all_events = soup.find_all('div', class_='v-b-event')
                events_count = len(all_events) if all_events else 0
                
                debug_msg = f'No reservations found for today ({today_day_name}, {today_month_name} {today_day_num})'
                if found_date_texts:
                    debug_msg += f'. Calendar shows dates: {", ".join(found_date_texts[:3])}'
                if events_count > 0:
                    debug_msg += f'. Found {events_count} total event(s) but none matched today.'
                    # Show sample of what dates the events had
                    if found_dates:
                        debug_msg += f' Event dates checked: {", ".join(found_dates[:3])}'
                else:
                    debug_msg += f'. No events found in calendar (checked {events_found_count} events).'
                if found_dates and events_count == 0:
                    debug_msg += f' Debug: {", ".join(found_dates[:3])}'
                
                return {
                    'website': self.config['websites'][website_index].get('name', f'Website {website_index + 1}'),
                    'url': url,
                    'timestamp': self._get_est_timestamp(),
                    'courts': [],
                    'status': 'success',
                    'message': debug_msg
                }
            else:
                return {
                    'website': self.config['websites'][website_index].get('name', f'Website {website_index + 1}'),
                    'url': url,
                    'timestamp': self._get_est_timestamp(),
                    'courts': [],
                    'status': 'success',
                    'message': f'Could not find calendar structure. Found {len(all_vb_divs)} v-b elements total. Make sure Selenium is installed and ChromeDriver is available. If using Selenium, ensure the "availability" tab was clicked.'
                }
    
    def scrape_website_1(self, url: str) -> Dict:
        """
        Scrape first website (Pitt EMS) for court availability.
        Uses Selenium if available to render JavaScript, otherwise falls back to requests.
        """
        try:
            # Try Selenium first if available (for JavaScript-rendered content)
            if SELENIUM_AVAILABLE:
                try:
                    return self._scrape_with_selenium(url, 0)
                except Exception as e:
                    # Fall back to requests if Selenium fails
                    pass
            
            # Fallback to requests (won't work if JS is required, but worth trying)
            # First, try to get the main page to establish session/cookies
            try:
                main_page = self.session.get('https://pitt.emscloudservice.com/', timeout=10)
            except:
                pass  # Continue even if main page fails
            
            # Add referer for EMS systems
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://pitt.emscloudservice.com/'
            headers['Origin'] = 'https://pitt.emscloudservice.com'
            
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Check if we got redirected or got an error page
            if 'problem' in response.text.lower() or 'error' in response.text.lower():
                # Check if it's actually an error or just contains those words
                if 'there was a problem' in response.text.lower():
                    return {
                        'website': self.config['websites'][0].get('name', 'Website 1'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'error',
                        'message': 'Page returned an error. The URL may require authentication or the data parameter may have expired. Try opening the URL in a browser first.'
                    }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for error messages
            error_elements = soup.find_all(string=lambda text: text and 'problem' in text.lower())
            if error_elements:
                return {
                    'website': self.config['websites'][0].get('name', 'Website 1'),
                    'url': url,
                    'timestamp': self._get_est_timestamp(),
                    'courts': [],
                    'status': 'error',
                    'message': 'Page returned an error. The URL may require authentication or the data parameter may have expired. Try opening the URL in a browser first.'
                }
            
            courts = []
            
            # ============================================
            # EMS SYSTEM PATTERNS - CUSTOMIZE BELOW
            # ============================================
            # 
            # EMS systems typically show availability in:
            # 1. Tables with time slots (rows = times, cols = courts)
            # 2. Grid of divs with availability classes
            # 3. Calendar-style layouts
            #
            # Try these patterns (uncomment and modify):
            
            # ============================================
            # EMS CALENDAR GRID PARSING
            # ============================================
            # Structure: v-b-cal-column (days) -> v-b-hour (hours) -> check for v-b-event (bookings)
            
            # Try to parse the calendar HTML
            result = self._parse_calendar_html(soup, 0, url)
            if result.get('courts'):
                return result
            
            # Approach 2: Try finding the container (original approach)
            availability_container = soup.find('div', id='room-availability-control')
            if not availability_container:
                availability_container = soup.find('div', class_='vertical-book-grid-container')
            
            if availability_container:
                # Find all day columns
                day_columns = availability_container.find_all('div', class_='v-b-cal-column')
                
                # Time mapping: hour number to time string
                time_mapping = {
                    0: '12:00 AM', 1: '1:00 AM', 2: '2:00 AM', 3: '3:00 AM',
                    4: '4:00 AM', 5: '5:00 AM', 6: '6:00 AM', 7: '7:00 AM',
                    8: '8:00 AM', 9: '9:00 AM', 10: '10:00 AM', 11: '11:00 AM',
                    12: '12:00 PM', 13: '1:00 PM', 14: '2:00 PM', 15: '3:00 PM',
                    16: '4:00 PM', 17: '5:00 PM', 18: '6:00 PM', 19: '7:00 PM',
                    20: '8:00 PM', 21: '9:00 PM', 22: '10:00 PM', 23: '11:00 PM'
                }
                
                for day_col in day_columns:
                    # Get the date for this day
                    date_elem = day_col.find('div', class_='v-b-date')
                    if not date_elem:
                        continue
                    
                    date_span = date_elem.find('span', {'aria-hidden': 'true'})
                    day_name = date_span.get_text(strip=True) if date_span else 'Unknown Day'
                    
                    # Find all events (bookings) for this day
                    events = day_col.find_all('div', class_='v-b-event')
                    booked_hours = set()
                    
                    # Parse event times to find which hours are booked
                    for event in events:
                        # Try to get time from aria-label
                        aria_label = event.get('aria-label', '')
                        if 'To' in aria_label:
                            # Extract time range from aria-label
                            parts = aria_label.split('To')
                            if len(parts) == 2:
                                start_time_str = parts[0].strip().split()[-2:]  # Last 2 words (time and AM/PM)
                                end_time_str = parts[1].strip().split()[:2]    # First 2 words
                                
                                # Parse times (simplified - just extract hour)
                                for time_part in [start_time_str, end_time_str]:
                                    if len(time_part) >= 1:
                                        time_str = ' '.join(time_part)
                                        # Convert to hour (0-23)
                                        for hour, time_label in time_mapping.items():
                                            if time_label in time_str or time_str in time_label:
                                                booked_hours.add(hour)
                    
                    # Find all hour slots
                    hour_divs = day_col.find_all('div', class_='v-b-hour')
                    
                    # Check each hour - if not in booked_hours and has the div, it's available
                    for hour_div in hour_divs:
                        hour_num = hour_div.get('data-hour')
                        if hour_num is not None:
                            try:
                                hour = int(hour_num)
                                # If this hour is not booked, it's available
                                if hour not in booked_hours:
                                    time_str = time_mapping.get(hour, f'{hour}:00')
                                    slot_name = f"{day_name} - {time_str}"
                                    courts.append({'name': slot_name, 'available': True})
                            except ValueError:
                                pass
                
                # If we found courts, return them
                if courts:
                    return {
                        'website': self.config['websites'][0].get('name', 'Website 1'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': courts,
                        'status': 'success',
                        'message': f'Found {len(courts)} available time slot(s)'
                    }
            
            # If no availability container found, try fallback patterns
            # Pattern 1: Look for tables
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            time_slot = cells[0].get_text(strip=True)
                            for i, cell in enumerate(cells[1:], 1):
                                cell_text = cell.get_text(strip=True).lower()
                                if not any(word in cell_text for word in ['reserved', 'booked', 'unavailable', 'taken']):
                                    if cell_text and len(cell_text) < 50:
                                        courts.append({'name': f"Slot {i} - {time_slot}", 'available': True})
            
            # If still no courts found
            if not courts:
                # Check if we found the container but no day columns
                if availability_container:
                    day_cols = availability_container.find_all('div', class_='v-b-cal-column')
                    if day_cols:
                        return {
                            'website': self.config['websites'][0].get('name', 'Website 1'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': f'Found calendar structure with {len(day_cols)} day(s), but all time slots appear to be booked.'
                        }
                    else:
                        return {
                            'website': self.config['websites'][0].get('name', 'Website 1'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': 'Found availability container but no day columns. Page structure may have changed.'
                        }
                else:
                    # Save HTML for debugging
                    with open('debug_sample_1.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    # If we have Knockout.js bindings, suggest using Selenium
                    if 'Knockout.js' in str(soup) or 'data-bind' in str(soup):
                        return {
                            'website': self.config['websites'][0].get('name', 'Website 1'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': f'Page uses JavaScript (Knockout.js) to render calendar. BeautifulSoup cannot execute JavaScript. Install Selenium: pip install selenium. HTML saved to debug_sample_1.html.'
                        }
                    else:
                        return {
                            'website': self.config['websites'][0].get('name', 'Website 1'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': f'Could not find calendar structure. HTML saved to debug_sample_1.html. The URL may be expired or require authentication.'
                        }
            
            return {
                'website': self.config['websites'][0].get('name', 'Website 1'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': courts,
                'status': 'success',
                'message': f'Found {len(courts)} available slot(s)'
            }
            
        except Exception as e:
            return {
                'website': self.config['websites'][0].get('name', 'Website 1'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': [],
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
    
    def scrape_website_2(self, url: str) -> Dict:
        """
        Scrape second website (Pitt EMS) for court availability.
        Uses Selenium if available to render JavaScript, otherwise falls back to requests.
        """
        # Use the same Selenium method as website 1
        if SELENIUM_AVAILABLE:
            return self._scrape_with_selenium(url, website_index=1)
        
        # Fallback to old method if Selenium not available
        return self._scrape_website_2_old(url)
    
    def _scrape_website_2_old(self, url: str) -> Dict:
        """
        Scrape second website (Pitt EMS) for court availability.
        Same as website 1 - EMS system patterns.
        """
        try:
            # First, try to get the main page to establish session/cookies
            try:
                main_page = self.session.get('https://pitt.emscloudservice.com/', timeout=10)
            except:
                pass  # Continue even if main page fails
            
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://pitt.emscloudservice.com/'
            headers['Origin'] = 'https://pitt.emscloudservice.com'
            
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # Check if we got redirected or got an error page
            if 'problem' in response.text.lower() or 'error' in response.text.lower():
                if 'there was a problem' in response.text.lower():
                    return {
                        'website': self.config['websites'][1].get('name', 'Website 2'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'error',
                        'message': 'Page returned an error. The URL may require authentication or the data parameter may have expired. Try opening the URL in a browser first.'
                    }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            error_elements = soup.find_all(string=lambda text: text and 'problem' in text.lower())
            if error_elements:
                return {
                    'website': self.config['websites'][1].get('name', 'Website 2'),
                    'url': url,
                    'timestamp': self._get_est_timestamp(),
                    'courts': [],
                    'status': 'error',
                    'message': 'Page returned an error. The URL may require authentication or the data parameter may have expired. Try opening the URL in a browser first.'
                }
            
            courts = []
            
            # Same EMS calendar grid parsing as website 1
            availability_container = soup.find('div', id='room-availability-control')
            if not availability_container:
                availability_container = soup.find('div', class_='vertical-book-grid-container')
            
            # Debug: Check if we found the container
            if not availability_container:
                test_divs = soup.find_all('div', class_=lambda x: x and 'v-b' in str(x))
                debug_info = f"Could not find availability container. Found {len(test_divs)} divs with 'v-b' in class name."
            else:
                debug_info = "Found availability container."
            
            if availability_container:
                day_columns = availability_container.find_all('div', class_='v-b-cal-column')
                
                time_mapping = {
                    0: '12:00 AM', 1: '1:00 AM', 2: '2:00 AM', 3: '3:00 AM',
                    4: '4:00 AM', 5: '5:00 AM', 6: '6:00 AM', 7: '7:00 AM',
                    8: '8:00 AM', 9: '9:00 AM', 10: '10:00 AM', 11: '11:00 AM',
                    12: '12:00 PM', 13: '1:00 PM', 14: '2:00 PM', 15: '3:00 PM',
                    16: '4:00 PM', 17: '5:00 PM', 18: '6:00 PM', 19: '7:00 PM',
                    20: '8:00 PM', 21: '9:00 PM', 22: '10:00 PM', 23: '11:00 PM'
                }
                
                for day_col in day_columns:
                    date_elem = day_col.find('div', class_='v-b-date')
                    if not date_elem:
                        continue
                    
                    date_span = date_elem.find('span', {'aria-hidden': 'true'})
                    day_name = date_span.get_text(strip=True) if date_span else 'Unknown Day'
                    
                    events = day_col.find_all('div', class_='v-b-event')
                    booked_hours = set()
                    
                    for event in events:
                        aria_label = event.get('aria-label', '')
                        if 'To' in aria_label:
                            parts = aria_label.split('To')
                            if len(parts) == 2:
                                start_time_str = parts[0].strip().split()[-2:]
                                end_time_str = parts[1].strip().split()[:2]
                                
                                for time_part in [start_time_str, end_time_str]:
                                    if len(time_part) >= 1:
                                        time_str = ' '.join(time_part)
                                        for hour, time_label in time_mapping.items():
                                            if time_label in time_str or time_str in time_label:
                                                booked_hours.add(hour)
                    
                    hour_divs = day_col.find_all('div', class_='v-b-hour')
                    
                    for hour_div in hour_divs:
                        hour_num = hour_div.get('data-hour')
                        if hour_num is not None:
                            try:
                                hour = int(hour_num)
                                if hour not in booked_hours:
                                    time_str = time_mapping.get(hour, f'{hour}:00')
                                    slot_name = f"{day_name} - {time_str}"
                                    courts.append({'name': slot_name, 'available': True})
                            except ValueError:
                                pass
                
                if courts:
                    return {
                        'website': self.config['websites'][1].get('name', 'Website 2'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': courts,
                        'status': 'success',
                        'message': f'Found {len(courts)} available time slot(s)'
                    }
            
            # Fallback to table parsing
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            time_slot = cells[0].get_text(strip=True)
                            for i, cell in enumerate(cells[1:], 1):
                                cell_text = cell.get_text(strip=True).lower()
                                if not any(word in cell_text for word in ['reserved', 'booked', 'unavailable', 'taken']):
                                    if cell_text and len(cell_text) < 50:
                                        courts.append({'name': f"Slot {i} - {time_slot}", 'available': True})
            
            if not courts:
                if availability_container:
                    day_cols = availability_container.find_all('div', class_='v-b-cal-column')
                    if day_cols:
                        return {
                            'website': self.config['websites'][1].get('name', 'Website 2'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': f'Found calendar structure with {len(day_cols)} day(s), but all time slots appear to be booked.'
                        }
                    else:
                        return {
                            'website': self.config['websites'][1].get('name', 'Website 2'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'success',
                            'message': 'Found availability container but no day columns. Page structure may have changed.'
                        }
                else:
                    with open('debug_sample_2.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    debug_msg = debug_info if 'debug_info' in locals() else "Could not find calendar structure."
                    return {
                        'website': self.config['websites'][1].get('name', 'Website 2'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'success',
                        'message': f'Could not find calendar structure. HTML saved to debug_sample_2.html. {debug_msg} The URL may be expired or require authentication.'
                    }
            
            return {
                'website': self.config['websites'][1].get('name', 'Website 2'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': courts,
                'status': 'success',
                'message': f'Found {len(courts)} available slot(s)'
            }
            
        except Exception as e:
            return {
                'website': self.config['websites'][1].get('name', 'Website 2'),
                'url': url,
                'timestamp': self._get_est_timestamp(),
                'courts': [],
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
    
    def check_all_websites(self) -> List[Dict]:
        """Check availability from all enabled websites (runs in parallel for speed with retries)."""
        enabled_sites = [(i, site_config) for i, site_config in enumerate(self.config['websites']) 
                        if site_config.get('enabled', True)]
        
        if not enabled_sites:
            return []
        
        # Check if running in cloud - use sequential scraping to avoid timeouts
        import os
        is_cloud = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
        
        results = [None] * len(self.config['websites'])
        
        if is_cloud:
            # In cloud: run sequentially with strict timeout (each court gets 14s, total ~28s for 2 courts)
            timeout_per_court = 14  # 14s per court to stay under 30s total
            for i, site_config in enabled_sites:
                url = site_config['url']
                start_time = time.time()
                result = None
                try:
                    # Use threading with timeout to enforce per-court limit
                    result_container = [None]
                    exception_container = [None]
                    
                    def scrape_with_timeout():
                        try:
                            if i == 0:
                                result_container[0] = self.scrape_website_1(url)
                            elif i == 1:
                                result_container[0] = self.scrape_website_2(url)
                            else:
                                result_container[0] = self.scrape_website_1(url)
                        except Exception as e:
                            exception_container[0] = e
                    
                    thread = threading.Thread(target=scrape_with_timeout, daemon=True)
                    thread.start()
                    thread.join(timeout=timeout_per_court)
                    
                    if thread.is_alive():
                        # Timeout - create error result
                        result = {
                            'website': self.config['websites'][i].get('name', f'Website {i + 1}'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'error',
                            'message': f'Request timed out after {timeout_per_court} seconds'
                        }
                    elif exception_container[0]:
                        result = {
                            'website': self.config['websites'][i].get('name', f'Website {i + 1}'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'error',
                            'message': f'Error: {str(exception_container[0])}'
                        }
                    else:
                        result = result_container[0]
                        
                except Exception as e:
                    result = {
                        'website': self.config['websites'][i].get('name', f'Website {i + 1}'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'error',
                        'message': f'Error: {str(e)}'
                    }
                
                if result:
                    results[i] = result
        else:
            # Local: run in parallel for speed
            threads = []
            
            def scrape_worker(index: int, url: str, max_retries=1):
                """Worker function to scrape a single website with retries."""
                result = None
                for attempt in range(max_retries + 1):
                    try:
                        if index == 0:
                            result = self.scrape_website_1(url)
                        elif index == 1:
                            result = self.scrape_website_2(url)
                        else:
                            result = self.scrape_website_1(url)
                        
                        # If we got a result (even if error), use it
                        if result:
                            results[index] = result
                            return
                    except Exception as e:
                        if attempt < max_retries:
                            # Wait before retry with exponential backoff
                            time.sleep(min(2 ** attempt, 3))
                            continue
                        # Last attempt failed, create error result
                        result = {
                            'website': self.config['websites'][index].get('name', f'Website {index + 1}'),
                            'url': url,
                            'timestamp': self._get_est_timestamp(),
                            'courts': [],
                            'status': 'error',
                            'message': f'Error after {max_retries + 1} attempts: {str(e)}'
                        }
                
                # If we still don't have a result, create a default error
                if not result:
                    results[index] = {
                        'website': self.config['websites'][index].get('name', f'Website {index + 1}'),
                        'url': url,
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'error',
                        'message': f'Failed to scrape after {max_retries + 1} attempts'
                    }
                else:
                    results[index] = result
            
            # Start all scrapers in parallel
            for i, site_config in enabled_sites:
                url = site_config['url']
                thread = threading.Thread(target=scrape_worker, args=(i, url), daemon=True)
                thread.start()
                threads.append((thread, i, site_config))
            
            # Wait for all threads to complete with timeout
            timeout = 60
            for thread, index, site_config in threads:
                thread.join(timeout=timeout)
                if thread.is_alive():
                    # Thread timed out, create error result
                    results[index] = {
                        'website': self.config['websites'][index].get('name', f'Website {index + 1}'),
                        'url': site_config['url'],
                        'timestamp': self._get_est_timestamp(),
                        'courts': [],
                        'status': 'error',
                        'message': f'Request timed out after {timeout} seconds'
                    }
        
        # Filter out None results and maintain order
        return [r for r in results if r is not None]

