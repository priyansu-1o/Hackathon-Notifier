from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

def scrape_unstop_with_selenium(url):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for content to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "app-competition-listing"))
        )
        
        time.sleep(2)  # Additional wait for dynamic content
        
        # Scroll to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        html_content = driver.page_source
        driver.quit()
        return html_content
        
    except Exception as e:
        print(f"Selenium error: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def extract_hackathons_from_rendered_html(html_content):
    """Extract hackathons from the rendered HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    hackathons = []
    
    # Find all competition listings
    listings = soup.find_all('app-competition-listing')
    print(f"Found {len(listings)} competition listings")
    
    for listing in listings:
        hackathon_link = listing.find('a', class_='item')
        if hackathon_link:
            data = extract_hackathon_data_improved(hackathon_link)
            if data and data not in hackathons:
                hackathons.append(data)
    
    return hackathons

def extract_hackathon_data_improved(hackathon_element):
    """Improved extraction with better error handling"""
    try:
        # Basic info
        title_elem = hackathon_element.find('h2', class_='double-wrap')
        organizer_elem = hackathon_element.find('p', class_='single-wrap')
        
        title = title_elem.get_text(strip=True) if title_elem else "No Title"
        organizer = organizer_elem.get_text(strip=True) if organizer_elem else "No Organizer"
        
        # URL
        hackathon_url = hackathon_element.get('href', '')
        full_url = f"https://unstop.com{hackathon_url}" if hackathon_url else ''
        
        # Extract location from individual hackathon page
        location = scrape_location_info(full_url)
        
        hackathon_data = {
            'title': title,
            'organizer': organizer,
            'url': full_url,
            'location': location,
        }
        
        print(f"✓ {title}")
        return hackathon_data
        
    except Exception as e:
        print(f"✗ Error extracting data: {e}")
        return None

def scrape_location_info(url):
    """Extract location information from individual hackathon page"""
    if not url:
        return "No URL provided"
    
    # Setup Chrome options for location scraping
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for location elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "location"))
        )
        
        time.sleep(1)  # Additional wait for dynamic content
        
        # Find all location elements
        location_elements = driver.find_elements(By.CLASS_NAME, "location")
        
        location_text = "Location not found"
        for element in location_elements:
            element_text = element.text.strip()
            
            # Check if this is the main location
            if any(indicator in element_text for indicator in ['College', 'University', 'Institute', 'Campus', 'Coimbatore', 'Chennai', 'Bangalore', 'Delhi', 'Mumbai', 'Hyderabad', 'Pune', 'Online']):
                location_text = element_text
                break
        
        # If no location found with indicators, use the first location element
        if location_text == "Location not found" and location_elements:
            location_text = location_elements[0].text.strip()
        
        driver.quit()
        return location_text
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return f"Location not available"

def main():
    url = "https://unstop.com/all-opportunities?oppstatus=recent&searchTerm=hackathons"
    
    print("Starting Selenium scraping...")
    rendered_html = scrape_unstop_with_selenium(url)
    
    if rendered_html:
        print("Extracting hackathons from rendered HTML...")
        hackathons = extract_hackathons_from_rendered_html(rendered_html)
        
        print(f"\n=== RESULTS ===")
        print(f"Total hackathons found: {len(hackathons)}")
        
        # CORRECTED: Filter for Chennai OR Online hackathons
        chennai_hackathons = []
        for h in hackathons:
            if 'Chennai' in h['location'] or 'Online' in h['location']:
                chennai_hackathons.append(h)
        
        print(f"\n=== CHENNAI & ONLINE HACKATHONS ({len(chennai_hackathons)}) ===")
        for i, hackathon in enumerate(chennai_hackathons, 1):
            print(f"{i}. {hackathon['title']}")
            print(f"   Organizer: {hackathon['organizer']}")
            print(f"   URL: {hackathon['url']}")
            print(f"   Location: {hackathon['location']}")
            print()
        
        # Save to JSON
        with open('hackathons_data.json', 'w', encoding='utf-8') as f:
            json.dump(hackathons, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to hackathons_data.json")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        print(f"Total hackathons: {len(hackathons)}")
        print(f"Chennai & Online hackathons: {len(chennai_hackathons)}")
        
        # Additional breakdown
        chennai_only = [h for h in hackathons if 'Chennai' in h['location']]
        online_only = [h for h in hackathons if 'Online' in h['location']]
        print(f"Chennai only: {len(chennai_only)}")
        print(f"Online only: {len(online_only)}")
        
    else:
        print("Failed to get rendered content")

if __name__ == "__main__":
    main()