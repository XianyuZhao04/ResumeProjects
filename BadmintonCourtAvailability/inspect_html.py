"""
Helper script to inspect HTML structure of your websites.
This helps you figure out what to scrape!

Usage:
    python inspect_html.py
"""
import json
import requests
from bs4 import BeautifulSoup


def inspect_website(url, website_name):
    """Fetch and display HTML structure of a website."""
    print(f"\n{'='*70}")
    print(f"Inspecting: {website_name}")
    print(f"URL: {url}")
    print(f"{'='*70}\n")
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("✅ Successfully fetched the page\n")
        
        # Look for common patterns
        print("🔍 Looking for common patterns...\n")
        
        # Check for tables
        tables = soup.find_all('table')
        if tables:
            print(f"📊 Found {len(tables)} table(s):")
            for i, table in enumerate(tables[:3]):  # Show first 3
                print(f"\n   Table {i+1}:")
                rows = table.find_all('tr')[:5]  # First 5 rows
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        cell_texts = [cell.get_text(strip=True)[:30] for cell in cells]
                        print(f"      {' | '.join(cell_texts)}")
            print()
        
        # Check for divs with common class names
        common_classes = ['court', 'availability', 'slot', 'time', 'reservation', 'booking']
        for class_name in common_classes:
            divs = soup.find_all('div', class_=lambda x: x and class_name.lower() in str(x).lower())
            if divs:
                print(f"📦 Found {len(divs)} div(s) with '{class_name}' in class name")
                for div in divs[:3]:  # Show first 3
                    text = div.get_text(strip=True)[:50]
                    classes = div.get('class', [])
                    print(f"      Classes: {classes}")
                    print(f"      Text: {text}...")
                print()
        
        # Check for list items
        lists = soup.find_all(['ul', 'ol'])
        if lists:
            print(f"📋 Found {len(lists)} list(s)")
            for lst in lists[:2]:  # Show first 2
                items = lst.find_all('li')[:3]  # First 3 items
                for item in items:
                    text = item.get_text(strip=True)[:50]
                    print(f"      • {text}...")
            print()
        
        # Show a sample of the HTML structure
        print("📄 Sample HTML structure (first 1000 chars):")
        print("-" * 70)
        print(str(soup)[:1000])
        print("-" * 70)
        
        # Save full HTML to file for inspection
        filename = f"html_sample_{website_name.lower().replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print(f"\n💾 Full HTML saved to: {filename}")
        print("   Open this file in a browser to see the structure better!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        print("Make sure:")
        print("  1. The URL is correct")
        print("  2. You have internet connection")
        print("  3. The website doesn't require login")


def main():
    """Main function to inspect all websites in config."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        print("\n" + "="*70)
        print("🔍 HTML Structure Inspector")
        print("="*70)
        print("\nThis script helps you see the HTML structure of your websites")
        print("so you can customize the scraper functions.\n")
        
        for site in config['websites']:
            if site.get('enabled', True):
                inspect_website(site['url'], site['name'])
        
        print("\n" + "="*70)
        print("✅ Inspection complete!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Look at the HTML samples above")
        print("  2. Open the saved HTML files in a browser")
        print("  3. Update scraper.py with the correct selectors")
        print("  4. Or share the website URLs with me and I can help!\n")
        
    except FileNotFoundError:
        print("❌ Error: config.json not found")
        print("   Please create config.json first with your website URLs")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == '__main__':
    main()

