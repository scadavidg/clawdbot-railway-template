"""Generic extractor: JSON-LD, Open Graph, h1, and common image/variant patterns."""

import json
import re
from typing import Any
from urllib.parse import urljoin

from .base import RawProduct


def extract(soup: Any, url: str) -> RawProduct:
    """Extract product data using generic heuristics."""
    raw = RawProduct(url=url)

    # JSON-LD Product
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = script.string and script.string.strip()
            if not data:
                continue
            data = json.loads(data)
            if isinstance(data, dict):
                data = [data]
            for item in data if isinstance(data, list) else [data]:
                if item.get("@type") in ("Product", "http://schema.org/Product"):
                    raw.title = raw.title or item.get("name")
                    raw.description = raw.description or item.get("description")
                    if isinstance(raw.description, list):
                        raw.description = " ".join(raw.description)
                    img = item.get("image")
                    if isinstance(img, str):
                        raw.image_urls.append(urljoin(url, img))
                    elif isinstance(img, list):
                        for u in img:
                            if isinstance(u, str):
                                raw.image_urls.append(urljoin(url, u))
                            elif isinstance(u, dict) and u.get("url"):
                                raw.image_urls.append(urljoin(url, u["url"]))
                    # Brand
                    brand = item.get("brand")
                    if isinstance(brand, dict) and brand.get("name"):
                        raw.metadata["brand"] = brand["name"]
                    elif isinstance(brand, str):
                        raw.metadata["brand"] = brand
                    break
        except (json.JSONDecodeError, TypeError):
            continue

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        raw.title = raw.title or og_title["content"]
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        raw.description = raw.description or og_desc["content"]
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        u = urljoin(url, og_image["content"])
        if u not in raw.image_urls:
            raw.image_urls.insert(0, u)

    # h1
    h1 = soup.find("h1")
    if h1 and not raw.title:
        raw.title = h1.get_text(strip=True)

    # Product images
    for img in soup.find_all("img", src=True):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue
        full = urljoin(url, src)
        if full not in raw.image_urls:
            raw.image_urls.append(full)

    # Variants: size/volume (e.g. 30ml, 50ml, 100ml)
    size_pattern = re.compile(r"\b(\d+\s*ml)\b", re.I)
    seen_sizes = set()
    for elem in soup.find_all(string=size_pattern):
        for m in size_pattern.finditer(elem):
            size = m.group(1).replace(" ", "").lower()
            if size not in seen_sizes:
                seen_sizes.add(size)
                raw.variants.append({
                    "size": size,
                    "title": f"{raw.title or 'Product'} {size}" if raw.title else size,
                })
    if not raw.variants and raw.title:
        raw.variants.append({"size": "", "title": raw.title})

    return raw
