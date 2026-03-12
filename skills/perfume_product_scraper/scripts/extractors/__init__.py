"""
Site-specific extractors for perfume product pages.
Register (domain -> extract_func) in REGISTRY; otherwise generic extractor is used.
"""

from .generic import extract as generic_extract

# Domain (no www) -> extract function (soup, url) -> RawProduct
REGISTRY = {
    # "example.com": example_extract,
}


def get_extractor(domain: str):
    """Return extract function for domain or generic."""
    return REGISTRY.get(domain, generic_extract)
