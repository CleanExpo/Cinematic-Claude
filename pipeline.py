#!/usr/bin/env python3
"""
Cinematic Pipeline — Generic Brand-to-Campaign Generator
═════════════════════════════════════════════════════════

Input any URL. The system extracts brand identity and generates
campaign assets: webpage, social ads, product video.

Usage
─────
  # Full pipeline from a URL
  python3 pipeline.py --url https://ccwonline.com.au

  # Specific task
  python3 pipeline.py --url https://example.com --task webpage
  python3 pipeline.py --url https://example.com --task social-ads
  python3 pipeline.py --url https://example.com --task product-video

  # Skip extraction — use an existing brand kit
  python3 pipeline.py --brand-kit ./runs/example-com-20260406/brand-kit.json

  # Dry run — show extracted brand kit and prompts without generating assets
  python3 pipeline.py --url https://example.com --dry-run

  # Brand extraction only
  python3 pipeline.py --url https://example.com --task brand-extract

Prerequisites
─────────────
  pip install Pillow requests          (Pillow optional, used for future compositing)
  export GEMINI_API_KEY=your_key

Output
──────
  ./runs/<domain>-<timestamp>/
    brand-kit.json       ← Extracted brand data
    index.html           ← Cinematic webpage
    ads/
      <product>-story.html      ← 1080×1920 vertical ad
      <product>-feed.html       ← 1080×1080 square ad
      <product>-landscape.html  ← 1200×628 horizontal ad
    assets/
      hero-background.png
      <product>-keyframe.png
    video/
      <product>-reveal.mp4
    logs/
      <run-id>-trace.json
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from modules.config import PipelineConfig
from modules.tracer import PipelineTracer
from schemas.brand_kit import BrandKit


# ── Task registry ─────────────────────────────────────────────────────────────

TASKS = {
    "brand-extract": "Extract and display brand kit — no asset generation",
    "webpage":       "Generate a cinematic single-page website",
    "social-ads":    "Generate story, feed, and landscape social ad variants",
    "product-video": "Generate a cinematic product reveal video",
    "full-campaign": "Webpage + social ads + product video (default)",
}


# ── Brand kit resolution ──────────────────────────────────────────────────────

def _resolve_kit(args: argparse.Namespace, config: PipelineConfig) -> tuple[BrandKit, str]:
    """
    Return (BrandKit, run_directory).
    Extracts from URL or loads from file depending on args.
    """
    if args.brand_kit:
        print(f"\n  Loading brand kit from {args.brand_kit}")
        kit = BrandKit.from_json(args.brand_kit)
        run_dir = str(Path(args.brand_kit).parent)
        print(f"  ✓ {kit.summary()}")
        return kit, run_dir

    from modules import brand_extractor
    kit = brand_extractor.extract(args.url, config)

    # Create timestamped run directory
    safe = (
        kit.domain.replace("www.", "")
        .replace(".", "-")
        .replace("/", "")
        .strip("-")[:30]
    )
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = str(Path(config.output_dir) / f"{safe}-{ts}")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    kit_path = Path(run_dir) / "brand-kit.json"
    kit.save(str(kit_path))
    print(f"  ✓ Brand kit saved → {kit_path}\n")

    return kit, run_dir


# ── Task runners ──────────────────────────────────────────────────────────────

def run_webpage(
    kit: BrandKit, run_dir: str,
    config: PipelineConfig, tracer: PipelineTracer,
) -> str:
    from modules import asset_generator, web_builder
    from modules.prompt_engine import hero_background

    assets: dict[str, str] = {}

    # Hero background image
    bg_path = str(Path(run_dir) / "assets" / "hero-background.png")
    print("\n  ▸ Generating hero background")
    try:
        result = asset_generator.generate(
            prompt=hero_background(kit),
            config=config,
            output_path=bg_path,
            tracer=tracer,
            step_name="hero-background",
        )
        assets["hero_background"] = result
    except Exception as exc:
        print(f"    ⚠  Background generation failed ({exc}) — using CSS gradient")

    # Assemble HTML
    print("\n  ▸ Assembling webpage")
    page_path = str(Path(run_dir) / "index.html")
    result = web_builder.build(kit, page_path, assets)
    tracer.log("webpage-build", "claude", status="success", output_path=result)
    return result


def run_social_ads(
    kit: BrandKit, run_dir: str,
    config: PipelineConfig, tracer: PipelineTracer,
) -> dict:
    from modules import asset_generator, ad_compositor
    from modules.prompt_engine import product_start_frame, social_background

    outputs: dict = {}
    # Use first two products, or one brand-level pass if no products
    subjects = kit.products[:2] if kit.products else [None]

    for product in subjects:
        label = product.name if product else kit.copy.business_name
        safe = label.lower().replace(" ", "-")[:20]

        # Generate background keyframe for this subject
        print(f"\n  ▸ Generating ad background — {label}")
        bg_path = str(Path(run_dir) / "assets" / f"{safe}-ad-bg.png")
        try:
            prompt = (
                product_start_frame(kit, product)
                if product else social_background(kit, "feed")
            )
            bg = asset_generator.generate(
                prompt=prompt,
                config=config,
                output_path=bg_path,
                tracer=tracer,
                step_name=f"{safe}-bg",
            )
        except Exception as exc:
            print(f"    ⚠  Background failed ({exc}) — ads will use CSS gradient")
            bg = None

        # Composite all three formats
        print(f"\n  ▸ Compositing social ads — {label}")
        ad_outputs = ad_compositor.composite_all(kit, product, bg, run_dir, tracer)
        outputs[label] = ad_outputs

    return outputs


def run_product_video(
    kit: BrandKit, run_dir: str,
    config: PipelineConfig, tracer: PipelineTracer,
) -> str | None:
    from modules import asset_generator, video_generator
    from modules.prompt_engine import product_start_frame, product_reveal_video

    if not kit.products:
        print("\n  ⚠  No products in brand kit — skipping product video")
        return None

    product = kit.products[0]
    safe = product.name.lower().replace(" ", "-")[:20]

    # Keyframe for reference image
    kf_path = str(Path(run_dir) / "assets" / f"{safe}-keyframe.png")
    print(f"\n  ▸ Generating keyframe — {product.name}")
    try:
        kf = asset_generator.generate(
            prompt=product_start_frame(kit, product),
            config=config,
            output_path=kf_path,
            tracer=tracer,
            step_name=f"{safe}-keyframe",
        )
    except Exception as exc:
        print(f"    ⚠  Keyframe failed ({exc}) — video will be text-to-video only")
        kf = None

    # Video
    video_path = str(Path(run_dir) / "video" / f"{safe}-reveal.mp4")
    print(f"\n  ▸ Generating product video — {product.name}")
    try:
        result = video_generator.generate(
            prompt=product_reveal_video(kit, product),
            config=config,
            output_path=video_path,
            tracer=tracer,
            reference_image_path=kf,
            step_name=f"{safe}-video",
        )
        return result
    except Exception as exc:
        print(f"    ✗  Video generation failed: {exc}")
        return None


def run_full_campaign(
    kit: BrandKit, run_dir: str,
    config: PipelineConfig, tracer: PipelineTracer,
) -> dict:
    print(f"\n{'─'*50}")
    print("  Phase 1 / 3 — Webpage")
    page = run_webpage(kit, run_dir, config, tracer)

    print(f"\n{'─'*50}")
    print("  Phase 2 / 3 — Social Ads")
    ads = run_social_ads(kit, run_dir, config, tracer)

    print(f"\n{'─'*50}")
    print("  Phase 3 / 3 — Product Video")
    video = run_product_video(kit, run_dir, config, tracer)

    return {"webpage": page, "ads": ads, "video": video}


# ── Dry run ───────────────────────────────────────────────────────────────────

def dry_run(kit: BrandKit) -> None:
    from modules import prompt_engine
    print(f"\n{'═'*60}")
    print("  DRY RUN — Brand Kit & Prompts")
    print(f"{'═'*60}")
    print(kit.to_json())
    print(f"\n{'─'*60}")
    print("  Generated Prompts")
    print(f"{'─'*60}")
    print(f"\nHero background:\n  {prompt_engine.hero_background(kit)}\n")
    if kit.products:
        p = kit.products[0]
        print(f"Product start frame ({p.name}):\n  {prompt_engine.product_start_frame(kit, p)}\n")
        print(f"Product reveal video ({p.name}):\n  {prompt_engine.product_reveal_video(kit, p)}\n")
    print(f"{'═'*60}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Cinematic Pipeline — URL → brand kit → campaign assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
tasks:
  brand-extract   Extract brand kit and display — no generation
  webpage         Cinematic responsive webpage
  social-ads      Story (9:16), feed (1:1), landscape (1.91:1) ad variants
  product-video   Cinematic product reveal video via Veo API
  full-campaign   All of the above (default)

examples:
  python3 pipeline.py --url https://ccwonline.com.au
  python3 pipeline.py --url https://example.com --task social-ads
  python3 pipeline.py --brand-kit ./runs/example/brand-kit.json --task webpage
  python3 pipeline.py --url https://example.com --dry-run
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", metavar="URL",
                        help="Website URL to extract brand from")
    source.add_argument("--brand-kit", metavar="PATH",
                        help="Path to existing brand-kit.json (skips extraction)")

    parser.add_argument("--task", choices=list(TASKS), default="full-campaign",
                        help="Generation task to run (default: full-campaign)")
    parser.add_argument("--api-key", metavar="KEY",
                        help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--output-dir", metavar="DIR", default="./runs",
                        help="Root output directory (default: ./runs)")
    parser.add_argument("--video-model", default="veo-3.0-fast-generate-001",
                        metavar="MODEL", help="Veo model ID")
    parser.add_argument("--duration", type=int, default=8, metavar="N",
                        help="Video duration in seconds, 4–8 (default: 8)")
    parser.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"],
                        dest="aspect_ratio", help="Video aspect ratio (default: 16:9)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Extract brand kit, print prompts, no generation")
    parser.add_argument("--verbose", action="store_true",
                        help="Show timing and extra detail")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = PipelineConfig(
        gemini_api_key=args.api_key or os.environ.get("GEMINI_API_KEY", ""),
        output_dir=args.output_dir,
        video_model=args.video_model,
        video_duration=args.duration,
        video_aspect_ratio=args.aspect_ratio,
        verbose=args.verbose,
    )

    try:
        config.validate()
    except ValueError as exc:
        print(f"\nConfiguration error: {exc}\n", file=sys.stderr)
        sys.exit(1)

    source = args.url or args.brand_kit
    print(f"\n{'═'*60}")
    print(f"  Cinematic Pipeline — Brand-to-Campaign Generator")
    print(f"  Source:  {source}")
    print(f"  Task:    {args.task} — {TASKS[args.task]}")
    print(f"{'═'*60}")

    # ── Brand extraction ──────────────────────────────────────────────────
    if args.task == "brand-extract":
        if not args.url:
            parser.error("--url is required for brand-extract task")
        from modules import brand_extractor
        kit = brand_extractor.extract(args.url, config)
        print(f"\n{'═'*60}")
        print(kit.to_json())
        return

    print("\n▸ Step 1: Brand Extraction")
    kit, run_dir = _resolve_kit(args, config)

    if args.dry_run:
        dry_run(kit)
        return

    # ── Asset generation ──────────────────────────────────────────────────
    run_id = f"pipeline-{Path(run_dir).name}"
    tracer = PipelineTracer(run_id, verbose=args.verbose)

    print(f"\n▸ Step 2: Asset Generation  (run: {run_id})")

    if args.task == "webpage":
        run_webpage(kit, run_dir, config, tracer)
    elif args.task == "social-ads":
        run_social_ads(kit, run_dir, config, tracer)
    elif args.task == "product-video":
        run_product_video(kit, run_dir, config, tracer)
    else:  # full-campaign
        run_full_campaign(kit, run_dir, config, tracer)

    # ── Trace + summary ───────────────────────────────────────────────────
    tracer.save(run_dir)

    print(f"{'═'*60}")
    print(f"  Output directory: {run_dir}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()