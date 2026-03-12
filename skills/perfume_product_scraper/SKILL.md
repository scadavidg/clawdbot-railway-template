---
name: perfume-product-scraper
description: Scrapes perfume product pages from URLs and converts extracted data into JSON compatible with the Medusa Store API Product schema. Use when scraping perfume e-commerce product pages, importing perfume catalogs, or building product feeds for Medusa stores.
---

# Perfume Product Scraper

## When to Use

Apply this skill when:
- Scraping one or more perfume product URLs into structured product data
- Importing perfume catalogs into a Medusa store
- Building product feeds from perfume e-commerce sites
- User requests "scrape perfume products", "extract product from URL", or similar

## Quick Start

1. **Input**: A list of product URLs (perfume product pages).
2. **Process**: For each URL, fetch HTML, parse, extract, normalize, then map to Medusa schema.
3. **Output**: `{ "products": [ ... ] }` — array of product objects compatible with Medusa.

Use the provided script when possible. From the skill root (`{baseDir}`):

```bash
python scripts/scraper.py --urls "https://example.com/perfume1" "https://example.com/perfume2" --output products.json
```

For a new perfume website, add a site-specific extractor in `scripts/extractors/` and register it (see Modular extractors below).

## Workflow

1. **Fetch**
   - Prefer fast HTML fetching (e.g. `httpx`/`requests`) first.
   - If the page requires JavaScript (SPA, dynamic content), use a headless browser (e.g. Playwright).
   - Use retry logic (e.g. 3 attempts, exponential backoff).
   - Use a realistic User-Agent (e.g. Chrome on Windows).

2. **Parse**
   - Parse DOM with a fast parser (e.g. `beautifulsoup4`, `lxml`).
   - If using a headless browser, get `page.content()` and parse that HTML.

3. **Extract**
   - Use a site-specific extractor when available; otherwise use generic selectors (e.g. `h1`, `meta`, `[itemprop]`, Open Graph, JSON-LD).
   - Extract: title, description, images, variants (sizes), price, and any perfume-specific metadata (brand, concentration, notes, gender).

4. **Normalize**
   - Strip HTML from descriptions.
   - Resolve relative URLs to absolute (base URL = product page URL).
   - Deduplicate images by URL; assign `rank` by order of appearance.
   - Generate deterministic IDs (e.g. hash of URL) when missing.
   - Generate `handle` from title (slug: lowercase, hyphens, no special chars).
   - Defaults: `status`: `"published"`, `inventory_quantity`: `0`, `allow_backorder`: `false`, `manage_inventory`: `true`.

5. **Map to Medusa**
   - Build one product object per URL following the schema in [reference.md](reference.md).
   - Ensure `images[]` has `id`, `url`, `rank`.
   - Build `options[]` (e.g. "Size" → 30ml, 50ml, 100ml) and `variants[]` with option linkage.
   - Put perfume-specific fields (brand, concentration, notes, etc.) under `metadata`.

## Output Shape

Return a single object:

```json
{
  "products": [
    {
      "id": "prod_...",
      "title": "...",
      "handle": "...",
      "status": "published",
      "description": "...",
      "thumbnail": "https://...",
      "images": [{ "id": "...", "url": "https://...", "rank": 0 }],
      "options": [{ "id": "...", "title": "Size", "values": [{ "value": "50ml" }] }],
      "variants": [{ "id": "...", "title": "Eau de Parfum 50ml", "sku": "...", ... }],
      "metadata": { "brand": "...", "concentration": "EDP", ... }
    }
  ]
}
```

Full field list, types, and perfume metadata conventions: [reference.md](reference.md).

## Robustness

- **Missing fields**: Omit or use schema defaults; never leave required Medusa fields as `undefined` if they are required (e.g. `id`, `title`, `handle`). Generate `id`/`handle`/`sku` when missing.
- **Different HTML structures**: Prefer site extractors; in generic mode try multiple strategies (JSON-LD, Open Graph, meta tags, common class names).
- **Multiple images**: Collect all product images, deduplicate by URL, sort by DOM order, assign `rank` 0, 1, 2, ...
- **Variants (sizes)**: Detect size options (30ml, 50ml, 100ml, etc.) and create one variant per size; set `variant_rank` by order.

## Modular Extractors

To support a new perfume site:

1. Add `scripts/extractors/<site_slug>.py` with a function that accepts `(soup, url: str) -> RawProduct` (or the current raw-dict shape).
2. Register the extractor in `extractors/__init__.py` (REGISTRY by domain).
3. The main script uses the registered extractor for that domain; others fall back to the generic extractor.

This keeps the skill reusable across multiple perfume websites.

## Implementation Notes

- **Headless browser**: Use when the product content is loaded by JS (e.g. React/Vue storefronts). Otherwise use HTTP + HTML parsing for speed.
- **Retries**: e.g. 3 attempts, 1s / 2s / 4s backoff; respect `Retry-After` if present.
- **User-Agent**: e.g. `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`.
- **Pagination**: If the input is a listing page (many products), detect pagination, collect product URLs from the listing, then scrape each product URL through this workflow; return one product per product page.

## Example Usage

**Single URL:**

```bash
python scripts/scraper.py --urls "https://example.com/perfume/dior-sauvage" -o out.json
```

**Multiple URLs:**

```bash
python scripts/scraper.py --urls "https://a.com/p1" "https://a.com/p2" -o products.json
```

**From file:**

```bash
python scripts/scraper.py --url-file urls.txt -o products.json
```

Output: JSON file with `{ "products": [ ... ] }` and, if run with `--validate`, a quick check that each product has required fields.

## Deploy on Railway (OpenClaw)

This skill is loaded by OpenClaw when it lives under the workspace **skills** folder. To use it with your clawbot on Railway:

1. Ensure this repo (with the `skills/` folder at the root) is what Railway uses as the workspace, **or**
2. Copy the folder `skills/perfume_product_scraper` into your OpenClaw workspace on the server (e.g. into `/data/workspace/skills/` if `OPENCLAW_WORKSPACE_DIR=/data/workspace`).

After the next session (or restart), OpenClaw will see the skill. If the agent runs the scraper script, install dependencies in the environment (e.g. `pip install -r skills/perfume_product_scraper/scripts/requirements.txt` or add them to the container/sandbox).

See [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) for step-by-step.

## Additional Resources

- Full Medusa product/variant/options schema and perfume metadata: [reference.md](reference.md).
