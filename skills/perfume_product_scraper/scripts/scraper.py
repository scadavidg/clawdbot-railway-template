#!/usr/bin/env python3
"""
Perfume product scraper: fetches product pages, extracts data, normalizes to Medusa Product schema.
Supports multiple URLs and modular site-specific extractors.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

# Ensure script dir is on path for extractors package
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from extractors import get_extractor
from extractors.base import RawProduct

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]


def _id_from_url(url: str, prefix: str = "prod") -> str:
    h = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"{prefix}_{h}"


def _slug(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"[-\s]+", "-", t)
    return t.strip("-") or "product"


def _clean_html(html: str | None) -> str:
    if not html:
        return ""
    if not BeautifulSoup:
        return re.sub(r"<[^>]+>", "", html)
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=" ", strip=True)


def _resolve_url(base: str, href: str | None) -> str | None:
    if not href or not href.strip():
        return None
    href = href.strip()
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(base, href)


def fetch_html(url: str, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 30) -> str:
    """Fetch HTML with retries and realistic User-Agent."""
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            if httpx:
                r = httpx.get(
                    url,
                    headers={"User-Agent": user_agent},
                    timeout=timeout,
                    follow_redirects=True,
                )
                r.raise_for_status()
                return r.text
            else:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": user_agent})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read().decode(errors="replace")
        except Exception as e:
            last_err = e
            if i < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_BACKOFF[i])
    raise last_err or RuntimeError("fetch failed")


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def normalize(raw: RawProduct) -> dict[str, Any]:
    """Convert RawProduct to Medusa-compatible product object."""
    base_url = raw.url
    pid = _id_from_url(base_url, "prod")
    title = (raw.title or "Untitled Product").strip()
    handle = _slug(title) or _id_from_url(base_url, "handle")[7:]

    # Images: dedupe, absolute URLs, rank
    seen = set()
    images = []
    for i, u in enumerate(raw.image_urls):
        full = _resolve_url(base_url, u)
        if not full or full in seen:
            continue
        seen.add(full)
        images.append({
            "id": f"img_{pid}_{i}",
            "url": full,
            "rank": len(images),
        })
    thumbnail = images[0]["url"] if images else None

    # Options from variants (Size)
    size_values = []
    for v in raw.variants:
        s = (v.get("size") or "").strip()
        if s and s not in size_values:
            size_values.append(s)
    if not size_values:
        size_values = [""]
    opt_id = f"opt_{pid}"
    options = [{
        "id": opt_id,
        "title": "Size",
        "values": [{"value": v} for v in size_values if v],
    }]
    if not options[0]["values"]:
        options = []

    # Variants
    variants = []
    for i, v in enumerate(raw.variants):
        size = (v.get("size") or "").strip() or "default"
        var_id = f"var_{pid}_{i}"
        title_v = v.get("title") or (f"{title} {size}" if size != "default" else title)
        sku = _slug(title)[:20] + "-" + _slug(size)[:10] if size != "default" else _slug(title)[:30]
        sku = sku or f"sku_{pid}_{i}"
        variants.append({
            "id": var_id,
            "title": title_v,
            "sku": sku,
            "barcode": v.get("barcode"),
            "ean": v.get("ean"),
            "upc": v.get("upc"),
            "weight": raw.weight or v.get("weight"),
            "length": raw.length or v.get("length"),
            "width": raw.width or v.get("width"),
            "height": raw.height or v.get("height"),
            "inventory_quantity": v.get("inventory_quantity", 0),
            "allow_backorder": False,
            "manage_inventory": True,
            "variant_rank": i,
            "thumbnail": v.get("thumbnail"),
            "metadata": v.get("metadata") or {},
        })

    # Metadata: merge perfume-specific
    meta = dict(raw.metadata or {})
    if raw.origin_country:
        meta.setdefault("origin_country", raw.origin_country)
    if raw.material:
        meta.setdefault("material", raw.material)

    product = {
        "id": pid,
        "title": title,
        "subtitle": raw.subtitle or None,
        "description": _clean_html(raw.description) or None,
        "handle": handle,
        "status": "published",
        "thumbnail": thumbnail,
        "images": images,
        "options": options,
        "variants": variants,
        "weight": raw.weight,
        "width": raw.width,
        "height": raw.height,
        "length": raw.length,
        "origin_country": raw.origin_country,
        "material": raw.material,
        "metadata": meta,
        "created_at": None,
        "updated_at": None,
        "tags": [{"id": f"tag_{hashlib.sha256(t.encode()).hexdigest()[:8]}", "value": t} for t in (raw.tags or [])],
        "categories": [{"id": f"cat_{hashlib.sha256(c.encode()).hexdigest()[:8]}", "name": c, "handle": _slug(c)} for c in (raw.categories or [])],
    }
    return product


def scrape_url(url: str, use_browser: bool = False) -> dict[str, Any]:
    """Fetch one URL, extract, normalize; return single product dict."""
    if use_browser:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(extra_http_headers={"User-Agent": DEFAULT_USER_AGENT})
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                html = page.content()
                browser.close()
        except ImportError:
            html = fetch_html(url)
    else:
        html = fetch_html(url)

    if not BeautifulSoup:
        raise RuntimeError("BeautifulSoup4 is required. Install: pip install beautifulsoup4 lxml")
    soup = BeautifulSoup(html, "lxml")
    extract = get_extractor(_domain(url))
    raw = extract(soup, url)
    return normalize(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape perfume product pages to Medusa JSON")
    parser.add_argument("--urls", nargs="*", help="Product URLs")
    parser.add_argument("--url-file", "-f", help="File with one URL per line")
    parser.add_argument("--output", "-o", default="-", help="Output JSON file (default: stdout)")
    parser.add_argument("--browser", action="store_true", help="Use headless browser (Playwright)")
    parser.add_argument("--validate", action="store_true", help="Validate required fields")
    args = parser.parse_args()

    urls = list(args.urls or [])
    if args.url_file:
        try:
            with open(args.url_file, encoding="utf-8") as f:
                urls.extend(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print(f"Error: URL file not found: {args.url_file}", file=sys.stderr)
            return 1

    if not urls:
        print("Error: No URLs provided (--urls or --url-file)", file=sys.stderr)
        return 1

    products = []
    for url in urls:
        try:
            products.append(scrape_url(url, use_browser=args.browser))
        except Exception as e:
            print(f"Error scraping {url}: {e}", file=sys.stderr)
            if len(urls) == 1:
                return 1

    out = {"products": products}

    if args.validate:
        required = {"id", "title", "handle"}
        for p in products:
            missing = required - set(p.keys())
            if missing:
                print(f"Validation warning: product {p.get('id')} missing {missing}", file=sys.stderr)

    if args.output == "-":
        json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
