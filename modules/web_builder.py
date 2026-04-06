"""
Web Builder — Assembles a cinematic, responsive HTML page from a BrandKit.

No framework dependencies. Vanilla HTML/CSS/JS only.
Brand token injection from BrandKit — colours, fonts, copy, products all
flow in automatically. Output is a single deployable file.
"""
from __future__ import annotations
from pathlib import Path
from schemas.brand_kit import BrandKit


# ── Colour utilities ──────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> str:
    """#RRGGBB → 'R, G, B'"""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
    except ValueError:
        return "0, 0, 0"


def _darken(hex_color: str, amount: float = 0.18) -> str:
    """Darken a hex colour by amount (0–1)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r = max(0, int(int(h[0:2], 16) * (1 - amount)))
        g = max(0, int(int(h[2:4], 16) * (1 - amount)))
        b = max(0, int(int(h[4:6], 16) * (1 - amount)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return "#000000"


def _lighten(hex_color: str, amount: float = 0.92) -> str:
    """Mix a hex colour toward white."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r = min(255, int(int(h[0:2], 16) + (255 - int(h[0:2], 16)) * amount))
        g = min(255, int(int(h[2:4], 16) + (255 - int(h[2:4], 16)) * amount))
        b = min(255, int(int(h[4:6], 16) + (255 - int(h[4:6], 16)) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return "#f5f5f5"


# ── Component renderers ───────────────────────────────────────────────────────

def _render_value_props(kit: BrandKit) -> str:
    if not kit.copy.value_propositions:
        return ""
    items = "".join(
        f'<div class="vp-item fade-up">'
        f'<div class="vp-check" aria-hidden="true"></div>'
        f'<p>{vp}</p>'
        f'</div>'
        for vp in kit.copy.value_propositions[:4]
    )
    return f"""
    <section class="vp-section" aria-label="Why {kit.copy.business_name}">
      <div class="container">
        <h2 class="section-title fade-up">Why {kit.copy.business_name}</h2>
        <div class="vp-grid">{items}</div>
      </div>
    </section>"""


def _render_products(kit: BrandKit) -> str:
    if not kit.products:
        return ""
    cards = ""
    for p in kit.products[:3]:
        feats = "".join(f"<li>{f}</li>" for f in p.features[:4])
        price_html = f'<div class="price">{p.price}</div>' if p.price else ""
        cards += f"""
        <article class="product-card fade-up">
          <header class="product-header">
            <h3>{p.name}</h3>
            {price_html}
          </header>
          <p class="product-desc">{p.description[:140] if p.description else ""}</p>
          {"<ul class='feature-list'>" + feats + "</ul>" if feats else ""}
          <a href="{kit.url}" class="btn btn-primary" target="_blank" rel="noopener">{kit.copy.cta_primary}</a>
        </article>"""
    return f"""
    <section class="products-section" id="products">
      <div class="container">
        <h2 class="section-title fade-up">Products &amp; Solutions</h2>
        <div class="products-grid">{cards}</div>
      </div>
    </section>"""


def _google_fonts_tag(kit: BrandKit) -> str:
    if kit.typography.google_fonts_url:
        return f'<link href="{kit.typography.google_fonts_url}" rel="stylesheet">'
    hf = kit.typography.heading_font
    bf = kit.typography.body_font
    if hf in ("sans-serif", "serif", "monospace") and bf in ("sans-serif", "serif", "monospace"):
        return ""
    encode = lambda s: urllib.parse.quote(s) if s not in ("sans-serif", "serif", "monospace") else None
    import urllib.parse
    families = []
    if hf not in ("sans-serif", "serif", "monospace"):
        families.append(f"family={urllib.parse.quote(hf)}:wght@400;600;700")
    if bf not in ("sans-serif", "serif", "monospace") and bf != hf:
        families.append(f"family={urllib.parse.quote(bf)}:wght@400;500")
    if not families:
        return ""
    return f'<link href="https://fonts.googleapis.com/css2?{"&".join(families)}&display=swap" rel="stylesheet">'


# ── Main builder ──────────────────────────────────────────────────────────────

def build(kit: BrandKit, output_path: str, assets: dict | None = None) -> str:
    """
    Assemble a complete cinematic webpage from a BrandKit.
    assets dict: {"hero_background": "/path/to/image.png"}
    Returns the output file path.
    """
    assets = assets or {}
    import urllib.parse

    # Hero background
    hero_bg_path = assets.get("hero_background", "")
    if hero_bg_path and Path(hero_bg_path).exists():
        hero_bg_css = f"background-image: url('{hero_bg_path}'); background-size: cover; background-position: center;"
    else:
        hero_bg_css = (
            f"background: linear-gradient(140deg, "
            f"{kit.colors.secondary} 0%, {kit.colors.primary} 60%, "
            f"{_darken(kit.colors.primary, 0.25)} 100%);"
        )

    primary_rgb = _hex_to_rgb(kit.colors.primary)
    fonts_tag = _google_fonts_tag(kit)
    vp_section = _render_value_props(kit)
    products_section = _render_products(kit)
    surface_tint = _lighten(kit.colors.primary, 0.94)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{kit.copy.business_name}{" — " + kit.copy.tagline if kit.copy.tagline else ""}</title>
  <meta name="description" content="{kit.copy.description or kit.copy.tagline}">
  <meta property="og:title" content="{kit.copy.business_name}">
  <meta property="og:description" content="{kit.copy.description}">
  {fonts_tag}
  <style>
    /* ── Design tokens ───────────────────────────────────── */
    :root {{
      --primary:        {kit.colors.primary};
      --primary-dark:   {_darken(kit.colors.primary)};
      --primary-light:  {surface_tint};
      --primary-rgb:    {primary_rgb};
      --secondary:      {kit.colors.secondary};
      --accent:         {kit.colors.accent};
      --bg:             {kit.colors.background};
      --surface:        {kit.colors.surface};
      --text:           {kit.colors.text};
      --text-muted:     {kit.colors.text_light};
      --font-head:      '{kit.typography.heading_font}', system-ui, sans-serif;
      --font-body:      '{kit.typography.body_font}', system-ui, sans-serif;
      --radius:         10px;
      --shadow-sm:      0 2px 8px rgba(0,0,0,0.07);
      --shadow-md:      0 6px 24px rgba(0,0,0,0.10);
      --shadow-lg:      0 16px 48px rgba(0,0,0,0.14);
      --ease:           cubic-bezier(0.4, 0, 0.2, 1);
      --dur:            0.28s;
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; font-size: 16px; }}
    body {{
      font-family: var(--font-body);
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    /* ── Layout helpers ──────────────────────────────── */
    .container {{ max-width: 1120px; margin: 0 auto; padding: 0 5vw; }}
    .section-title {{
      font-family: var(--font-head);
      font-size: clamp(26px, 3.5vw, 40px);
      font-weight: 700; letter-spacing: -0.025em;
      color: var(--text); margin-bottom: 48px; text-align: center;
    }}

    /* ── Navigation ──────────────────────────────────── */
    nav {{
      position: fixed; inset-block-start: 0; inset-inline: 0; z-index: 200;
      height: 64px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 5vw;
      background: rgba({_hex_to_rgb(kit.colors.background)}, 0.94);
      backdrop-filter: blur(16px) saturate(160%);
      -webkit-backdrop-filter: blur(16px) saturate(160%);
      border-bottom: 1px solid rgba(0,0,0,0.07);
      transition: box-shadow var(--dur) var(--ease);
    }}
    nav.scrolled {{ box-shadow: var(--shadow-sm); }}
    .nav-brand {{
      font-family: var(--font-head);
      font-weight: 700; font-size: 17px;
      color: var(--primary); text-decoration: none;
      letter-spacing: -0.01em;
    }}
    .nav-links {{
      display: flex; gap: 28px; list-style: none; align-items: center;
    }}
    .nav-links a {{
      font-size: 14px; font-weight: 500;
      color: var(--text); text-decoration: none;
      transition: color var(--dur) var(--ease);
    }}
    .nav-links a:hover {{ color: var(--primary); }}
    .nav-cta {{
      background: var(--primary); color: #fff;
      padding: 9px 22px; border-radius: var(--radius);
      font-size: 13px; font-weight: 600; text-decoration: none;
      transition: filter var(--dur) var(--ease), transform var(--dur) var(--ease);
    }}
    .nav-cta:hover {{ filter: brightness(1.1); transform: translateY(-1px); }}

    /* ── Hero ────────────────────────────────────────── */
    .hero {{
      min-height: 100svh;
      display: flex; align-items: center;
      padding: 96px 5vw 72px;
      position: relative; overflow: hidden;
      {hero_bg_css}
    }}
    .hero::after {{
      content: '';
      position: absolute; inset: 0;
      background: linear-gradient(
        120deg,
        rgba({_hex_to_rgb(kit.colors.secondary)}, 0.78) 0%,
        rgba({_hex_to_rgb(kit.colors.secondary)}, 0.4) 50%,
        transparent 100%
      );
    }}
    .hero-content {{ position: relative; z-index: 1; max-width: 620px; }}
    .eyebrow {{
      display: inline-block;
      font-size: 11px; font-weight: 700; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--primary);
      background: rgba({primary_rgb}, 0.12);
      padding: 5px 14px; border-radius: 20px;
      margin-bottom: 20px;
    }}
    .hero h1 {{
      font-family: var(--font-head);
      font-size: clamp(36px, 5.5vw, 72px);
      font-weight: 700; line-height: 1.05; letter-spacing: -0.03em;
      color: #fff; margin-bottom: 20px;
    }}
    .hero-sub {{
      font-size: clamp(16px, 2vw, 20px);
      color: rgba(255,255,255,0.82); margin-bottom: 40px;
      max-width: 500px; line-height: 1.55;
    }}
    .hero-actions {{ display: flex; gap: 14px; flex-wrap: wrap; }}

    /* ── Buttons ─────────────────────────────────────── */
    .btn {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 13px 30px; border-radius: var(--radius);
      font-weight: 600; font-size: 14px; text-decoration: none;
      transition: all var(--dur) var(--ease);
      cursor: pointer; border: 2px solid transparent;
    }}
    .btn-primary {{
      background: var(--primary); color: #fff;
      border-color: var(--primary);
    }}
    .btn-primary:hover {{
      filter: brightness(1.08);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(var(--primary-rgb), 0.38);
    }}
    .btn-ghost {{
      background: transparent; color: #fff;
      border-color: rgba(255,255,255,0.5);
    }}
    .btn-ghost:hover {{
      border-color: #fff;
      background: rgba(255,255,255,0.1);
    }}
    .btn-outline {{
      background: transparent; color: var(--primary);
      border-color: var(--primary);
    }}
    .btn-outline:hover {{
      background: var(--primary); color: #fff;
      transform: translateY(-1px);
    }}

    /* ── Value propositions ──────────────────────────── */
    .vp-section {{
      padding: 96px 0;
      background: var(--primary-light);
    }}
    .vp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
    }}
    .vp-item {{
      background: var(--bg);
      border-radius: var(--radius);
      padding: 28px 24px;
      display: flex; align-items: flex-start; gap: 14px;
      box-shadow: var(--shadow-sm);
      transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
    }}
    .vp-item:hover {{
      transform: translateY(-3px);
      box-shadow: var(--shadow-md);
    }}
    .vp-check {{
      width: 20px; height: 20px; border-radius: 50%;
      background: var(--primary); flex-shrink: 0;
      margin-top: 2px;
      position: relative;
    }}
    .vp-check::after {{
      content: '';
      position: absolute; left: 6px; top: 4px;
      width: 5px; height: 8px;
      border: 2px solid #fff; border-top: none; border-left: none;
      transform: rotate(40deg);
    }}
    .vp-item p {{ font-size: 15px; font-weight: 500; line-height: 1.45; }}

    /* ── Products ────────────────────────────────────── */
    .products-section {{ padding: 96px 0; }}
    .products-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 28px;
    }}
    .product-card {{
      background: var(--bg);
      border-radius: 14px; padding: 36px 32px;
      border: 1px solid rgba(0,0,0,0.07);
      box-shadow: var(--shadow-sm);
      display: flex; flex-direction: column; gap: 16px;
      transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
    }}
    .product-card:hover {{
      transform: translateY(-5px);
      box-shadow: var(--shadow-lg);
    }}
    .product-header h3 {{
      font-family: var(--font-head);
      font-size: 20px; font-weight: 700; margin-bottom: 6px;
    }}
    .price {{
      font-size: 30px; font-weight: 700; color: var(--primary);
      letter-spacing: -0.02em;
    }}
    .product-desc {{
      font-size: 14px; color: var(--text-muted);
      line-height: 1.55; flex: 1;
    }}
    .feature-list {{
      list-style: none; display: flex; flex-direction: column; gap: 8px;
    }}
    .feature-list li {{
      font-size: 13px; padding: 7px 0;
      border-bottom: 1px solid rgba(0,0,0,0.05);
      display: flex; align-items: center; gap: 8px;
    }}
    .feature-list li::before {{
      content: ''; display: inline-block;
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--primary); flex-shrink: 0;
    }}

    /* ── CTA strip ───────────────────────────────────── */
    .cta-strip {{
      padding: 100px 0; text-align: center;
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      color: #fff;
    }}
    .cta-strip h2 {{
      font-family: var(--font-head);
      font-size: clamp(28px, 4vw, 52px);
      font-weight: 700; letter-spacing: -0.025em;
      margin-bottom: 14px;
    }}
    .cta-strip p {{
      font-size: 18px; opacity: 0.85;
      max-width: 560px; margin: 0 auto 40px;
    }}
    .btn-white {{
      background: #fff; color: var(--primary);
      padding: 15px 40px; border-radius: var(--radius);
      font-weight: 700; font-size: 15px;
      text-decoration: none; display: inline-block;
      transition: all var(--dur) var(--ease);
      box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    }}
    .btn-white:hover {{
      transform: translateY(-3px);
      box-shadow: 0 12px 32px rgba(0,0,0,0.2);
    }}

    /* ── Footer ──────────────────────────────────────── */
    footer {{
      padding: 36px 5vw;
      border-top: 1px solid rgba(0,0,0,0.07);
      display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 12px;
      font-size: 13px; color: var(--text-muted);
    }}
    footer a {{ color: var(--primary); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    /* ── Scroll reveal ───────────────────────────────── */
    .fade-up {{
      opacity: 0; transform: translateY(28px);
      transition: opacity 0.55s var(--ease), transform 0.55s var(--ease);
    }}
    .fade-up.visible {{ opacity: 1; transform: translateY(0); }}

    /* ── Responsive ──────────────────────────────────── */
    @media (max-width: 768px) {{
      .nav-links {{ display: none; }}
      .hero-actions {{ flex-direction: column; }}
      .hero-actions .btn {{ text-align: center; justify-content: center; }}
      footer {{ flex-direction: column; text-align: center; }}
    }}
  </style>
</head>
<body>

<!-- Navigation -->
<nav id="nav" role="navigation" aria-label="Main navigation">
  <a class="nav-brand" href="/">{kit.copy.business_name}</a>
  <ul class="nav-links">
    {"".join(f'<li><a href="#{item.lower().replace(" ", "-")}">{item}</a></li>' for item in ["Products", "About", "Contact"])}
    <li><a href="{kit.url}" target="_blank" rel="noopener">Visit Site</a></li>
  </ul>
  <a class="nav-cta" href="#products">{kit.copy.cta_primary}</a>
</nav>

<!-- Hero -->
<section class="hero" role="banner">
  <div class="hero-content">
    <span class="eyebrow">{kit.style.industry or kit.copy.business_name}</span>
    <h1>{kit.copy.headline or kit.copy.business_name}</h1>
    <p class="hero-sub">{kit.copy.subheadline or kit.copy.description}</p>
    <div class="hero-actions">
      <a href="#products" class="btn btn-primary">{kit.copy.cta_primary}</a>
      <a href="{kit.url}" class="btn btn-ghost" target="_blank" rel="noopener">{kit.copy.cta_secondary}</a>
    </div>
  </div>
</section>

{vp_section}
{products_section}

<!-- CTA Strip -->
<section class="cta-strip">
  <div class="container">
    <h2 class="fade-up">{kit.copy.headline or "Ready to Get Started?"}</h2>
    <p class="fade-up">{kit.copy.description or kit.copy.tagline}</p>
    <a href="{kit.url}" class="btn-white" target="_blank" rel="noopener">{kit.copy.cta_primary}</a>
  </div>
</section>

<!-- Footer -->
<footer>
  <span>© {kit.copy.business_name} — Built with Cinematic Pipeline</span>
  <a href="{kit.url}" target="_blank" rel="noopener">{kit.domain}</a>
</footer>

<script>
  // ── Scroll-aware nav ───────────────────────────────────────────────────
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => {{
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }}, {{ passive: true }});

  // ── Fade-up reveal ─────────────────────────────────────────────────────
  const io = new IntersectionObserver(
    entries => entries.forEach(e => {{
      if (e.isIntersecting) {{
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }}
    }}),
    {{ threshold: 0.12, rootMargin: '0px 0px -32px 0px' }}
  );
  document.querySelectorAll('.fade-up').forEach(el => io.observe(el));
</script>

</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path