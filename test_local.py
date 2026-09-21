"""
Local test of the scraper without Apify Actor framework
"""
import asyncio
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin

async def test_scrape():
    url = "https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/1092/tractors"
    
    print("Starting Playwright...")
    playwright = await async_playwright().start()
    
    print("Launching browser...")
    browser = await playwright.chromium.launch(headless=False)
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = await context.new_page()
    
    print(f"Navigating to: {url}")
    await page.goto(url, wait_until='domcontentloaded', timeout=90000)
    
    print("Waiting for content to load...")
    await page.wait_for_timeout(15000)  # Long wait for Cloudflare
    
    page_title = await page.title()
    print(f"Page title: {page_title}")
    
    if "Just a moment" in page_title:
        print("⚠️  Cloudflare challenge page detected!")
        print("Waiting additional time...")
        await page.wait_for_timeout(20000)
        page_title = await page.title()
        print(f"New title: {page_title}")
    
    # Try selector strategies
    print("\n" + "="*70)
    print("TESTING SELECTOR STRATEGIES:")
    print("="*70)
    
    strategies = [
        ('[data-listing-id]', 'Data attribute'),
        ('article', 'Article tag'),
        ('.listing-item', 'Class: listing-item'),
        ('[class*="listing"]', 'Class contains listing'),
    ]
    
    listings = []
    for selector, name in strategies:
        elements = await page.query_selector_all(selector)
        print(f"{name} ({selector}): {len(elements)} elements")
        if elements and not listings:
            listings = elements
    
    # Heading strategy
    if not listings:
        print("\nTrying heading strategy...")
        headings = await page.query_selector_all('h2, h3, h4')
        print(f"Found {len(headings)} headings")
        containers = []
        for heading in headings:
            text = await heading.text_content()
            if text and re.search(r'20\d{2}', text.strip()):
                print(f"  - Found year in: {text.strip()[:50]}")
                container = await heading.evaluate_handle('el => el.closest("div, article, section")')
                if container:
                    containers.append(container.as_element())
        listings = containers[:5]  # Test first 5
        print(f"Heading strategy found {len(listings)} containers")
    
    if not listings:
        print("\n❌ NO LISTINGS FOUND!")
        await page.screenshot(path='test_no_results.png')
        html = await page.content()
        with open('test_page_source.html', 'w') as f:
            f.write(html)
        print("Saved screenshot and HTML for debugging")
    else:
        print(f"\n✓ Found {len(listings)} listings")
        print("\n" + "="*70)
        print("EXTRACTING FIRST 3 LISTINGS:")
        print("="*70)
        
        for i, listing in enumerate(listings[:3], 1):
            print(f"\n--- Listing {i} ---")
            
            # Title
            title = ''
            for selector in ['h2', 'h3', 'h4']:
                title_elem = await listing.query_selector(selector)
                if title_elem:
                    title = await title_elem.inner_text()
                    title = title.strip()
                    if title:
                        break
            print(f"Title: {title}")
            
            # URL
            link_elem = await listing.query_selector('a[href*="/listing/"]')
            url = ''
            if link_elem:
                href = await link_elem.get_attribute('href')
                url = urljoin('https://www.tractorhouse.com', href)
            print(f"URL: {url}")
            
            # Get all text for parsing
            listing_text = await listing.inner_text()
            
            # Price
            price_match = re.search(r'USD \$[\d,]+', listing_text)
            price = price_match.group(0) if price_match else 'N/A'
            print(f"Price: {price}")
            
            # Location
            location_match = re.search(r'Location:\s*([^\n]+)', listing_text)
            location = location_match.group(1).strip() if location_match else 'N/A'
            print(f"Location: {location}")
            
            print(f"\nSample text (first 200 chars):")
            print(listing_text[:200])
    
    input("\nPress Enter to close browser...")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_scrape())
