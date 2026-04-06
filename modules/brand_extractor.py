"""
Brand Extractor — URL → BrandKit

Two-pass approach:
  1. Structural parse  — HTML/CSS signals: colours, fonts, meta tags, headings, CTAs, prices
  2. AI enrichment     — Gemini synthesises extracted signals into a structured BrandKit,
                         fills gaps, infers industry/tone/style from context

This keeps hallucination low (Gemini works from real page data, not imagination)
while handling the messiness of real-world websites gracefully.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from schemas.brand_kit import (
    BrandKit, BrandColors, BrandTypography, BrandCopy,
    BrandProduct, BrandStyle,
)
from modules.config import PipelineConfig


# ── HTTP ──────────────────────────────────────────────────────────────────────

def _fetch(url: str, timeout: int = 20) -> tuple[str, str]:
    """
    Fetch page HTML. Returns (html_text, final_url).
    Follows redirects, sends a real browser UA to avoid bot-blocking.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = "utf-8"
        content_type = resp.headers.get("Content-Type", "")
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()
        return resp.read().decode(charset, errors="replace"), resp.url


# ── Structural parsers ────────────────────────────────────────────────────────

def _extract_colors(html: str) -> list[str]:
    """
    Pull hex colours from inline styles, <style> blocks, and CSS custom properties.
    Returns deduplicated list, most frequently occurring first.
    """
    # Exclude near-white, near-black, and grey shades — they're structural, not brand
    EXCLUDE = {
        "ffffff", "fff", "000000", "000", "111111", "222222",
        "333333", "444444", "cccccc", "eeeeee", "f0f0f0", "f5f5f5",
        "fafafa", "e0e0e0", "d0d0d0", "999999", "888888",
    }
    hits: dict[str, int] = {}
    for match in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", html):
        norm = match.lower()
        if norm not in EXCLUDE:
            key = f"#{norm}"
            hits[key] = hits.get(key, 0) + 1

    # Also grab rgb() values and convert
    for r_val, g_val, b_val in re.findall(
        r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", html
    ):
        r, g, b = int(r_val), int(g_val), int(b_val)
        if not (r == g == b):  # Skip greys
            key = f"#{r:02x}{g:02x}{b:02x}"
            if key.lower().lstrip("#") not in EXCLUDE:
                hits[key] = hits.get(key, 0) + 1

    return [k for k, _ in sorted(hits.items(), key=lambda x: -x[1])][:12]


def _extract_fonts(html: str) -> list[str]:
    """Extract Google Fonts and font-family declarations."""
    fonts: list[str] = []

    # Google Fonts link tags
    for match in re.findall(r'fonts\.googleapis\.com/css[^"\'>\s]+', html):
        for family in re.findall(r"family=([^&\"'>\s]+)", match):
            for name in urllib.parse.unquote(family).replace("+", " ").split("|"):
                clean = name.split(":")[0].strip()
                if clean and clean not in fonts:
                    fonts.append(clean)

    # CSS font-family declarations
    for raw in re.findall(r"font-family\s*:\s*([^;}{
]+)", html):
        for part in raw.split(","):
            clean = part.strip().strip("'\"")
            if clean and not clean.startswith("var(") and clean not in (
                "inherit", "initial", "unset", "sans-serif", "serif", "monospace", "system-ui"
            ):
                if clean not in fonts:
                    fonts.append(clean)

    return fonts[:6]


def _extract_meta(html: str) -> dict:
    """Extract <meta> and Open Graph tags."""
    out: dict = {}

    for name in ("description", "keywords", "author"):
        pat1 = rf'<meta[^>]+name=["\']?{name}["\']?[^>]+content=["\']([^"\']+')
        pat2 = rf'<meta[^>]+content=["\']([^"\']+')+[^>]+name=["\']?{name}["\']?'
        for pat in (pat1, pat2):
            m = re.search(pat, html, re.I)
            if m:
                out[name] = m.group(1).strip()
                break

    for prop in ("og:title", "og:description", "og:image", "og:site_name"):
        prop_esc = re.escape(prop)
        pat1 = rf'<meta[^>]+property=["\']?{prop_esc}["\']?[^>]+content=["\']([^"\']+')
        pat2 = rf'<meta[^>]+content=["\']([^"\']+')+[^>]+property=["\']?{prop_esc}["\']?'
        for pat in (pat1, pat2):
            m = re.search(pat, html, re.I)
            if m:
                out[prop] = m.group(1).strip()
                break

    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        out["title"] = m.group(1).strip()

    return out


def _extract_content(html: str) -> dict:
    """
    Extract text content signals: headings, CTAs, prices, logo, navigation.
    Strip scripts/styles first to avoid false matches.
    """
    # Remove script and style blocks
    clean = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    clean = re.sub(r"<style[^>]*>.*?</style>", " ", clean, flags=re.S | re.I)
    # Decode common HTML entities
    clean = clean.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#39;", "'")

    out: dict = {}

    # Headings
    h1s = [h.strip() for h in re.findall(r"<h1[^>]*>([^<]+)</h1>", clean, re.I) if len(h.strip()) > 3]
    h2s = [h.strip() for h in re.findall(r"<h2[^>]*>([^<]+)</h2>", clean, re.I) if len(h.strip()) > 3]
    out["h1"] = list(dict.fromkeys(h1s))[:4]
    out["h2"] = list(dict.fromkeys(h2s))[:8]

    # Buttons and CTAs
    btn_pattern = re.compile(
        r'<(?:button|a)[^>]*(?:class|id)=[^>]*(?:btn|button|cta|action|call)[^>]*>([^<]{3,80})<',
        re.I,
    )
    ctals = [m.strip() for m in btn_pattern.findall(clean)]
    out["ctas"] = list(dict.fromkeys(ctals))[:8]

    # Prices
    prices = re.findall(r"(?:AUD|USD|GBP|EUR|\$|£|€)\s*[\d,]+(?:\.\d{2})?", clean)
    out["prices"] = list(dict.fromkeys(prices))[:6]

    # Navigation links
    nav_text = re.findall(r"<(?:nav|header)[^>]*>(.*?)</(?:nav|header)>", clean, re.I | re.S)
    nav_links = []
    for nav in nav_text[:1]:
        nav_links = re.findall(r"<a[^>]*>([^<]{2,40})</a>", nav)
    out["nav_items"] = [n.strip() for n in nav_links if n.strip()][:8]

    # Logo image (look in header/nav area first)
    logo = None
    for block in (nav_text or [""]):
        logo = re.search(r'<img[^>]+src=["\']([^"\']+')+["\'][^>]*(?:alt=["\'][^"\']')+*logo[^"\']')+*["\']|class=["\'][^"\']')+*logo[^"\']')+*["\'])', block, re.I)
        if logo:
            break
    if not logo:
        logo = re.search(r'<img[^>]+(?:logo|brand)[^>]+src=["\']([^"\']+')', clean, re.I)
    out["logo_src"] = logo.group(1) if logo else ""

    return out


# ── AI enrichment ─────────────────────────────────────────────────────────────

def _ai_enrich(url: str, signals: dict, config: PipelineConfig) -> dict:
    """
    Send extracted signals to Gemini for intelligent brand kit construction.
    Returns a raw dict matching the BrandKit schema.
    """
    prompt = f"""You are a senior brand analyst and creative director.

A website scraper has extracted the following raw signals from {url}:

{json.dumps(signals, indent=2)}

Your job: synthesise these signals into a structured brand kit JSON. Use the data above as your primary source — do not invent specific product names, prices, or URLs unless they appear in the signals. Make creative inferences about tone, style, and visual direction based on the available evidence.

Return ONLY valid JSON matching this exact schema:

{{
  "business_name": "string",
  "tagline": "string",
  "description": "1–2 sentence brand summary",
  "industry": "string (e.g. cleaning equipment, healthcare, fashion, SaaS)",
  "tone": "professional | luxury | friendly | industrial | technical",
  "target_audience": "string",
  "visual_style": "clean | cinematic | bold | minimal | industrial",
  "lighting": "studio | dramatic | natural | product | environmental",
  "color_grade": "neutral | warm | cool | desaturated | vibrant",
  "motion_style": "smooth | dynamic | subtle | cinematic | energetic",
  "photography_style": "product | lifestyle | corporate | editorial",
  "primary_color": "#hex — most dominant brand colour from signals, not black/white",
  "secondary_color": "#hex",
  "accent_color": "#hex",
  "text_color": "#hex",
  "background_color": "#hex",
  "heading_font": "font name from signals, or most appropriate for the tone",
  "body_font": "font name from signals, or most appropriate for the tone",
  "google_fonts_url": "full Google Fonts URL if detected, else empty string",
  "headline": "strong, specific marketing headline for this brand",
  "subheadline": "supporting subtitle that reinforces the headline",
  "cta_primary": "primary call to action",
  "cta_secondary": "secondary call to action",
  "value_propositions": ["3–4 key value props extracted or inferred from signals"],
  "keywords": ["5–8 relevant keywords for this brand"],
  "products": [
    {{
      "name": "exact name from signals",
      "price": "exact price string from signals",
      "description": "brief description",
      "features": ["feature 1", "feature 2", "feature 3"],
      "category": "product category"
    }}
  ],
  "logo_url": "logo src from signals if present, else empty string",
  "hero_image_url": "og:image from signals if present, else empty string",
  "confidence": 0.0
}}

Set confidence (0.0–1.0) based on how much real data was available. Return ONLY the JSON object."""

    api_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.extract_model}:generateContent?key={config.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.15,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())

    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw)


# ── Assembler ─────────────────────────────────────────────────────────────────

def _assemble_kit(url: str, ai: dict) -> BrandKit:
    """Map AI response dict → typed BrandKit."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc

    return BrandKit(
        url=url,
        domain=domain,
        extracted_at=datetime.now(timezone.utc).isoformat(),
        extraction_method="html-parse+gemini",
        confidence=float(ai.get("confidence", 0.5)),
        colors=BrandColors(
            primary=ai.get("primary_color", "#0073CE"),
            secondary=ai.get("secondary_color", "#313131"),
            accent=ai.get("accent_color", "#ffffff"),
            background=ai.get("background_color", "#ffffff"),
            text=ai.get("text_color", "#333333"),
        ),
        typography=BrandTypography(
            heading_font=ai.get("heading_font", "sans-serif"),
            body_font=ai.get("body_font", "sans-serif"),
            google_fonts_url=ai.get("google_fonts_url", ""),
        ),
        copy=BrandCopy(
            business_name=ai.get("business_name", domain),
            tagline=ai.get("tagline", ""),
            description=ai.get("description", ""),
            headline=ai.get("headline", ""),
            subheadline=ai.get("subheadline", ""),
            cta_primary=ai.get("cta_primary", "Learn More"),
            cta_secondary=ai.get("cta_secondary", "Contact Us"),
            value_propositions=ai.get("value_propositions", []),
            keywords=ai.get("keywords", []),
        ),
        products=[
            BrandProduct(
                name=p.get("name", ""),
                price=p.get("price", ""),
                description=p.get("description", ""),
                features=p.get("features", []),
                category=p.get("category", ""),
                image_url=p.get("image_url", ""),
            )
            for p in ai.get("products", [])
        ],
        style=BrandStyle(
            industry=ai.get("industry", ""),
            tone=ai.get("tone", "professional"),
            target_audience=ai.get("target_audience", ""),
            visual_style=ai.get("visual_style", "clean"),
            lighting=ai.get("lighting", "studio"),
            color_grade=ai.get("color_grade", "neutral"),
            motion_style=ai.get("motion_style", "smooth"),
            photography_style=ai.get("photography_style", "product"),
        ),
        logo_url=ai.get("logo_url", ""),
        hero_image_url=ai.get("hero_image_url", ""),
    )


# ── Public interface ──────────────────────────────────────────────────────────

def extract(url: str, config: PipelineConfig) -> BrandKit:
    """
    Full brand extraction pipeline.
    URL → HTML parse → AI enrichment → BrandKit
    """
    # Normalise URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"  ⟳ Fetching {url}")
    try:
        html, final_url = _fetch(url)
    except Exception as e:
        raise RuntimeError(f"Could not fetch {url}: {e}") from e

    print(f"  ⟳ Parsing HTML signals ({len(html):,} bytes)")
    signals = {
        "url": final_url,
        "colors": _extract_colors(html),
        "fonts": _extract_fonts(html),
        "meta": _extract_meta(html),
        "content": _extract_content(html),
    }

    if config.verbose:
        print(f"    Colors found:  {signals['colors']}")
        print(f"    Fonts found:   {signals['fonts']}")

    print(f"  ⟳ Enriching with AI brand analysis")
    try:
        ai_data = _ai_enrich(final_url, signals, config)
    except Exception as e:
        raise RuntimeError(f"AI enrichment failed: {e}") from e

    kit = _assemble_kit(final_url, ai_data)

    print(f"  ✓ Brand kit assembled — {kit.summary()}")
    print(f"    Confidence: {kit.confidence:.0%}")

    return kit