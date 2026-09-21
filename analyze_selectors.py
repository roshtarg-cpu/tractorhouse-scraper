"""
Automated test to find DOM selectors (headless version)
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    
    page = await context.new_page()
    
    print("Loading page...")
    await page.goto('https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/1092/tractors', 
                     wait_until='domcontentloaded', timeout=60000)
    print("Waiting for content to load...")
    await page.wait_for_timeout(8000)  # Give JavaScript time to render
    
    # Analyze DOM structure
    results = await page.evaluate("""
        () => {
            // Strategy 1: Find by heading pattern
            const allHeadings = Array.from(document.querySelectorAll('h1, h2, h3, h4'));
            const listingHeadings = allHeadings.filter(h => {
                const text = h.textContent.trim();
                return /20\\d{2}/.test(text) && text.length < 100;
            });
            
            if (listingHeadings.length === 0) {
                return {error: 'No headings with years found', totalHeadings: allHeadings.length};
            }
            
            const firstHeading = listingHeadings[0];
            
            // Walk up to find the listing container
            let container = firstHeading;
            let depth = 0;
            while (container && container.tagName !== 'BODY' && depth < 10) {
                const text = container.textContent;
                const hasPrice = /USD \\$|\\$[\\d,]+/.test(text);
                const hasLocation = /location/i.test(text);
                
                if (hasPrice && hasLocation && text.length < 5000) {
                    break;
                }
                container = container.parentElement;
                depth++;
            }
            
            // Extract container info
            const containerTag = container.tagName.toLowerCase();
            const containerClasses = container.className;
            const containerId = container.id;
            
            // Find all similar containers
            let allContainers = [];
            if (containerClasses) {
                const mainClass = containerClasses.split(' ').filter(c => c.length > 0)[0];
                if (mainClass) {
                    allContainers = Array.from(document.querySelectorAll(`.${mainClass}`));
                }
            }
            
            // If no class, try by tag
            if (allContainers.length === 0) {
                allContainers = Array.from(document.querySelectorAll(containerTag));
            }
            
            // Analyze first container's structure
            const firstLink = container.querySelector('a[href*="/listing/"]');
            const priceElem = Array.from(container.querySelectorAll('*')).find(el => 
                /^USD \\$[\\d,]+$/.test(el.textContent.trim())
            );
            const locationElem = Array.from(container.querySelectorAll('*')).find(el => 
                el.textContent.includes('Location:')
            );
            
            return {
                success: true,
                totalListingHeadings: listingHeadings.length,
                totalContainers: allContainers.length,
                
                container: {
                    tag: containerTag,
                    classes: containerClasses,
                    id: containerId,
                    selector: containerId ? `#${containerId}` : 
                             containerClasses ? `.${containerClasses.split(' ')[0]}` : 
                             containerTag,
                },
                
                elements: {
                    heading: {
                        tag: firstHeading.tagName.toLowerCase(),
                        classes: firstHeading.className,
                        text: firstHeading.textContent.trim(),
                        selector: `${firstHeading.tagName.toLowerCase()}${firstHeading.className ? '.' + firstHeading.className.split(' ').join('.') : ''}`,
                    },
                    link: {
                        href: firstLink?.href,
                        selector: firstLink ? `a[href*="/listing/"]` : 'NOT FOUND',
                    },
                    price: {
                        text: priceElem?.textContent.trim(),
                        tag: priceElem?.tagName.toLowerCase(),
                        classes: priceElem?.className,
                    },
                    location: {
                        text: locationElem?.textContent.trim(),
                        tag: locationElem?.tagName.toLowerCase(),
                        classes: locationElem?.className,
                    },
                },
                
                sampleHTML: container.outerHTML.substring(0, 2000),
            };
        }
    """)
    
    print("\n" + "="*70)
    print("SELECTOR ANALYSIS:")
    print("="*70)
    print(json.dumps(results, indent=2))
    
    # Save detailed results
    with open('selector_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save HTML
    html = await page.content()
    with open('page_full.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    await browser.close()
    await playwright.stop()
    
    # Return recommendations
    if 'success' in results and results['success']:
        print("\n" + "="*70)
        print("RECOMMENDED SELECTORS:")
        print("="*70)
        print(f"Listing container: {results['container']['selector']}")
        print(f"Title: {results['elements']['heading']['selector']}")
        print(f"Link: {results['elements']['link']['selector']}")
        print(f"Price element tag: {results['elements']['price']['tag']}")
        print(f"Location element tag: {results['elements']['location']['tag']}")

if __name__ == "__main__":
    asyncio.run(main())
