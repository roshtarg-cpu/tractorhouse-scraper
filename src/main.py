"""
Updated TractorHouse.com scraper with corrected selectors
Based on analysis of actual page structure
"""
from apify import Actor
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

async def main():
    async with Actor:
        Actor.log.info("TractorHouse Scraper starting...")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        search_mode = actor_input.get('searchMode', 'filters')
        start_url = actor_input.get('startUrl', '')
        category = actor_input.get('category', 'tractors')
        max_results = actor_input.get('maxResults', 100)
        proxy_config = actor_input.get('proxyConfiguration', {'useApifyProxy': True})
        
        Actor.log.info(f"Search mode: {search_mode}")
        Actor.log.info(f"Max results: {max_results}")
        
        # Build search URL
        if search_mode == 'url' and start_url:
            search_url = start_url
        else:
            # Map category to TractorHouse category ID
            category_map = {
                'tractors': '1092',
                'combines': '1024',
                'headers': '1046',
                'planters': '1081',
                'grain-drills': '1044',
                'sprayers': '1086',
                'tillage': '1091',
                'hay-forage': '1047',
                'harvesting': '1045',
                'loaders': '1055',
                'skid-steers': '1085',
                'utility-vehicles': '1096',
                'trailers': '1090'
            }
            
            cat_id = category_map.get(category, '1092')
            search_url = f"https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/{cat_id}"
        
        Actor.log.info(f"Base search URL: {search_url}")
        
        # Launch browser
        playwright = await async_playwright().start()
        
        proxy_settings = None
        if proxy_config.get('useApifyProxy'):
            # Apify SDK v1 proxy setup
            import os
            proxy_password = os.getenv('APIFY_PROXY_PASSWORD')
            if proxy_password:
                proxy_settings = {
                    'server': 'http://proxy.apify.com:8000',
                    'username': 'auto',
                    'password': proxy_password
                }
                Actor.log.info("Using Apify proxy")
            else:
                Actor.log.warning("Apify proxy requested but APIFY_PROXY_PASSWORD not set")
        
        browser = await playwright.chromium.launch(
            headless=True,
            proxy=proxy_settings
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        results_count = 0
        page_num = 1
        
        try:
            while results_count < max_results:
                # Build paginated URL
                current_url = f"{search_url}?p={page_num}"
                Actor.log.info(f"Scraping page {page_num}: {current_url}")
                
                # Load page with extended timeout for Cloudflare
                try:
                    await page.goto(current_url, wait_until='domcontentloaded', timeout=90000)
                    Actor.log.info("Page loaded, waiting for content...")
                    
                    # Wait longer for JavaScript and Cloudflare bypass
                    await page.wait_for_timeout(10000)
                    
                    # Check if we're on Cloudflare challenge page
                    page_title = await page.title()
                    if "Just a moment" in page_title or "challenge" in page_title.lower():
                        Actor.log.warning("Cloudflare challenge detected, waiting longer...")
                        await page.wait_for_timeout(15000)
                    
                except Exception as e:
                    Actor.log.error(f"Error loading page: {e}")
                    break
                
                # Try multiple selector strategies
                listings = []
                
                # Strategy 1: Look for elements with listing data attributes
                listings = await page.query_selector_all('[data-listing-id]')
                Actor.log.info(f"Strategy 1 ([data-listing-id]): {len(listings)} elements")
                
                # Strategy 2: Look for article tags
                if not listings:
                    listings = await page.query_selector_all('article')
                    Actor.log.info(f"Strategy 2 (article): {len(listings)} elements")
                
                # Strategy 3: Look for divs with listing classes
                if not listings:
                    for selector in ['.listing-item', '.result-item', '[class*="listing"]', '[class*="result"]']:
                        listings = await page.query_selector_all(selector)
                        if listings:
                            Actor.log.info(f"Strategy 3 ({selector}): {len(listings)} elements")
                            break
                
                # Strategy 4: Find by heading pattern (h2, h3 with year)
                if not listings:
                    Actor.log.info("Trying headings strategy...")
                    headings = await page.query_selector_all('h2, h3')
                    containers = []
                    for heading in headings:
                        text = await heading.text_content()
                        if text and re.search(r'20\d{2}', text):  # Has a year
                            # Get parent container
                            container = await heading.evaluate_handle('el => el.closest("div, article, section")')
                            if container:
                                containers.append(container.as_element())
                    listings = containers
                    Actor.log.info(f"Strategy 4 (heading pattern): {len(listings)} elements")
                
                if not listings:
                    Actor.log.warning("No listings found with any strategy")
                    # Save screenshot and HTML for debugging
                    await page.screenshot(path='no_listings_debug.png')
                    html = await page.content()
                    with open('no_listings_debug.html', 'w') as f:
                        f.write(html)
                    Actor.log.info("Debug files saved")
                    break
                
                Actor.log.info(f"Found {len(listings)} listings on page {page_num}")
                
                for idx, listing in enumerate(listings):
                    if results_count >= max_results:
                        break
                    
                    try:
                        # Extract listing data with multiple fallback selectors
                        # Title - try multiple selectors
                        title = ''
                        for selector in ['h2', 'h3', 'h4', '.title', '[class*="title"]']:
                            title_elem = await listing.query_selector(selector)
                            if title_elem:
                                title = await title_elem.inner_text()
                                title = title.strip()
                                if title and len(title) > 5:
                                    break
                        
                        if not title:
                            Actor.log.warning(f"No title found for listing {idx}")
                            continue
                        
                        # Get URL - look for any link with /listing/ in href
                        link_elem = await listing.query_selector('a[href*="/listing/"]')
                        relative_url = await link_elem.get_attribute('href') if link_elem else ''
                        url = urljoin('https://www.tractorhouse.com', relative_url) if relative_url else ''
                        
                        # Price - look for USD $ pattern
                        price = ''
                        listing_text = await listing.inner_text()
                        price_match = re.search(r'USD \$[\d,]+', listing_text)
                        if price_match:
                            price = price_match.group(0)
                        else:
                            # Try other price patterns
                            price_match = re.search(r'\$[\d,]+', listing_text)
                            if price_match:
                                price = price_match.group(0)
                        
                        # Location - look for "Location:" pattern
                        location = ''
                        location_match = re.search(r'Location:\s*([^\n]+)', listing_text)
                        if location_match:
                            location = location_match.group(1).strip()
                        else:
                            # Try finding location elements
                            for selector in ['.location', '[class*="location"]', 'span:has-text("Location")']:
                                try:
                                    loc_elem = await listing.query_selector(selector)
                                    if loc_elem:
                                        location = await loc_elem.inner_text()
                                        location = location.replace('Location:', '').strip()
                                        if location:
                                            break
                                except:
                                    pass
                        
                        # Manufacturer & Model from title
                        mfr_model = title.split(' ', 1)
                        mfr = mfr_model[0] if len(mfr_model) > 0 else ''
                        model = mfr_model[1] if len(mfr_model) > 1 else ''
                        
                        # Parse year from title or text
                        year_match = re.search(r'\b(19|20)\d{2}\b', title)
                        year = year_match.group(0) if year_match else ''
                        
                        # Parse hours
                        hours_match = re.search(r'Hours:\s*([\d,]+)', listing_text)
                        hours = hours_match.group(1) if hours_match else ''
                        
                        # Parse horsepower
                        hp_match = re.search(r'(\d{1,4})\s*HP', listing_text, re.IGNORECASE)
                        horsepower = hp_match.group(1) if hp_match else ''
                        
                        # Condition
                        cond = 'Used'
                        if 'Condition: New' in listing_text or re.search(r'\bNew\b', title):
                            cond = 'New'
                        
                        # Seller
                        seller = ''
                        seller_match = re.search(r'Seller:\s*([^\n]+)', listing_text)
                        if seller_match:
                            seller = seller_match.group(1).strip()
                        
                        # Stock number
                        stock = ''
                        stock_match = re.search(r'Stock Number:\s*([^\n]+)', listing_text)
                        if stock_match:
                            stock = stock_match.group(1).strip()
                        
                        item = {
                            'title': title,
                            'url': url,
                            'price': price,
                            'manufacturer': mfr,
                            'model': model,
                            'year': year,
                            'hours': hours,
                            'horsepower': horsepower,
                            'condition': cond,
                            'location': location,
                            'seller': seller,
                            'stockNumber': stock,
                            'category': category,
                            'scrapedAt': datetime.now(timezone.utc).isoformat()
                        }
                        
                        Actor.log.info(f"Scraped: {title} - {price} - {location}")
                        await Actor.push_data(item)
                        results_count += 1
                        
                        if results_count % 10 == 0:
                            Actor.log.info(f"Scraped {results_count}/{max_results} listings")
                    
                    except Exception as e:
                        Actor.log.warning(f"Error extracting listing {idx}: {e}")
                        continue
                
                # Check for next page
                if results_count >= max_results:
                    break
                
                # If we got no results, don't continue
                if len(listings) == 0:
                    break
                
                page_num += 1
                await page.wait_for_timeout(2000)
        
        finally:
            await browser.close()
            await playwright.stop()
        
        Actor.log.info(f"Scraping completed. Total items: {results_count}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
