import os
import requests
from playwright.sync_api import sync_playwright

# Base directory for saving profiles
BASE_DIR = "linkedin_output"

def scrape_linkedin():
    # Launch Playwright and connect to the existing browser
    with sync_playwright() as p:
        try:
            # Debugging: Check if Chrome is accessible at http://localhost:9222
            print("Checking if Chrome is accessible at http://localhost:9222...")
            try:
                response = requests.get("http://localhost:9222/json")
                print("Chrome remote debugging response:", response.json())
            except Exception as e:
                print("Error connecting to Chrome remote debugging:", e)
                return

            # Connect to the existing Chrome browser instance
            print("Connecting to Chrome at http://127.0.0.1:9222...")
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            print("Connected to existing browser.")

            # Create a new browser context to isolate the scraping session
            context = browser.new_context()
            page = context.new_page()

            # Navigate to the target profile
            target_profile_url = "https://www.linkedin.com/in/posokin/"
            page.goto(target_profile_url)

            # Wait for the page to load completely
            page.wait_for_load_state("networkidle")

            # Click on the "Connections" section (adjust selector if needed)
            print("Navigating to mutual connections...")
            try:
                page.click('a:has-text("Connections")', timeout=30000)  # Adjust this selector if necessary
            except Exception as e:
                print("Error clicking 'Connections' link:", e)
                return

            page.wait_for_load_state("networkidle")

            # Scrape mutual connections
            scrape_mutual_connections(page)

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Close the browser context after scraping
            context.close()

def scrape_mutual_connections(page):
    # Create base output directory
    os.makedirs(BASE_DIR, exist_ok=True)

    # Extract all mutual connection links
    print("Extracting mutual connection links...")
    connection_links = []
    while True:
        # Get all profile links on the current page
        links = page.query_selector_all('a[data-test-app-aware-link]')
        for link in links:
            href = link.get_attribute("href")
            if href and "/in/" in href and href not in connection_links:
                connection_links.append(href)

        # Check if there's a "Next" button to paginate
        next_button = page.query_selector('button[aria-label="Next"]')
        if next_button and not next_button.is_disabled():
            print("Navigating to the next page of connections...")
            next_button.click()
            page.wait_for_load_state("networkidle")
        else:
            break

    # Scrape each profile
    print(f"Found {len(connection_links)} mutual connections. Scraping profiles...")
    for i, profile_url in enumerate(connection_links, start=1):
        print(f"Scraping profile {i}/{len(connection_links)}: {profile_url}")
        scrape_profile(page, profile_url)

def scrape_profile(page, profile_url):
    # Navigate to the profile
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    # Extract username from URL
    username = profile_url.split("/in/")[-1].split("?")[0]  # Handle query parameters in the URL
    profile_dir = os.path.join(BASE_DIR, username)
    os.makedirs(profile_dir, exist_ok=True)

    # Save the profile page as HTML
    html_content = page.content()
    output_file = os.path.join(profile_dir, "profile.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Saved profile: {output_file}")

# Run the scraper
if __name__ == "__main__":
    scrape_linkedin()