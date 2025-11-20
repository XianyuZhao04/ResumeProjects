# 🏸 Badminton Court Availability

A simple local web app to check badminton court availability from Pitt EMS system. Access it from your iPhone on the same WiFi network - no cloud deployment needed!

## ✨ Features

- **📱 Mobile-Optimized**: Beautiful, touch-friendly interface designed for iPhone
- **🔄 Auto-Refresh**: Automatically fetches data when the app launches and refreshes every 30 seconds
- **⚡ Fast Loading**: Parallel scraping of multiple courts for faster data retrieval
- **🔒 Shows Reserved Times**: Displays today's reserved time slots so you know when courts are unavailable
- **🛑 Auto-Shutdown**: Automatically shuts down after 5 minutes of inactivity or when browser tab closes
- **🎯 Today Only**: Filters to show only today's reservations for quick reference

## 🎯 What It Does

The app scrapes the Pitt EMS booking system to check availability for badminton courts. It:

1. **Fetches court data** from the EMS calendar system using Selenium (for JavaScript-rendered content)
2. **Parses reserved time slots** from the calendar grid structure
3. **Filters to today only** - shows only reservations for the current day
4. **Displays results** in a clean, mobile-friendly interface
5. **Auto-refreshes** to keep data up-to-date

You can access it from your iPhone on the same WiFi network - just open the IP address shown in the terminal!

## 🚀 Quick Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `flask` - Web framework
- `selenium` - For JavaScript rendering
- `webdriver-manager` - Automatic ChromeDriver management
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP requests

### Step 2: Verify URLs

1. Open both court URLs in your browser to make sure they work
2. You should see a calendar grid showing availability
3. If you see an error, you may need to:
   - Log in to the EMS system first
   - Get fresh URLs (the `data` parameter in the URL might expire)

### Step 3: Configure Courts

1. Copy the example config file:
   ```bash
   cp config.example.json config.json
   ```
   (Or create `config.json` manually)

2. Edit `config.json` and add your court URLs:
   ```json
   {
     "websites": [
       {
         "name": "Court 610A",
         "url": "https://pitt.emscloudservice.com/web/LocationDetails.aspx?data=YOUR_URL_DATA_HERE",
         "enabled": true
       },
       {
         "name": "Court 610B",
         "url": "https://pitt.emscloudservice.com/web/LocationDetails.aspx?data=YOUR_URL_DATA_HERE",
         "enabled": true
       }
     ]
   }
   ```

**Note**: `config.json` is in `.gitignore` to protect your URLs. Always use `config.example.json` as a template.

### Step 4: Run the App

```bash
python app.py
```

The app will start and display:
```
🏸 Badminton Court Availability
============================================================

📱 To access from your iPhone:
   1. Make sure your phone is on the same WiFi network
   2. Open Safari and go to: http://192.168.1.100:5000

💻 Or access locally at: http://localhost:5000

⏹️  Server will auto-shutdown after 5 minutes of inactivity
   (or when you close the browser tab)
```

### Step 5: Access from Your iPhone

1. Make sure your iPhone is on the **same WiFi network** as your computer
2. Open Safari on your iPhone
3. Go to the IP address shown (e.g., `http://192.168.1.100:5000`)
4. **Optional**: Tap Share → "Add to Home Screen" to create an app icon

## 📱 What You'll See

The app displays:
- **Court name** (610A or 610B)
- **Reserved time slots** for today in format: "10:30 AM to 11:45 AM (Event Name)"
- **Status indicator** (✓ Connected or ✗ Error)
- **Last update timestamp**
- **Message** indicating if no reservations were found (court is available!)

Each reserved slot shows the time range and event name. If no reservations are shown, the court is available for the day!

## 🔧 How It Works

### Scraping Process

The scraper uses Selenium to render JavaScript-heavy pages:

1. **Launches headless Chrome** to render the EMS calendar
2. **Clicks the "availability" tab** to show the calendar view
3. **Waits for calendar to load** - finds the `v-b-date` elements
4. **Parses reserved events** - extracts `v-b-event` divs with time ranges from `aria-label` attributes
5. **Filters to today** - matches events to today's date
6. **Returns results** - shows only today's reserved time slots

### Technical Details

The scraper looks for:
- `v-b-date` - Date headers in the calendar
- `v-b-event` - Reserved time slot divs
- `aria-label` attributes - Contains event name and time range (e.g., "Event Name10:30 AM To 11:45 AM")
- `v-b-cal-column` - Day columns in the calendar grid

### Parallel Processing

Both courts are scraped **simultaneously** using threading, making the app load faster.

## 🔄 Updating URLs

If the URLs expire or you need to change them:

1. Go to the EMS booking system
2. Navigate to each court's availability page
3. Copy the full URL from the address bar
4. Update `config.json` with the new URLs

The URLs contain encoded data that may expire, so you might need to refresh them periodically.

## 📄 License

This is a personal project for checking badminton court availability. Use at your own discretion.
