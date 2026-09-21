"""
Test script to identify correct selectors for TractorHouse listings
Based on the extracted markdown content structure
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_selectors():
    url = "https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/1092/tractors"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    
    page = await context.new_page()
    
    print(f"Navigating to: {url}")
    await page.goto(url, wait_until='networkidle', timeout=60000)
    
    # Wait extra time for dynamic content
    print("Waiting for page to fully load...")
    await page.wait_for_timeout(5000)
    
    # Try different selector strategies
    selectors_to_test = [
        'article',
        '[class*="listing"]',
        '[class*="result"]',
        '[data-listing-id]',
        '.listing-container',
        '.search-result',
        'div[class*="premium"]',
        'section[class*="listing"]',
    ]
    
    print("\n=== Testing listing container selectors ===")
    for selector in selectors_to_test:
        try:
            elements = await page.query_selector_all(selector)
            print(f"{selector}: {len(elements)} elements")
            if len(elements) > 0 and len(elements) < 100:
                # Get class names of first element
                first_elem = elements[0]
                classes = await first_elem.get_attribute('class')
                tag = await first_elem.evaluate('el => el.tagName')
                print(f"  -> First element: <{tag}> class='{classes}'")
        except Exception as e:
            print(f"{selector}: Error - {e}")
    
    # Get page HTML snippet to analyze
    print("\n=== Getting page HTML structure ===")
    html_snippet = await page.evaluate("""
        () => {
            // Find elements that might be listings
            const body = document.body.innerHTML;
            const div = document.createElement('div');
            div.innerHTML = body;
            
            // Look for heading with price pattern
            const headings = document.querySelectorAll('h2, h3');
            const results = [];
            
            for (let h of headings) {
                const text = h.textContent.trim();
                if (text.match(/20\\d{2}/)) {  // Year pattern
                    const parent = h.closest('div') || h.parentElement;
                    if (parent) {
                        results.push({
                            tag: parent.tagName,
                            classes: parent.className,
                            id: parent.id,
                            html: parent.outerHTML.substring(0, 500)
                        });
                        if (results.length >= 3) break;
                    }
                }
            }
            return results;
        }
    """)
    
    print("Found listing-like elements:")
    for i, elem in enumerate(html_snippet):
        print(f"\n--- Element {i+1} ---")
        print(f"Tag: {elem['tag']}")
        print(f"Classes: {elem['classes']}")
        print(f"ID: {elem['id']}")
        print(f"HTML preview: {elem['html'][:200]}...")
    
    # Save full page HTML for analysis
    full_html = await page.content()
    with open('full_page.html', 'w', encoding='utf-8') as f:
        f.write(full_html)
    print("\n✓ Full page HTML saved to full_page.html")
    
    # Take screenshot
    await page.screenshot(path='page_screenshot.png')
    print("✓ Screenshot saved to page_screenshot.png")
    
    # Try to find price elements
    print("\n=== Testing price selectors ===")
    price_selectors = [
        'text=/USD \\$/',
        '[class*="price"]',
        'text=/\\$\\d+/',
    ]
    
    for selector in price_selectors:
        try:
            if selector.startswith('text='):
                elements = await page.locator(selector).all()
            else:
                elements = await page.query_selector_all(selector)
            print(f"{selector}: {len(elements)} elements")
        except Exception as e:
            print(f"{selector}: Error - {e}")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_selectors())
