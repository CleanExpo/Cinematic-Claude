# Cinematic Claude — Generic URL-to-Campaign Pipeline v3

A fully modular, type-safe Python system that automatically extracts brand identity from any URL and generates production-ready campaign assets: cinematic webpages, social media ads (story/feed/landscape), and product reveal videos.

## Features

- **Brand Extraction**: Two-pass architecture (HTML parsing + Gemini AI enrichment) extracts colors, fonts, copy, products, and visual style from any live website
- **Campaign Generation**: Single CLI command generates webpage, social ads, and product videos with zero manual intervention
- **Type-Safe**: All data flows through strongly-typed `BrandKit` dataclass contracts
- **Observability**: Per-run tracing with `PipelineTracer` logs status, duration, cost estimates, and error tracking
- **Modular Design**: Stateless generation modules (asset_generator, video_generator, web_builder, ad_compositor) can be used independently
- **API-First**: Gemini API for images and text, Veo API for video—no browser automation required
- **Production-Ready**: Vanilla HTML/CSS/JS, responsive design, no framework dependencies

## Architecture

### Core Data Flow
```
URL → Brand Extraction → BrandKit (typed) → Prompts → Asset Generation → Campaign Assets
```

### Module Stack

| Module | Responsibility |
|--------|---|
| `pipeline.py` | CLI orchestrator, task routing, output management |
| `schemas/brand_kit.py` | Typed data contracts (BrandColors, BrandTypography, BrandCopy, BrandProduct, BrandStyle, BrandKit) |
| `modules/config.py` | Injectable configuration (API keys, models, parameters) |
| `modules/tracer.py` | Observability (per-step logging, cost tracking, run summaries) |
| `modules/brand_extractor.py` | Two-pass brand extraction (HTML + AI enrichment) |
| `modules/prompt_engine.py` | Dynamic prompt composition from BrandKit |
| `modules/asset_generator.py` | Gemini image generation wrapper |
| `modules/video_generator.py` | Veo video generation with polling and redirect handling |
| `modules/web_builder.py` | HTML page assembly with responsive design |
| `modules/ad_compositor.py` | Social ad variants (story/feed/landscape) |

## Installation

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_api_key_here
```

**Prerequisites:**
- Python 3.10+
- Gemini API key (for brand extraction and image generation)
- Veo API key (for product video generation)

## Usage

### Full Pipeline (Default)
```bash
python3 pipeline.py --url https://example.com
```

Generates: webpage, social ads (story/feed/landscape), and product video
Output: `./runs/<domain>-<timestamp>/`

### Brand Extraction Only
```bash
python3 pipeline.py --url https://example.com --task brand-extract
```

### Specific Task
```bash
python3 pipeline.py --url https://example.com --task social-ads
python3 pipeline.py --url https://example.com --task webpage
python3 pipeline.py --url https://example.com --task product-video
```

### Dry Run (Show Brand Kit & Prompts, No Generation)
```bash
python3 pipeline.py --url https://example.com --dry-run
```

### Use Existing Brand Kit
```bash
python3 pipeline.py --brand-kit ./runs/example-20260406/brand-kit.json --task webpage
```

### Options
```
--url URL                    Website URL to extract brand from
--brand-kit PATH             Path to existing brand-kit.json (skips extraction)
--task TASK                  brand-extract | webpage | social-ads | product-video | full-campaign (default)
--api-key KEY                Gemini API key (or set GEMINI_API_KEY env var)
--output-dir DIR             Root output directory (default: ./runs)
--video-model MODEL          Veo model ID (default: veo-3.0-fast-generate-001)
--duration N                 Video duration in seconds, 4–8 (default: 8)
--aspect {16:9,9:16}         Video aspect ratio (default: 16:9)
--dry-run                    Extract brand kit, print prompts, no generation
--verbose                    Show timing and extra detail
```

## Output Structure

```
./runs/<domain>-<timestamp>/
├── brand-kit.json              ← Extracted brand identity
├── index.html                  ← Cinematic responsive webpage
├── ads/
│   ├── <product>-story.html    ← 1080×1920 (9:16) Instagram/TikTok story
│   ├── <product>-feed.html     ← 1080×1080 (1:1) Instagram/Facebook feed
│   └── <product>-landscape.html ← 1200×628 (16:9) Facebook/LinkedIn
├── assets/
│   ├── hero-background.png
│   └── <product>-keyframe.png
├── video/
│   └── <product>-reveal.mp4
└── logs/
    └── <run-id>-trace.json     ← Observability log
```

## Brand Kit Format

The `BrandKit` dataclass aggregates all brand signals:

```python
@dataclass
class BrandKit:
    domain: str
    colors: BrandColors             # primary, secondary, accent, background, surface, text
    typography: BrandTypography     # heading_font, body_font, weights, google_fonts_url
    copy: BrandCopy                 # business_name, tagline, CTAs, value props, keywords
    style: BrandStyle               # industry, tone, visual_style, lighting, color_grade, motion_style
    products: list[BrandProduct]    # name, price, features, category
    logo_url: str
    favicon_url: str
    hero_image_url: str
    social_links: dict[str, str]
```

## Key Design Patterns

### Token Injection
Brand kit values flow through prompts to asset generation:
```python
# prompt_engine.py
def hero_background(kit: BrandKit) -> str:
    tone = _TONE.get(kit.style.tone, "professional")
    lighting = _LIGHTING.get(kit.style.lighting, "studio")
    return f"Background for {kit.copy.business_name}: {tone}, {lighting}..."
```

### Stateless Modules
Each generation module (asset_generator, video_generator) is self-contained:
```python
asset_generator.generate(
    prompt=hero_background(kit),
    config=config,
    output_path=path,
    tracer=tracer,
    step_name="hero-background"
)
```

### Observability
Every step is logged with metadata:
```python
tracer.log(
    step="hero-background",
    provider="gemini",
    model="gemini-2.5-flash",
    prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:12],
    status="success",
    duration_ms=1234,
    output_path=path,
    metadata={"bytes": 123456}
)
```

## Brand Extraction Details

### Pass 1: HTML Parsing
- Extract hex colors from inline styles and CSS
- Find Google Fonts links and CSS font-family declarations
- Scrape meta tags, Open Graph properties, headings, CTAs
- Locate logo, favicon, hero image URLs
- Parse pricing and product information

### Pass 2: AI Enrichment
- Send all HTML signals to Gemini with structured JSON schema
- Synthesize industry, tone, target audience, visual style
- Infer lighting approach, color grade, motion style, photography style
- Generate value propositions if missing

## Critical Rules

### Product Image Integrity
- **NEVER** AI-generate or reimagine a client's product photo
- **ALWAYS** use the real product image supplied by the client
- Generate backgrounds separately, composite product programmatically

### Brand Fidelity
- Extract exact hex colors from client site (not approximations)
- Use client's actual fonts (load via Google Fonts or local files)
- Maintain logo aspect ratio—never stretch or recolor
- Match the visual tone of the client's existing brand

### Technical Standards
- All components: vanilla HTML/CSS/JS, no framework dependencies
- Responsive: mobile-first with desktop enhancement
- Performance: optimized image sizes, GPU-accelerated transforms

## API Costs & Performance

### Typical Run (Full Campaign)
- Brand extraction: ~$0.02 (Gemini reasoning + HTML parsing)
- Hero background: ~$0.04 (Gemini image generation)
- Social ad backgrounds (2x): ~$0.08
- Product keyframe: ~$0.04
- Product video: ~$0.10 (Veo)
- **Total: ~$0.30/run**

### Performance
- Brand extraction: 5-10 seconds
- Image generation: 15-30 seconds per image
- Video generation: 60-120 seconds (polling duration)
- **Full pipeline: 2-3 minutes**

## Troubleshooting

### "GEMINI_API_KEY not configured"
```bash
export GEMINI_API_KEY=your_key_here
python3 pipeline.py --url https://example.com
```

### Video generation times out
Increase polling timeout:
```bash
python3 pipeline.py --url https://example.com --task product-video
```
Veo API can take 120+ seconds. Check `logs/<run-id>-trace.json` for progress.

### Brand extraction missing products
If the website doesn't have clear product sections, the extraction may return empty products list. Use `--task brand-extract` to review the extracted kit and adjust prompts manually if needed.

### Ad copy is too long for format
The `social_ad_copy()` function includes character limits per format:
- Story (9:16): 60-char headline, 120-char subheadline
- Feed (1:1): 50-char headline, 100-char subheadline
- Landscape (16:9): 40-char headline, 80-char subheadline

Adjust in `modules/prompt_engine.py` if needed.

## Development

### Adding a New Generation Task
1. Add function to `pipeline.py`: `def run_my_task(kit, run_dir, config, tracer) -> str`
2. Register in `TASKS` dict
3. Add entry in main CLI handler
4. Implement via stateless modules (asset_generator, video_generator, etc.)

### Adding Prompt Customization
Edit `modules/prompt_engine.py`:
```python
_TONE = {
    "professional": "polished, corporate, high-trust",
    "casual": "friendly, approachable, energetic",
    # Add your tone...
}
```

### Testing
```bash
# Dry run to validate brand extraction and prompts
python3 pipeline.py --url https://example.com --dry-run

# Generate only social ads to save API costs
python3 pipeline.py --url https://example.com --task social-ads
```

## License

MIT

## Support

For issues, feature requests, or contributions, please open an issue or pull request on GitHub.

---

**Built with Claude, Gemini, and Veo.**