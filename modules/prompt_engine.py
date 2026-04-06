"""
Prompt Engine — BrandKit → model-ready prompts.

Prompts are composed dynamically from brand data. No hardcoded product names
or colours. A 15-year DP doesn't write generic descriptions — they spec
exact lighting rigs, surface materials, and motion behaviour.
"""
from __future__ import annotations
from schemas.brand_kit import BrandKit, BrandProduct


# ── Internal style directives ─────────────────────────────────────────────────

_TONE = {
    "professional": "authoritative, precise, clean",
    "luxury":       "premium, refined, aspirational, restrained",
    "friendly":     "warm, approachable, approachable colour temperature",
    "industrial":   "robust, technical, hard-edged, functional",
    "technical":    "clinical, scientific, high-precision, credible",
}

_LIGHTING = {
    "studio":       "controlled studio lighting — large softbox key at 45°, fill card opposite, gentle rim from behind, clean shadow beneath product on solid surface",
    "dramatic":     "single hard key light at 30° creating deep directional shadow, strong contrast, dark fill side — cinematic chiaroscuro",
    "natural":      "diffused north-facing daylight, soft roll-off, realistic ambient occlusion, no harsh shadows",
    "product":      "dual softbox product photography setup, even fill, specular highlights on surfaces, clean white base",
    "environmental":"ambient environmental illumination appropriate to context, motivated light sources only",
}

_GRADE = {
    "neutral":      "neutral colour grade, calibrated white balance, accurate skin tones and material colours",
    "warm":         "warm colour grade, slight amber push in highlights, rich mid-tone warmth",
    "cool":         "cool desaturated grade, lifted shadows, slight blue-grey in midtones — clean and clinical",
    "desaturated":  "muted desaturated palette, pulled saturation across all channels, editorial feel",
    "vibrant":      "saturated vivid colours, punchy contrast, clean blacks",
}

_MOTION = {
    "smooth":       "slow deliberate camera movement — 0.3–0.5 m/s dolly, imperceptible acceleration curve",
    "dynamic":      "confident purposeful push — moderate pace, clean start/stop with minimal ease",
    "subtle":       "barely perceptible drift, effectively static — subject does all the moving",
    "cinematic":    "shallow depth-of-field pull focus, slow orbit at 20–30° arc, motivated movement",
    "energetic":    "dynamic tracking with velocity, subject-locked with environmental blur",
}

_PHOTO_STYLE = {
    "product":    "professional product photography — object is the sole subject, graphic composition",
    "lifestyle":  "lifestyle photography — product in natural use context, human element present",
    "corporate":  "corporate photography — clean, trustworthy, business context",
    "editorial":  "editorial photography — conceptual, art-directed, narrative-driven",
}


def _style_block(kit: BrandKit) -> str:
    """Build a reusable multi-line style directive from brand kit values."""
    tone = _TONE.get(kit.style.tone, _TONE["professional"])
    lighting = _LIGHTING.get(kit.style.lighting, _LIGHTING["studio"])
    grade = _GRADE.get(kit.style.color_grade, _GRADE["neutral"])
    photo = _PHOTO_STYLE.get(kit.style.photography_style, _PHOTO_STYLE["product"])
    return f"{tone}. {lighting}. {grade}. {photo}."


def _motion_block(kit: BrandKit) -> str:
    return _MOTION.get(kit.style.motion_style, _MOTION["smooth"])


# ── Image prompts ─────────────────────────────────────────────────────────────

def hero_background(kit: BrandKit) -> str:
    """Abstract hero background — no product, no text, no people."""
    return (
        f"Abstract cinematic background for a {kit.style.industry} brand. "
        f"Dominant brand colour {kit.colors.primary} bleeds into {kit.colors.secondary}. "
        f"Atmospheric depth, subtle texture, no identifiable objects, no text, no people. "
        f"{_style_block(kit)} "
        f"2K resolution, 16:9 widescreen, designed as a hero section background."
    )


def product_start_frame(kit: BrandKit, product: BrandProduct) -> str:
    """Product in assembled, pristine condition — the 'before' keyframe."""
    feature_hint = (
        f" Key distinguishing features: {', '.join(product.features[:3])}."
        if product.features else ""
    )
    return (
        f"Professional {kit.style.photography_style} photography of {product.name}. "
        f"{product.description[:120] + '.' if product.description else ''}"
        f"{feature_hint} "
        f"Product centred and floating on solid {kit.colors.primary} background. "
        f"No props, no context, no text overlays. "
        f"{_style_block(kit)} "
        f"8K quality, ultra-sharp detail on all surfaces and edges."
    )


def product_end_frame(kit: BrandKit, product: BrandProduct) -> str:
    """Product in exploded/disassembled state — the 'after' keyframe."""
    return (
        f"Professional exploded-view product photography of {product.name}. "
        f"The product is elegantly disassembled — all major components floating "
        f"apart in mid-air on solid {kit.colors.primary} background. "
        f"Components arranged with clear vertical hierarchy and generous spacing "
        f"so each part reads distinctly. "
        f"No labels or callouts. "
        f"{_style_block(kit)} "
        f"8K quality, photorealistic exploded diagram style."
    )


def social_background(kit: BrandKit, format_name: str = "story") -> str:
    """Background image for a social media ad."""
    dims = {
        "story":     "1080×1920 vertical 9:16",
        "feed":      "1080×1080 square 1:1",
        "landscape": "1200×628 landscape 1.91:1",
    }
    dim = dims.get(format_name, "1080×1080")
    return (
        f"Cinematic social media ad background for {kit.copy.business_name}. "
        f"Brand colour {kit.colors.primary}. Abstract, premium, no text. "
        f"{_style_block(kit)} "
        f"{dim} format. High contrast, designed for overlaid white text."
    )


# ── Video prompts ─────────────────────────────────────────────────────────────

def product_reveal_video(kit: BrandKit, product: BrandProduct) -> str:
    """Slow product orbit / turntable reveal — workhorse hero video."""
    return (
        f"Cinematic product reveal film for {product.name} by {kit.copy.business_name}. "
        f"The product rotates slowly on its vertical axis — a 45-degree arc over the full duration. "
        f"{_motion_block(kit)}. "
        f"{_style_block(kit)} "
        f"Solid {kit.colors.primary} background. Steady locked-off camera with imperceptible breathing. "
        f"No cuts, no text, no voice-over. Professional commercial grade."
    )


def pull_apart_video(kit: BrandKit, product: BrandProduct) -> str:
    """Product disassembly / explode-apart reveal video."""
    return (
        f"Smooth cinematic pull-apart animation of {product.name}. "
        f"The product begins fully assembled, centred in frame. "
        f"Over the duration, each major component separates cleanly — "
        f"outer casing first, then internal modules, each floating apart "
        f"with precise mechanical motion and a subtle easing curve. "
        f"Final frame: all components suspended equidistant in a balanced composition. "
        f"{_motion_block(kit)}. "
        f"{_style_block(kit)} "
        f"Solid {kit.colors.primary} background throughout. "
        f"Steady camera — no rotation, no push. "
        f"Depth of field subtly deepens as components separate."
    )


def hero_brand_film(kit: BrandKit) -> str:
    """Abstract brand film — no product, pure atmosphere."""
    return (
        f"Short cinematic brand film for {kit.copy.business_name}. "
        f"{kit.copy.description or kit.copy.tagline}. "
        f"Atmospheric, abstract, no identifiable products or people. "
        f"Brand colours {kit.colors.primary} and {kit.colors.secondary} dominate. "
        f"{_motion_block(kit)}. "
        f"{_style_block(kit)} "
        f"Duration: full clip. No cuts. No text. No voice-over."
    )


# ── Copy generation ───────────────────────────────────────────────────────────

def social_ad_copy(kit: BrandKit, product, fmt: str = "story") -> dict:
    """
    Generate copy dict for a social ad.
    Falls back to brand-level copy when no product is supplied.
    """
    from schemas.brand_kit import BrandProduct as BP  # avoid circular at module level

    name = product.name if product else kit.copy.business_name
    price = product.price if product else ""
    desc = (product.description[:90] if product and product.description
            else kit.copy.subheadline or kit.copy.tagline)
    features = product.features[:3] if product and product.features else kit.copy.value_propositions[:3]

    headline = kit.copy.headline or f"Introducing {name}"
    subhead = kit.copy.subheadline or desc

    limits = {
        "story":     {"headline": 36, "subhead": 72},
        "feed":      {"headline": 44, "subhead": 90},
        "landscape": {"headline": 56, "subhead": 110},
    }
    lim = limits.get(fmt, limits["feed"])

    return {
        "headline":    headline[: lim["headline"]],
        "subheadline": subhead[: lim["subhead"]],
        "cta":         kit.copy.cta_primary,
        "price":       price,
        "business":    kit.copy.business_name,
        "features":    features,
        "product_name": name,
    }


# Allow importing without circular dependency issues
try:
    from typing import Optional
except ImportError:
    pass