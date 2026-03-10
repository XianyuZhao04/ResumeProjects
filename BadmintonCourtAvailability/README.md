# Badminton Court Availability

A web app that shows a 7-day availability calendar for two badminton courts at Pitt's Recreation and Wellness Center. It calls the Pitt EMS booking system's internal API directly and displays reserved time slots by day, so you can quickly find open court time across the week.

Live demo: [badminton-court-availability.onrender.com](https://badminton-court-availability.onrender.com)

---

## Features

- 7-day week view with reservations grouped by day
- Both courts selectable via tabs
- Today highlighted and auto-scrolled into view
- Auto-refreshes every 30 seconds
- Mobile-optimized, accessible from your phone on the same WiFi (Might remove soon...)
- Auto-shutdown after 5 minutes of inactivity (local mode only)

## How It Works

Rather than scraping the EMS web page with a browser, the app calls the internal JSON API that the EMS page itself uses (`AnonymousServersApi.aspx/GetLocationDetailsAvailability`). This returns a week's worth of bookings in one request with no authentication required. The room IDs for each court were discovered by intercepting browser network traffic.

On Render, results are cached for 5 minutes and refreshed in the background. Locally, data is fetched on demand.

---

## Tech Stack

- Python, Flask
- Requests (HTTP client)
- Gunicorn (production server)
- Docker (Render deployment)

---

## Local Setup

### Prerequisites

- Python 3.11+

### Steps

1. Clone the repo and navigate into it:
   ```bash
   git clone <your-repo-url>
   cd BadmintonCourtAvailability
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Mac/Linux:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your config file:
   ```bash
   cp config.example.json config.json
   ```
   Then open `config.json` and paste in the EMS URLs for each court.

5. Run the app:
   ```bash
   python app.py
   ```

6. Open the URL shown in the terminal. To access from your phone, make sure it's on the same WiFi network and use the IP address shown (e.g. `http://192.168.1.100:5000`). (Again, might be removed soon...)

### Updating Court URLs

The `data=` token in each URL may expire over time. If the app stops working, go to the EMS booking page for each court in your browser, copy the full URL, and update `config.json`.

---

## Configuration

`config.json` (gitignored) follows this structure:

```json
{
  "websites": [
    {
      "name": "Court 610A",
      "url": "https://pitt.emscloudservice.com/web/LocationDetails.aspx?data=...",
      "enabled": true
    },
    {
      "name": "Court 610B",
      "url": "https://pitt.emscloudservice.com/web/LocationDetails.aspx?data=...",
      "enabled": true
    }
  ]
}
```

Set `enabled` to `false` to skip a court without removing it from the config.

The room IDs used by the API (`456` for 610A, `457` for 610B) are *hardcoded* in `scraper.py`. If courts change, these can be rediscovered by opening the EMS page in a browser, clicking the Availability tab, and inspecting the network request to `GetLocationDetailsAvailability`.

---

## Notes

- This project was developed with the assistance of AI tools.