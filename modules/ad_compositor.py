"""
Ad Compositor — Social media ad generation.

Outputs self-contained HTML files for three standard formats:
  story     — 1080 × 1920  (9:16)  Instagram/TikTok story
  feed      — 1080 × 1080  (1:1)   Instagram/Facebook feed
  landscape — 1200 × 628   (1.91)  Facebook/LinkedIn/Twitter

Each file is a complete, browser-renderable ad. Open in Chrome and screenshot
at the exact pixel dimensions to get a production-ready image.

No external dependencies. Brand tokens injected from BrandKit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from schemas.brand_kit import BrandKit, BrandProduct
from modules.tracer import PipelineTracer
from modules import prompt_engine


# ── Colour helpers (duplicated locally to avoid import coupling) ──────────────

def _hex_rgb(h: str) -> str:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
    except ValueError:
        return "0, 0, 0"


def _darken(h: str, amt: float = 0.22) -> str:
    raw = h.lstrip("#")
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    try:
        r = max(0, int(int(raw[0:2], 16) * (1 - amt)))
        g = max(0, int(int(raw[2:4], 16) * (1 - amt)))
        b = max(0, int(int(raw[4:6], 16) * (1 - amt)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return "#000000"


# ── Ad template ───────────────────────────────────────────────────────────────

_AD_FORMATS = {
    "story":     (1080, 1920, "9:16"),
    "feed":      (1080, 1080, "1:1"),
    "landscape": (1200, 628,  "16:9"),
}


def _render_ad(
    kit: BrandKit,
    copy: dict,
    bg_image_path: str,
    width: int,
    height: int,
    fmt: str,
) -> str:
    """Generate a single ad HTML string."""
    primary_rgb = _hex_rgb(kit.colors.primary)
    dark_primary = _darken(kit.colors.primary)

    # Background layer
    if bg_image_path and Path(bg_image_path).exists():
        bg_css = f"background-image: url('{bg_image_path}'); background-size: cover; background-position: center;"
    else:
        bg_css = f"background: linear-gradient(145deg, {kit.colors.secondary} 0%, {kit.colors.primary} 70%, {dark_primary} 100%);"

    # Features HTML
    features_html = ""
    if copy.get("features") and fmt in ("story", "feed"):
        features_html = "<ul class='ad-features'>" + "".join(
            f"<li>{f}</li>" for f in copy["features"][:3]
        ) + "</ul>"

    # Price HTML
    price_html = ""
    if copy.get("price"):
        price_html = f'<div class="ad-price">{copy["price"]}</div>'

    # Sizing: font scale adjusts with canvas
    scale = height / 1920
    h1_size = max(28, int(72 * scale))
    sub_size = max(14, int(32 * scale))
    badge_size = max(10, int(20 * scale))
    cta_size = max(13, int(28 * scale))
    padding = max(24, int(60 * scale))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ad — {copy.get('business', '')} — {fmt}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ width: {width}px; height: {height}px; overflow: hidden; }}
    body {{
      font-family: '{kit.typography.heading_font}', system-ui, sans-serif;
      -webkit-font-smoothing: antialiased;
      position: relative;
    }}

    /* ── Canvas ──────────────────────────────────── */
    .canvas {{
      width: {width}px; height: {height}px;
      position: relative; overflow: hidden;
      {bg_css}
    }}

    /* ── Overlay gradient ─────────────────────────── */
    .overlay {{
      position: absolute; inset: 0;
      background: linear-gradient(
        to top,
        rgba({_hex_rgb(kit.colors.secondary)}, 0.92) 0%,
        rgba({_hex_rgb(kit.colors.secondary)}, 0.55) 35%,
        rgba({_hex_rgb(kit.colors.secondary)}, 0.1) 65%,
        transparent 100%
      );
    }}

    /* ── Content ──────────────────────────────────── */
    .content {{
      position: absolute; inset: 0;
      display: flex; flex-direction: column;
      justify-content: flex-end;
      padding: {padding}px;
      gap: {int(16 * scale)}px;
    }}

    /* ── Brand badge ──────────────────────────────── */
    .brand-badge {{
      position: absolute; top: {padding}px; left: {padding}px;
      background: var(--primary);
      color: #fff; font-size: {badge_size}px;
      font-weight: 700; letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: {int(8*scale)}px {int(18*scale)}px;
      border-radius: {int(20*scale)}px;
    }}

    /* ── Price badge ──────────────────────────────── */
    .ad-price {{
      display: inline-block;
      font-size: {int(h1_size * 0.72)}px;
      font-weight: 800; color: #fff;
      letter-spacing: -0.02em;
      text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}

    /* ── Headline ─────────────────────────────────── */
    .ad-headline {{
      font-size: {h1_size}px;
      font-weight: 800; color: #fff;
      line-height: 1.05; letter-spacing: -0.03em;
      text-shadow: 0 2px 12px rgba(0,0,0,0.25);
    }}

    /* ── Sub ──────────────────────────────────────── */
    .ad-sub {{
      font-size: {sub_size}px; color: rgba(255,255,255,0.88);
      font-weight: 400; line-height: 1.35;
      max-width: {int(width * 0.88)}px;
    }}

    /* ── Features ─────────────────────────────────── */
    .ad-features {{
      list-style: none;
      display: flex; flex-direction: column;
      gap: {int(8*scale)}px;
    }}
    .ad-features li {{
      font-size: {int(sub_size * 0.8)}px;
      color: rgba(255,255,255,0.9); font-weight: 500;
      display: flex; align-items: center; gap: {int(10*scale)}px;
    }}
    .ad-features li::before {{
      content: '';
      display: inline-block; flex-shrink: 0;
      width: {int(8*scale)}px; height: {int(8*scale)}px;
      border-radius: 50%; background: var(--primary);
    }}

    /* ── CTA button ───────────────────────────────── */
    .ad-cta {{
      display: inline-flex; align-items: center;
      background: var(--primary);
      color: #fff; font-weight: 700;
      font-size: {cta_size}px;
      padding: {int(14*scale)}px {int(36*scale)}px;
      border-radius: {int(50*scale)}px;
      align-self: flex-start;
      box-shadow: 0 {int(6*scale)}px {int(20*scale)}px rgba({primary_rgb}, 0.45);
      letter-spacing: 0.01em;
    }}

    :root {{
      --primary: {kit.colors.primary};
      --primary-rgb: {primary_rgb};
    }}
  </style>
</head>
<body>
<div class="canvas">
  <div class="overlay"></div>
  <div class="brand-badge">{copy.get('business', kit.copy.business_name)}</div>
  <div class="content">
    {price_html}
    <h2 class="ad-headline">{copy.get('headline', '')}</h2>
    <p class="ad-sub">{copy.get('subheadline', '')}</p>
    {features_html}
    <a class="ad-cta">{copy.get('cta', kit.copy.cta_primary)}</a>
  </div>
</div>
</body>
</html>"""


# ── Public interface ──────────────────────────────────────────────────────────

def composite_all(
    kit: BrandKit,
    product: Optional[BrandProduct],
    bg_image_path: Optional[str],
    run_dir: str,
    tracer: PipelineTracer,
) -> dict[str, str]:
    """
    Generate all three social ad variants for a product (or brand-level).
    Returns {format_name: output_path}.
    """
    outputs: dict[str, str] = {}
    bg = bg_image_path or ""

    for fmt, (width, height, aspect) in _AD_FORMATS.items():
        copy = prompt_engine.social_ad_copy(kit, product, fmt)
        html = _render_ad(kit, copy, bg, width, height, fmt)

        product_slug = (
            product.name.lower().replace(" ", "-")[:20]
            if product else "brand"
        )
        out_path = str(Path(run_dir) / "ads" / f"{product_slug}-{fmt}.html")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        tracer.log(f"ad-{fmt}", "claude",
                   status="success", output_path=out_path,
                   metadata={"width": width, "height": height, "aspect": aspect})
        outputs[fmt] = out_path

    return outputs