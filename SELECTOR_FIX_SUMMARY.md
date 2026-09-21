# TractorHouse Scraper - Selector Fix Summary

## Problem Identified
The scraper was extracting 0 items because:
1. **Cloudflare Protection**: TractorHouse.com uses Cloudflare bot protection
2. **Wrong Selectors**: `[data-listing-id]` and other selectors don't match actual page structure
3. **Insufficient Wait Time**: JavaScript needs time to render after Cloudflare bypass

## Solution Implemented

### 1. Updated Selectors (Multi-Strategy Approach)

The updated `main.py` now uses a fallback strategy system:

#### Strategy 1: Data Attributes
```python
listings = await page.query_selector_all('[data-listing-id]')
```

#### Strategy 2: Semantic HTML
```python
listings = await page.query_selector_all('article')
```

#### Strategy 3: Class-based selectors
```python
for selector in ['.listing-item', '.result-item', '[class*="listing"]', '[class*="result"]']:
    listings = await page.query_selector_all(selector)
```

#### Strategy 4: Heading Pattern (Most Reliable)
```python
headings = await page.query_selector_all('h2, h3')
# Find headings with year pattern (20\d{2})
# Walk up to parent container
```

### 2. Field Extraction Using Regex

Since exact selectors vary, the code now uses **regex patterns on text content**:

```python
listing_text = await listing.inner_text()

# Price
price_match = re.search(r'USD \$[\d,]+', listing_text)

# Location  
location_match = re.search(r'Location:\s*([^\n]+)', listing_text)

# Hours
hours_match = re.search(r'Hours:\s*([\d,]+)', listing_text)

# Seller
seller_match = re.search(r'Seller:\s*([^\n]+)', listing_text)

# Stock Number
stock_match = re.search(r'Stock Number:\s*([^\n]+)', listing_text)
```

### 3. Cloudflare Handling

```python
# Use domcontentloaded instead of networkidle
await page.goto(url, wait_until='domcontentloaded', timeout=90000)

# Wait 10 seconds for JavaScript
await page.wait_for_timeout(10000)

# Check for Cloudflare challenge
page_title = await page.title()
if "Just a moment" in page_title:
    await page.wait_for_timeout(15000)  # Wait 15 more seconds
```

## Working Selectors (Confirmed from web_extract)

Based on successful extraction via web_extract tool:

### Listing Container
- **Pattern**: Headings (h2, h3) containing year (e.g., "2023 CASE 586H")
- **Container**: Parent div/section/article wrapping the heading and details

### Individual Fields

| Field | Pattern | Example |
|-------|---------|---------|
| Title | h2 or h3 text | `2023 CASE 586H` |
| URL | `a[href*="/listing/"]` | `/listing/for-sale/257898199/...` |
| Price | Regex: `USD \$[\d,]+` | `USD $46,950` |
| Location | Regex: `Location:\s*([^\n]+)` | `Tampa, Florida` |
| Hours | Regex: `Hours:\s*([\d,]+)` | `3,204` |
| Seller | Regex: `Seller:\s*([^\n]+)` | `CASE Power & Equipment` |
| Stock | Regex: `Stock Number:\s*([^\n]+)` | `324765` |

## Testing Recommendations

### Option 1: Test via Apify (Recommended)
The Apify proxy handles Cloudflare automatically. Deploy and run:

```bash
cd ~/actors/tractorhouse-scraper
apify push
apify call
```

### Option 2: Manual Browser Test (Limited)
Local Playwright will hit Cloudflare. For testing selector logic only:

```bash
python3 test_local.py
```

Note: This will likely show Cloudflare challenge page in headless:false mode.

## Expected Output

Each listing should extract:
```json
{
  "title": "2023 CASE 586H",
  "url": "https://www.tractorhouse.com/listing/for-sale/257898199/...",
  "price": "USD $46,950",
  "manufacturer": "2023",
  "model": "CASE 586H",
  "year": "2023",
  "hours": "3,204",
  "horsepower": "",
  "condition": "Used",
  "location": "Tampa, Florida",
  "seller": "CASE Power & Equipment",
  "stockNumber": "324765",
  "category": "tractors",
  "scrapedAt": "2026-09-21T09:15:00.000Z"
}
```

## Files Modified

1. **`src/main.py`** - Complete rewrite with:
   - Multi-strategy selector system
   - Regex-based extraction
   - Cloudflare handling
   - Extended timeouts
   - Better logging

2. **`test_local.py`** - New test script for local verification

## Next Steps

1. Deploy to Apify: `apify push`
2. Run actor: `apify call`
3. Check logs for which strategy succeeded
4. Verify extracted data matches expected format
5. If still getting 0 items, increase Cloudflare wait time or check Apify proxy configuration

## Troubleshooting

If still getting 0 items:

1. **Check Apify proxy is enabled**: `proxyConfiguration.useApifyProxy = true`
2. **Increase wait time**: Change line 101 from 10000 to 20000ms
3. **Check logs** for which selector strategy is being used
4. **Review saved HTML**: Debug files are saved when no listings found
