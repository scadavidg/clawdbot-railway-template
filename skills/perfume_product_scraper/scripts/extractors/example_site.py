"""
Example site-specific extractor.
Register in extractors/__init__.py: REGISTRY["example.com"] = example_site.extract
"""

from .base import RawProduct


def extract(soup, url: str) -> RawProduct:
    """Extract product from example.com perfume pages."""
    raw = RawProduct(url=url)

    # Site-specific selectors (customize per site)
    title_el = soup.select_one("h1.product-title") or soup.find("h1")
    if title_el:
        raw.title = title_el.get_text(strip=True)

    desc_el = soup.select_one(".product-description") or soup.find("meta", attrs={"name": "description"})
    if desc_el:
        raw.description = desc_el.get("content") if desc_el.name == "meta" else desc_el.get_text(separator=" ", strip=True)

    for img in soup.select(".product-gallery img") or soup.find_all("img", src=True):
        src = img.get("data-src") or img.get("src")
        if src and src not in raw.image_urls:
            raw.image_urls.append(src)

    # Variants: e.g. size buttons
    for btn in soup.select("[data-size]") or []:
        size = btn.get("data-size") or btn.get_text(strip=True)
        if size and not any(v.get("size") == size for v in raw.variants):
            raw.variants.append({"size": size, "title": f"{raw.title or 'Product'} {size}"})

    if not raw.variants and raw.title:
        raw.variants.append({"size": "", "title": raw.title})

    # Perfume metadata if present
    brand_el = soup.select_one(".brand-name")
    if brand_el:
        raw.metadata["brand"] = brand_el.get_text(strip=True)

    return raw
