"""
Brand Kit — Typed data contract for brand extraction and campaign generation.

This is the central schema. Every module reads from and writes to this structure.
Changing a field here ripples through extraction, prompts, web build, and ads.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class BrandColors:
    primary: str = "#0073CE"       # Main brand colour — used on CTAs, accents, headers
    secondary: str = "#313131"     # Supporting colour — text, secondary elements
    accent: str = "#ffffff"        # Highlight / contrast colour
    background: str = "#ffffff"    # Page background
    surface: str = "#f5f7fa"       # Card / panel background
    text: str = "#313131"          # Body text
    text_light: str = "#666666"    # Muted text, captions


@dataclass
class BrandTypography:
    heading_font: str = "sans-serif"
    body_font: str = "sans-serif"
    heading_weight: int = 700
    body_weight: int = 400
    google_fonts_url: str = ""     # Full Google Fonts URL if detected


@dataclass
class BrandCopy:
    business_name: str = ""
    tagline: str = ""
    description: str = ""          # 1-2 sentence brand summary
    headline: str = ""             # Primary marketing headline
    subheadline: str = ""          # Supporting subtitle
    cta_primary: str = "Learn More"
    cta_secondary: str = "Contact Us"
    value_propositions: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class BrandProduct:
    name: str = ""
    price: str = ""
    currency: str = "AUD"
    description: str = ""
    features: List[str] = field(default_factory=list)
    image_url: str = ""
    category: str = ""
    sku: str = ""


@dataclass
class BrandStyle:
    """
    Creative direction extracted from brand analysis.
    These values drive prompt generation for images, video, and layout.
    """
    industry: str = ""
    tone: str = "professional"              # professional | luxury | friendly | industrial | technical
    target_audience: str = ""
    visual_style: str = "clean"            # clean | cinematic | bold | minimal | industrial
    lighting: str = "studio"               # studio | dramatic | natural | product | environmental
    color_grade: str = "neutral"           # neutral | warm | cool | desaturated | vibrant
    motion_style: str = "smooth"           # smooth | dynamic | subtle | cinematic | energetic
    photography_style: str = "product"     # product | lifestyle | corporate | editorial


@dataclass
class BrandKit:
    """
    Complete brand data extracted from a URL.
    Serialisable to/from JSON. Used as input to all generation modules.
    """
    url: str = ""
    domain: str = ""
    extracted_at: str = ""
    extraction_method: str = "html-parse+gemini"
    confidence: float = 0.0            # 0–1, AI's self-reported confidence in extraction

    colors: BrandColors = field(default_factory=BrandColors)
    typography: BrandTypography = field(default_factory=BrandTypography)
    copy: BrandCopy = field(default_factory=BrandCopy)
    products: List[BrandProduct] = field(default_factory=list)
    style: BrandStyle = field(default_factory=BrandStyle)

    logo_url: str = ""
    favicon_url: str = ""
    hero_image_url: str = ""
    social_links: dict = field(default_factory=dict)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict) -> "BrandKit":
        kit = cls()
        kit.colors = BrandColors(**{
            k: v for k, v in data.get("colors", {}).items()
            if k in BrandColors.__dataclass_fields__
        })
        kit.typography = BrandTypography(**{
            k: v for k, v in data.get("typography", {}).items()
            if k in BrandTypography.__dataclass_fields__
        })
        kit.copy = BrandCopy(**{
            k: v for k, v in data.get("copy", {}).items()
            if k in BrandCopy.__dataclass_fields__
        })
        kit.products = [
            BrandProduct(**{k: v for k, v in p.items() if k in BrandProduct.__dataclass_fields__})
            for p in data.get("products", [])
        ]
        kit.style = BrandStyle(**{
            k: v for k, v in data.get("style", {}).items()
            if k in BrandStyle.__dataclass_fields__
        })
        for key in ("url", "domain", "extracted_at", "extraction_method", "confidence",
                    "logo_url", "favicon_url", "hero_image_url", "social_links"):
            if key in data:
                setattr(kit, key, data[key])
        return kit

    @classmethod
    def from_json(cls, path: str) -> "BrandKit":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def summary(self) -> str:
        """Human-readable one-liner for logging."""
        return (
            f"{self.copy.business_name or self.domain} | "
            f"{self.style.industry} | {self.style.tone} | "
            f"{self.colors.primary} | {self.typography.heading_font}"
        )