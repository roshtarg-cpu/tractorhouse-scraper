# TractorHouse Scraper - Working Selectors Quick Reference

## Listing Container Selectors (Priority Order)

1. `[data-listing-id]` - Data attribute (if exists)
2. `article` - Semantic HTML
3. `.listing-item` - Class name
4. `[class*="listing"]` - Partial class match
5. **Heading Pattern** (Most Reliable):
   - Find all `h2, h3` elements
   - Filter for text matching `/20\d{2}/` (year pattern)
   - Get parent container: `el.closest("div, article, section")`

## Field Extraction

### Title
```python
# Try in order:
selectors = ['h2', 'h3', 'h4', '.title', '[class*="title"]']
title = await listing.query_selector(selector).inner_text()
```

### URL
```python
link = await listing.query_selector('a[href*="/listing/"]')
url = urljoin('https://www.tractorhouse.com', await link.get_attribute('href'))
```

### Price (Regex Pattern)
```python
listing_text = await listing.inner_text()
price_match = re.search(r'USD \$[\d,]+', listing_text)
price = price_match.group(0) if price_match else ''
```

### Location (Regex Pattern)
```python
location_match = re.search(r'Location:\s*([^\n]+)', listing_text)
location = location_match.group(1).strip() if location_match else ''
```

### Hours (Regex Pattern)
```python
hours_match = re.search(r'Hours:\s*([\d,]+)', listing_text)
hours = hours_match.group(1) if hours_match else ''
```

### Horsepower (Regex Pattern)
```python
hp_match = re.search(r'(\d{1,4})\s*HP', listing_text, re.IGNORECASE)
horsepower = hp_match.group(1) if hp_match else ''
```

### Condition (Regex Pattern)
```python
cond = 'Used'
if 'Condition: New' in listing_text or re.search(r'\bNew\b', title):
    cond = 'New'
```

### Seller (Regex Pattern)
```python
seller_match = re.search(r'Seller:\s*([^\n]+)', listing_text)
seller = seller_match.group(1).strip() if seller_match else ''
```

### Stock Number (Regex Pattern)
```python
stock_match = re.search(r'Stock Number:\s*([^\n]+)', listing_text)
stock = stock_match.group(1).strip() if stock_match else ''
```

### Year (Regex from Title)
```python
year_match = re.search(r'\b(19|20)\d{2}\b', title)
year = year_match.group(0) if year_match else ''
```

### Manufacturer & Model (Split Title)
```python
mfr_model = title.split(' ', 1)
mfr = mfr_model[0] if len(mfr_model) > 0 else ''
model = mfr_model[1] if len(mfr_model) > 1 else ''
```

## Cloudflare Handling

```python
# 1. Use extended timeout
await page.goto(url, wait_until='domcontentloaded', timeout=90000)

# 2. Wait for JavaScript to render
await page.wait_for_timeout(10000)

# 3. Check for Cloudflare challenge
page_title = await page.title()
if "Just a moment" in page_title or "challenge" in page_title.lower():
    Actor.log.warning("Cloudflare challenge detected")
    await page.wait_for_timeout(15000)  # Additional wait
```

## Apify Proxy Configuration

```python
proxy_config = actor_input.get('proxyConfiguration', {'useApifyProxy': True})

if proxy_config.get('useApifyProxy'):
    proxy_url = Actor.create_proxy_url()
    parsed = urlparse(proxy_url)
    proxy_settings = {
        'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        'username': parsed.username,
        'password': parsed.password
    }
```

## Test URLs

- Tractors: `https://www.tractorhouse.com/listings/farm-equipment/for-sale/list/category/1092/tractors`
- Expected first listing (as of Sept 2026):
  - Title: "2023 CASE 586H"
  - Price: "USD $46,950"
  - Location: "Tampa, Florida"
  - URL: Contains `/listing/for-sale/257898199/`

## Debugging

If extraction fails:
1. Check logs for which selector strategy matched
2. Review saved files: `no_listings_debug.png` and `no_listings_debug.html`
3. Verify proxy is working: Look for "Using Apify proxy" in logs
4. Check Cloudflare bypass: Page title should NOT be "Just a moment"
