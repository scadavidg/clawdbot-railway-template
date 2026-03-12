"""Shared types for extractors."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawProduct:
    """Extracted raw product data before normalization to Medusa schema."""
    url: str
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)
    variants: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    weight: float | None = None
    width: float | None = None
    height: float | None = None
    length: float | None = None
    origin_country: str | None = None
    material: str | None = None
