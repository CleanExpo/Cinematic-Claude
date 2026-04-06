# Pi CEO Analysis — Cinematic-Claude

Branch: `pidev/analysis-20260406`
Date: 2026-04-06

## Tech Stack
Python 3.10+, Gemini API (gemini-2.5-flash, gemini-2.5-flash-image), Veo API (veo-3.0-fast-generate-001), Kling AI API (kling-v1-5, optional fallback), Pillow>=10.0.0, requests>=2.31.0, Node.js (ESM, orchestrate-pipeline.js only), React (CleanTrust-YZ3500-Social-Post.jsx, standalone demo), Vanilla HTML/CSS/JS (web_builder.py, ad_compositor.py output)

## Quality Scores
| Dimension | Score |
|-----------|-------|
| Completeness | 7/10 |
| Correctness | 6/10 |
| Code Quality | 6/10 |
| Documentation | 8/10 |

## ZTE Maturity
Level 2 — Score: 31/60

## Sprint Plan
### Sprint 1: Foundation Hardening (5d)
- [M] Fix broken regex in brand_extractor.py — malformed continuation patterns at lines with r'<meta[^>]+content=...' chained with raw string breaks (modules/brand_extractor.py ~L90-130)
- [S] Fix _extract_content() logo regex — orphaned group syntax r'<img[^>]+src=...' with unclosed alternation at modules/brand_extractor.py ~L155-165
- [M] Add test suite: pytest unit tests for brand_extractor._extract_colors, _extract_fonts, _extract_meta with fixture HTML files
- [S] Pin all requirements.txt versions — add google-generativeai, add dev deps (pytest, ruff, mypy). Currently only Pillow>=10 and requests>=2.31 declared, but neither is imported in any module
- [S] Remove dead orchestrate-pipeline.py — duplicates pipeline.py with no unique logic; causes confusion about entry point
- [S] Add Makefile / justfile: lint, test, dry-run, full-campaign targets so CI and devs have one canonical invocation

### Sprint 2: Reliability & Observability (5d)
- [M] Add retry logic with exponential back-off to asset_generator.generate() and video_generator.generate() — currently any transient API error is fatal (modules/asset_generator.py L47, modules/video_generator.py L55)
- [M] Decouple video polling into a separate thread with cancel event — current while-loop in video_generator.py L85-120 blocks the process and eats SIGINT
- [S] Add cost_estimate values to all tracer.log() calls — currently the TraceEntry.cost_estimate field (tracer.py L24) is declared but never populated
- [S] Structured JSON logging to stderr (--verbose flag) — current print() calls in PipelineTracer.log() are not machine-parseable
- [S] Add prompt length guard in prompt_engine.py — no validation that generated prompts stay under Gemini/Veo token ceilings

### Sprint 3: Brand Extraction Quality (5d)
- [L] Replace hand-rolled HTML parser in brand_extractor.py with html.parser (stdlib) or BeautifulSoup — current regex on real-world HTML is brittle and already broken in several places
- [L] Add JS-rendered page support via Playwright headless option (behind --js-render flag) — many Shopify/React sites return skeleton HTML to the current urllib fetch
- [S] Add brand kit validation step after AI enrichment — check primary_color is valid hex, fonts are non-empty, products list is sane before saving brand-kit.json
- [S] Cache raw HTML fetch per domain+day to avoid re-fetching on --brand-kit reuse workflows

### Sprint 4: Multimodel Expansion (7d)
- [L] Integrate Kling API from env-local-template.env and orchestrate-pipeline.js into Python pipeline — JWT generation, text2video, image2video, polling (currently JS-only, orphaned from main pipeline)
- [L] Add Anthropic Claude as prompt-engineering agent — use claude-sonnet-4 to auto-refine prompts based on brand kit before sending to Gemini/Veo (ANTHROPIC_API_KEY already in env template)
- [M] Add Shopify Storefront API integration — read live product data (name, price, images, SKU) directly into BrandProduct instead of relying on HTML scrape (SHOPIFY_STOREFRONT_TOKEN already in env template)
- [M] Add Cloudinary/S3 asset hosting option — generated assets are local-only; social posting requires a public URL (config stubs exist in env-local-template.env)

### Sprint 5: Ad & Web Output Quality (5d)
- [S] Replace provider='claude' in ad_compositor.py tracer.log() calls (ad_compositor.py L120) — no Claude API is called there; this is a mislabelled local render step
- [L] Add Pillow-based product compositing in ad_compositor.py — README states 'composite product programmatically' but composite_all() only generates backgrounds; no actual image compositing occurs
- [S] Add Google Fonts preconnect and font-display:swap to web_builder.py output HTML — currently fonts block render (web_builder.py ~L200)
- [S] Add social_links rendering to web_builder.py footer — BrandKit.social_links dict is populated but never rendered in the output page (web_builder.py footer section)
- [S] Add review-dashboard.html trace loader for pipeline.py JSON output — dashboard already supports drag-drop trace JSON (review-dashboard.html L210) but run summary path is not printed as an actionable link

### Sprint 6: Developer Experience & Packaging (4d)
- [S] Add pyproject.toml with [project] metadata, ruff config, mypy config — repo has no build system declaration
- [S] Move env-local-template.env to .env.example (conventional name) and add dotenv loading to pipeline.py so users don't need to manually export vars
- [M] Add GitHub Actions CI: ruff lint + mypy + pytest on push
- [S] Add CONTRIBUTING.md documenting how to add a new task, new provider, and new ad format
