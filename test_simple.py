"""
Quick test to find the actual DOM selectors
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    
    print("Loading page...")
    await page.goto('https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/1092/tractors')
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(3000)
    
    # Find what contains "2023 CASE 586H"
    print("\nSearching for title element...")
    title_locator = page.locator('text=2023 CASE 586H').first
    
    # Get the parent container
    container = await title_locator.evaluate("""
        el => {
            // Walk up to find the listing container
            let current = el;
            while (current && current.tagName !== 'BODY') {
                const html = current.outerHTML.substring(0, 300);
                if (html.includes('USD $') && html.includes('Tampa')) {
                    return {
                        tag: current.tagName,
                        className: current.className,
                        id: current.id,
                        innerHTML: current.innerHTML.substring(0, 1000)
                    };
                }
                current = current.parentElement;
            }
            return null;
        }
    """)
    
    print("\nListing container found:")
    print(f"Tag: {container['tag']}")
    print(f"Class: {container['className']}")
    print(f"ID: {container['id']}")
    
    # Now find specific child elements
    results = await page.evaluate("""
        () => {
            // Find all h2 or h3 with year in them
            const allHeadings = Array.from(document.querySelectorAll('h2, h3'));
            const listingHeadings = allHeadings.filter(h => {
                const text = h.textContent;
                return /20\\d{2}/.test(text);  // Contains year
            });
            
            if (listingHeadings.length === 0) return {error: 'No headings found'};
            
            const firstHeading = listingHeadings[0];
            
            // Find container
            let container = firstHeading;
            while (container && container.tagName !== 'ARTICLE' && container.tagName !== 'BODY') {
                if (container.className && (
                    container.className.includes('listing') ||
                    container.className.includes('result') ||
                    container.className.includes('item')
                )) {
                    break;
                }
                container = container.parentElement;
            }
            
            // Get all similar containers
            const containerClass = container.className.split(' ')[0];
            const allContainers = Array.from(document.querySelectorAll(`.${containerClass}`));
            
            return {
                totalListings: listingHeadings.length,
                containerTag: container.tagName,
                containerClass: container.className,
                containerSelector: `.${containerClass}`,
                totalContainers: allContainers.length,
                
                // Analyze first listing
                firstListing: {
                    titleSelector: `${firstHeading.tagName}.${firstHeading.className.split(' ').join('.')}`,
                    titleText: firstHeading.textContent.trim(),
                    
                    // Find link
                    linkHref: firstHeading.querySelector('a')?.href || container.querySelector('a[href*="/listing/"]')?.href,
                    
                    // Find price
                    priceText: container.textContent.match(/USD \\$([\\d,]+)/)?.[0],
                    
                    // Find location
                    locationText: container.textContent.match(/Location:?\\s*([^\\n]+)/)?.[1],
                },
                
                sampleHTML: container.outerHTML.substring(0, 1500)
            };
        }
    """)
    
    print("\n" + "="*70)
    print("ANALYSIS RESULTS:")
    print("="*70)
    print(f"Total listing headings found: {results.get('totalListings', 0)}")
    print(f"Container tag: {results.get('containerTag', 'N/A')}")
    print(f"Container class: {results.get('containerClass', 'N/A')}")
    print(f"Container selector: {results.get('containerSelector', 'N/A')}")
    print(f"Total containers: {results.get('totalContainers', 0)}")
    
    if 'firstListing' in results:
        fl = results['firstListing']
        print(f"\nFirst listing analysis:")
        print(f"  Title selector: {fl.get('titleSelector', 'N/A')}")
        print(f"  Title text: {fl.get('titleText', 'N/A')}")
        print(f"  Link href: {fl.get('linkHref', 'N/A')}")
        print(f"  Price: {fl.get('priceText', 'N/A')}")
        print(f"  Location: {fl.get('locationText', 'N/A')}")
    
    if 'sampleHTML' in results:
        print(f"\nSample HTML (first 500 chars):")
        print(results['sampleHTML'][:500])
    
    # Save full HTML
    html = await page.content()
    with open('actual_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✓ Full HTML saved to actual_page.html")
    
    await page.screenshot(path='listing_page.png', full_page=True)
    print("✓ Screenshot saved to listing_page.png")
    
    input("\nPress Enter to close browser...")
    
    await browser.close()
    await playwright.stop()

asyncio.run(main())
