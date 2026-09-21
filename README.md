# TractorHouse Scraper — Farm Equipment Listings & Prices

Extract farm equipment listings from TractorHouse.com, North America's largest online marketplace for new and used tractors, combines, planters, sprayers, and agricultural machinery.

## What does TractorHouse Scraper do?

This actor scrapes equipment listings from TractorHouse.com with detailed specifications, pricing, and seller information. Search by category, manufacturer, year range, location, horsepower, and price filters.

**Input:** Category, filters (manufacturer, year, price, location, horsepower), or direct search URL  
**Output:** Structured farm equipment data (title, price, specs, location, seller, URL)

## Why scrape TractorHouse?

- **Market Intelligence:** Track farm equipment prices, inventory trends, and seller competition
- **Fleet Management:** Monitor available equipment for farm expansion or fleet upgrades
- **Dealer Analysis:** Research competitor pricing and inventory for dealerships
- **Equipment Valuation:** Compare similar equipment for accurate appraisals
- **Lead Generation:** Identify equipment sellers for B2B outreach

## Features

✅ **Category Search** — Browse tractors, combines, planters, sprayers, tillage, hay equipment  
✅ **Advanced Filters** — Manufacturer, year range, price, location, horsepower, condition  
✅ **Detailed Data** — Title, price, manufacturer, model, year, hours, HP, condition, seller  
✅ **Geo Search** — Filter by state/province or search radius from zip code  
✅ **Pagination** — Scrape 1-10,000+ listings across multiple pages  
✅ **Proxy Support** — Residential proxies for reliable access

## Input Schema

```json
{
  "searchMode": "filters",
  "category": "tractors",
  "manufacturer": "John Deere",
  "condition": "used",
  "yearMin": 2015,
  "yearMax": 2024,
  "priceMin": 50000,
  "priceMax": 200000,
  "location": "Iowa",
  "horsepowerMin": 150,
  "horsepowerMax": 300,
  "maxResults": 100
}
```

### Input Parameters

- **searchMode** — `url` (direct TractorHouse URL) or `filters` (category/filter search)
- **startUrl** — Direct TractorHouse search or category URL
- **category** — Equipment type: `tractors`, `combines`, `planters`, `sprayers`, `tillage`, `hay-forage`, etc.
- **manufacturer** — Brand filter (e.g., John Deere, Case IH, New Holland, Kubota)
- **condition** — `all`, `new`, or `used`
- **yearMin/yearMax** — Manufacturing year range (1950-2027)
- **priceMin/priceMax** — Price range in USD
- **location** — State or province filter (e.g., Iowa, Nebraska, Ontario)
- **zipCode** — Center point for radius search
- **searchRadius** — Search radius in miles (10-1000)
- **horsepowerMin/horsepowerMax** — Horsepower range for tractors/powered equipment
- **maxResults** — Maximum listings to scrape (1-10,000)
- **proxyConfiguration** — Apify proxy settings (residential recommended)

## Output Example

```json
{
  "title": "2018 John Deere 8370R",
  "url": "https://www.tractorhouse.com/listings/...",
  "price": "$285,000",
  "manufacturer": "John Deere",
  "model": "8370R",
  "year": "2018",
  "hours": "1245",
  "horsepower": "370",
  "condition": "Used",
  "location": "Des Moines, Iowa",
  "seller": "Heartland Equipment",
  "stockNumber": "TH-38472",
  "category": "tractors",
  "scrapedAt": "2026-09-21T14:30:00.000Z"
}
```

## Use Cases

**Agricultural Operations:**  
Monitor available equipment for farm expansion, compare pricing for fleet upgrades

**Equipment Dealers:**  
Track competitor inventory, analyze pricing trends, identify underpriced acquisition opportunities

**Market Research:**  
Study equipment depreciation rates, regional price variations, seasonal inventory patterns

**Appraisal Services:**  
Build comparable sales databases for accurate equipment valuations

**Lead Generation:**  
Identify sellers of specific equipment models for targeted outreach

## Setup & Usage

1. **Configure Input** — Select category, set filters, or provide direct URL
2. **Set Filters** — Manufacturer, year, price, location, horsepower
3. **Choose Max Results** — 1-10,000 listings
4. **Enable Proxies** — Residential proxies recommended
5. **Run Actor** — Data exports to JSON, CSV, Excel

## Data Fields

| Field | Type | Description |
|-------|------|-------------|
| title | string | Full equipment listing title |
| url | string | Direct link to listing |
| price | string | Listed price (USD) |
| manufacturer | string | Equipment brand/manufacturer |
| model | string | Model designation |
| year | string | Manufacturing year |
| hours | string | Engine/usage hours |
| horsepower | string | Engine horsepower |
| condition | string | New or Used |
| location | string | Equipment location (city, state) |
| seller | string | Dealership or seller name |
| stockNumber | string | Stock/inventory number |
| category | string | Equipment category |
| scrapedAt | datetime | Extraction timestamp (ISO 8601) |

## Categories Supported

- **Tractors** — All sizes and configurations
- **Combines** — Grain harvesters and headers
- **Planters & Seeders** — Planting equipment
- **Sprayers** — Self-propelled and pull-type
- **Tillage** — Plows, discs, cultivators, field cultivators
- **Hay & Forage** — Balers, mowers, tedders, rakes
- **Harvesting** — Cotton pickers, corn heads, platforms
- **Loaders & Attachments** — Front-end loaders, buckets, forks
- **Skid Steers** — Compact utility loaders
- **Utility Vehicles** — ATVs, UTVs, farm vehicles
- **Trailers** — Equipment and livestock trailers

## Integration

**Apify API:** Real-time access via GET/POST  
**Webhooks:** Trigger workflows on completion  
**Schedules:** Daily/weekly inventory monitoring  
**Zapier/Make:** Connect to 5,000+ apps

## Cost Efficiency

- **$0.50-$2 per 1,000 listings** (typical)
- Residential proxies recommended for scale
- 1024 MB memory sufficient for most runs

## Support & Resources

📖 [Full Documentation](https://apify.com/fervent_bus/tractorhouse-scraper)  
💬 [Discord Community](https://discord.gg/jyEM2PRvMU)  
📧 Email: support@apify.com

---

**MCP & AI Agent Compatible**  
This actor follows Apify MCP conventions for seamless integration with Claude, ChatGPT, and autonomous AI agents.

Compatible with Claude, ChatGPT & AI agents via Apify MCP.
