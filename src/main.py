"""
TractorHouse.com Farm Equipment Scraper
Scrapes farm equipment listings with detailed specs and pricing
"""
from apify import Actor, Request
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

async def main():
    async with Actor:
        Actor.log.info("TractorHouse Scraper starting...")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        search_mode = actor_input.get('searchMode', 'filters')
        start_url = actor_input.get('startUrl', '')
        category = actor_input.get('category', 'tractors')
        manufacturer = actor_input.get('manufacturer', '')
        condition = actor_input.get('condition', 'all')
        year_min = actor_input.get('yearMin')
        year_max = actor_input.get('yearMax')
        price_min = actor_input.get('priceMin')
        price_max = actor_input.get('priceMax')
        location = actor_input.get('location', '')
        zip_code = actor_input.get('zipCode', '')
        search_radius = actor_input.get('searchRadius', 100)
        hp_min = actor_input.get('horsepowerMin')
        hp_max = actor_input.get('horsepowerMax')
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
            proxy_url = Actor.create_proxy_url()
            parsed = urlparse(proxy_url)
            proxy_settings = {
                'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                'username': parsed.username,
                'password': parsed.password
            }
        
        browser = await playwright.chromium.launch(
            headless=True,
            proxy=proxy_settings
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        results_count = 0
        page_num = 1
        
        try:
            while results_count < max_results:
                # Build paginated URL
                current_url = f"{search_url}?p={page_num}"
                Actor.log.info(f"Scraping page {page_num}: {current_url}")
                
                await page.goto(current_url, wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Extract listings
                listings = await page.query_selector_all('[data-listing-id]')
                
                if not listings:
                    Actor.log.info("No more listings found")
                    break
                
                Actor.log.info(f"Found {len(listings)} listings on page {page_num}")
                
                for listing in listings:
                    if results_count >= max_results:
                        break
                    
                    try:
                        # Extract listing data
                        title_elem = await listing.query_selector('h3.listing-title, h2.listing-title, .title a')
                        title = await title_elem.inner_text() if title_elem else 'N/A'
                        title = title.strip()
                        
                        # Get URL
                        link_elem = await listing.query_selector('a[href*="/listings/"]')
                        relative_url = await link_elem.get_attribute('href') if link_elem else ''
                        url = urljoin('https://www.tractorhouse.com', relative_url) if relative_url else ''
                        
                        # Price
                        price_elem = await listing.query_selector('.price, [class*="price"], .listing-price')
                        price_text = await price_elem.inner_text() if price_elem else ''
                        price = price_text.strip()
                        
                        # Location
                        location_elem = await listing.query_selector('.location, [class*="location"]')
                        location_text = await location_elem.inner_text() if location_elem else ''
                        location = location_text.strip()
                        
                        # Manufacturer & Model
                        mfr_model = title.split(' ', 1)
                        mfr = mfr_model[0] if len(mfr_model) > 0 else ''
                        model = mfr_model[1] if len(mfr_model) > 1 else ''
                        
                        # Additional details (year, hours, etc.)
                        details_elem = await listing.query_selector('.listing-details, .specs, [class*="detail"]')
                        details_text = await details_elem.inner_text() if details_elem else ''
                        
                        # Parse year
                        year_match = re.search(r'\b(19|20)\d{2}\b', details_text)
                        year = year_match.group(0) if year_match else ''
                        
                        # Parse hours
                        hours_match = re.search(r'(\d{1,6})\s*(hrs?|hours)', details_text, re.IGNORECASE)
                        hours = hours_match.group(1) if hours_match else ''
                        
                        # Parse horsepower
                        hp_match = re.search(r'(\d{1,4})\s*HP', details_text, re.IGNORECASE)
                        horsepower = hp_match.group(1) if hp_match else ''
                        
                        # Condition
                        cond = 'Used'
                        if 'new' in title.lower() or 'new' in details_text.lower():
                            cond = 'New'
                        
                        # Seller
                        seller_elem = await listing.query_selector('.dealer-name, .seller-name, [class*="seller"]')
                        seller = await seller_elem.inner_text() if seller_elem else ''
                        seller = seller.strip()
                        
                        # Stock number
                        stock_elem = await listing.query_selector('.stock-number, [class*="stock"]')
                        stock = await stock_elem.inner_text() if stock_elem else ''
                        stock = stock.strip()
                        
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
                            'scrapedAt': Actor.now().isoformat()
                        }
                        
                        await Actor.push_data(item)
                        results_count += 1
                        
                        if results_count % 10 == 0:
                            Actor.log.info(f"Scraped {results_count}/{max_results} listings")
                    
                    except Exception as e:
                        Actor.log.warning(f"Error extracting listing: {e}")
                        continue
                
                # Check for next page
                if results_count >= max_results:
                    break
                
                page_num += 1
                await page.wait_for_timeout(1500)
        
        finally:
            await browser.close()
            await playwright.stop()
        
        Actor.log.info(f"Scraping completed. Total items: {results_count}")
