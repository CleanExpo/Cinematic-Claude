#!/usr/bin/env python3
"""
CleanTrust YZ3500 — Cinematic Pipeline Orchestrator v2
═══════════════════════════════════════════════════════

API-first pipeline. Zero browser automation. Everything runs from the terminal.

Model Stack (April 2026):
  Claude    → Orchestration, prompt engineering, compositing logic
  Gemini    → Image generation (gemini-2.5-flash-image, imagen-4.0)
  Veo       → Video generation (veo-3.0-fast, veo-3.1)
  Kling API → Video generation fallback (kling-v3.0) — requires separate API key

Usage:
  python3 orchestrate-pipeline.py --task pull-apart
  python3 orchestrate-pipeline.py --task hero-video
  python3 orchestrate-pipeline.py --task full-campaign

Prerequisites:
  pip install Pillow requests
  Set GEMINI_API_KEY in environment or .env file
"""

import os
import sys
import json
import time
import base64
import hashlib
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

# ─── CONFIGURATION ───────────────────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """Central config — edit these or override via environment variables."""
    gemini_api_key: str = ""
    kling_access_key: str = ""   # Optional: only if using Kling API
    kling_secret_key: str = ""   # Optional: only if using Kling API

    # Model defaults
    image_model: str = "gemini-2.5-flash-image"
    video_model: str = "veo-3.0-fast-generate-001"
    video_model_fallback: str = "veo-2.0-generate-001"

    # Output settings
    output_dir: str = "./output"
    video_duration: int = 8        # seconds (Veo range: 4-8)
    video_aspect_ratio: str = "16:9"  # 16:9 or 9:16
    image_temperature: float = 0.4

    # Pipeline
    max_poll_seconds: int = 300    # 5 min max wait for video
    poll_interval: int = 5         # seconds between polls

    def __post_init__(self):
        # Load from env if not provided
        self.gemini_api_key = self.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.kling_access_key = self.kling_access_key or os.environ.get("KLING_ACCESS_KEY", "")
        self.kling_secret_key = self.kling_secret_key or os.environ.get("KLING_SECRET_KEY", "")


# ─── TRACE / OBSERVABILITY ──────────────────────────────────────────────────

@dataclass
class TraceEntry:
    timestamp: str
    run_id: str
    step: str
    provider: str
    model: str = ""
    prompt_hash: str = ""
    status: str = ""
    duration_ms: int = 0
    output_path: str = ""
    cost_estimate: str = ""
    error: str = ""
    metadata: dict = field(default_factory=dict)

class PipelineTracer:
    """Structured observability for every generation step."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.entries: list[TraceEntry] = []
        self.start_time = time.time()

    def log(self, step: str, provider: str, **kwargs) -> TraceEntry:
        entry = TraceEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            run_id=self.run_id,
            step=step,
            provider=provider,
            **kwargs
        )
        self.entries.append(entry)
        status_icon = "✓" if entry.status == "success" else "✗" if entry.status == "error" else "⟳"
        print(f"  {status_icon} [{provider}] {step} {f'→ {entry.output_path}' if entry.output_path else ''}")
        if entry.error:
            print(f"    Error: {entry.error}")
        return entry

    def save(self, output_dir: str):
        log_dir = Path(output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{self.run_id}-trace.json"
        with open(log_path, "w") as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)
        elapsed = time.time() - self.start_time
        print(f"\n  Trace log: {log_path}")
        print(f"  Total steps: {len(self.entries)} | Elapsed: {elapsed:.1f}s")
        return log_path


# ─── GEMINI IMAGE GENERATION ────────────────────────────────────────────────

def gemini_generate_image(
    prompt: str,
    config: PipelineConfig,
    output_path: str,
    tracer: PipelineTracer
) -> str:
    """Generate an image via Gemini API. Returns output file path."""
    t0 = time.time()
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.image_model}:generateContent?key={config.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "temperature": config.image_temperature
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        # Extract image from response
        img_data = None
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                break

        if not img_data:
            raise ValueError("No image data in Gemini response")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_data)

        tracer.log("image-generate", "gemini",
                   model=config.image_model,
                   prompt_hash=prompt_hash,
                   status="success",
                   duration_ms=int((time.time()-t0)*1000),
                   output_path=output_path)
        return output_path

    except Exception as e:
        tracer.log("image-generate", "gemini",
                   model=config.image_model,
                   prompt_hash=prompt_hash,
                   status="error",
                   duration_ms=int((time.time()-t0)*1000),
                   error=str(e))
        raise


# ─── VEO VIDEO GENERATION ───────────────────────────────────────────────────

def veo_generate_video(
    prompt: str,
    config: PipelineConfig,
    output_path: str,
    tracer: PipelineTracer,
    reference_image_path: Optional[str] = None,
) -> str:
    """
    Generate video via Google Veo API.
    Supports text-to-video and image-to-video (with reference_image_path).
    Returns output file path.
    """
    t0 = time.time()
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.video_model}:predictLongRunning?key={config.gemini_api_key}"
    )

    # Build instance
    instance = {"prompt": prompt}

    if reference_image_path and Path(reference_image_path).exists():
        with open(reference_image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        # Detect mime type
        ext = Path(reference_image_path).suffix.lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")
        instance["image"] = {"bytesBase64Encoded": img_b64, "mimeType": mime}
        mode = "image-to-video"
    else:
        mode = "text-to-video"

    payload = {
        "instances": [instance],
        "parameters": {
            "sampleCount": 1,
            "durationSeconds": config.video_duration,
            "aspectRatio": config.video_aspect_ratio,
        }
    }

    try:
        # Submit generation
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        operation_name = data.get("name")
        if not operation_name:
            raise ValueError(f"No operation returned: {data}")

        tracer.log(f"video-submit-{mode}", "veo",
                   model=config.video_model,
                   prompt_hash=prompt_hash,
                   status="submitted",
                   metadata={"operation": operation_name, "mode": mode})

        # Poll for completion
        poll_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"{operation_name}?key={config.gemini_api_key}"
        )
        elapsed = 0
        while elapsed < config.max_poll_seconds:
            time.sleep(config.poll_interval)
            elapsed += config.poll_interval

            poll_req = urllib.request.Request(poll_url)
            with urllib.request.urlopen(poll_req, timeout=30) as resp:
                poll_data = json.loads(resp.read())

            if poll_data.get("done"):
                # Extract video URL
                video_uri = (
                    poll_data.get("response", {})
                    .get("generateVideoResponse", {})
                    .get("generatedSamples", [{}])[0]
                    .get("video", {})
                    .get("uri")
                )
                if not video_uri:
                    raise ValueError(f"No video URI in response: {poll_data}")

                # Download video (follow redirects)
                download_url = f"{video_uri}&key={config.gemini_api_key}"
                dl_req = urllib.request.Request(download_url)
                with urllib.request.urlopen(dl_req, timeout=120) as dl_resp:
                    # Handle redirect
                    video_bytes = dl_resp.read()

                # If we got a small JSON error, the redirect wasn't followed
                if len(video_bytes) < 500:
                    try:
                        err_data = json.loads(video_bytes)
                        if "error" in err_data:
                            # Retry with redirect-following approach
                            import http.client
                            from urllib.parse import urlparse
                            parsed = urlparse(download_url)
                            conn = http.client.HTTPSConnection(parsed.hostname)
                            conn.request("GET", f"{parsed.path}?{parsed.query}")
                            resp2 = conn.getresponse()
                            if resp2.status in (301, 302, 307, 308):
                                redirect_url = resp2.getheader("Location")
                                redirect_req = urllib.request.Request(redirect_url)
                                with urllib.request.urlopen(redirect_req, timeout=120) as r:
                                    video_bytes = r.read()
                    except (json.JSONDecodeError, Exception):
                        pass

                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                tracer.log(f"video-complete-{mode}", "veo",
                           model=config.video_model,
                           prompt_hash=prompt_hash,
                           status="success",
                           duration_ms=int((time.time()-t0)*1000),
                           output_path=output_path,
                           metadata={"file_size_bytes": len(video_bytes)})
                return output_path

            # Check for error
            if "error" in poll_data:
                raise ValueError(f"Veo error: {poll_data['error']}")

            # Still processing — show progress
            pct = min(95, int(elapsed / config.max_poll_seconds * 100))
            print(f"    ⟳ Generating... {pct}% ({elapsed}s)", end="\r")

        raise TimeoutError(f"Video generation timed out after {config.max_poll_seconds}s")

    except Exception as e:
        tracer.log(f"video-error-{mode}", "veo",
                   model=config.video_model,
                   prompt_hash=prompt_hash,
                   status="error",
                   duration_ms=int((time.time()-t0)*1000),
                   error=str(e))
        raise


# ─── TASK DEFINITIONS ────────────────────────────────────────────────────────

# Each task is a self-contained generation job with clear inputs and outputs.

TASKS = {
    "pull-apart": {
        "description": "Product disassembly reveal video (START → END keyframe)",
        "steps": [
            {
                "type": "image",
                "id": "start-keyframe",
                "prompt": (
                    "Professional product photography of a pristine handheld ATP "
                    "bioluminescence testing device (luminometer). Rectangular white "
                    "body with rounded edges, 5.5 inch color touchscreen display, "
                    "sample insertion port on top. Device floating centered on solid "
                    "blue (#0073CE) background. Clean studio lighting, slight shadow "
                    "beneath. No text overlays. Photorealistic, 8K quality."
                ),
                "output": "assets/YZ3500-START-keyframe.png",
            },
            {
                "type": "image",
                "id": "end-keyframe",
                "prompt": (
                    "Professional exploded-view product photography of a handheld ATP "
                    "testing device disassembled into 5 floating component layers on "
                    "solid blue (#0073CE) background: (1) outer casing shell at top, "
                    "(2) color touchscreen display module, (3) green circuit board PCB "
                    "with chips, (4) photodiode sensor and lithium battery pack, "
                    "(5) cylindrical testing/reaction chamber at bottom. Components "
                    "arranged vertically with clean spacing. Studio lighting. "
                    "Photorealistic exploded diagram style. 8K quality."
                ),
                "output": "assets/YZ3500-END-keyframe.png",
            },
            {
                "type": "video",
                "id": "pull-apart-video",
                "prompt": (
                    "Smooth cinematic pull-apart animation. The handheld ATP testing "
                    "device slowly and elegantly disassembles in mid-air, revealing "
                    "its internal components one by one. The outer casing separates "
                    "first, then the touchscreen lifts away, followed by the circuit "
                    "board, photodiode sensor, lithium battery, and testing chamber. "
                    "Each component floats apart with precise mechanical motion. Soft "
                    "studio lighting on solid blue background. Steady camera, no "
                    "rotation. Professional product reveal style. Slow, controlled "
                    "motion with subtle depth-of-field."
                ),
                "reference_image": "start-keyframe",
                "output": "video/YZ3500-PullApart.mp4",
            },
        ],
    },
    "hero-video": {
        "description": "Hero product reveal video for social ads",
        "steps": [
            {
                "type": "image",
                "id": "hero-frame",
                "prompt": (
                    "Professional product photography of a premium handheld ATP "
                    "luminometer device. White body, color touchscreen showing test "
                    "results with green pass indicator. Device centered on gradient "
                    "background transitioning from dark navy to CCW blue (#0073CE). "
                    "Dramatic studio lighting with subtle rim light. Photorealistic. 8K."
                ),
                "output": "assets/YZ3500-hero-frame.png",
            },
            {
                "type": "video",
                "id": "hero-reveal",
                "prompt": (
                    "Cinematic product reveal. A premium handheld testing device "
                    "rotates slowly on a dark background. Dramatic studio lighting "
                    "highlights the device contours. The touchscreen glows with test "
                    "result data. Camera slowly orbits 45 degrees. Volumetric light "
                    "rays. Professional commercial quality. Steady, controlled motion."
                ),
                "reference_image": "hero-frame",
                "output": "video/YZ3500-HeroReveal.mp4",
            },
        ],
    },
    "full-campaign": {
        "description": "Complete campaign: keyframes + pull-apart + hero + social variants",
        "steps": [
            # Inherits pull-apart steps then adds hero and social variants
            # (Defined at runtime by combining tasks)
        ],
    },
}


# ─── PIPELINE RUNNER ─────────────────────────────────────────────────────────

def run_task(task_name: str, config: PipelineConfig):
    """Execute a named task through the pipeline."""
    task = TASKS.get(task_name)
    if not task:
        print(f"Unknown task: {task_name}")
        print(f"Available: {', '.join(TASKS.keys())}")
        sys.exit(1)

    run_id = f"ccw-{task_name}-{int(time.time())}"
    tracer = PipelineTracer(run_id)
    output_base = Path(config.output_dir)

    print(f"\n{'═'*60}")
    print(f"  Cinematic Pipeline v2 — API-First")
    print(f"  Task: {task_name} — {task['description']}")
    print(f"  Run:  {run_id}")
    print(f"  Video: {config.video_model} | Image: {config.image_model}")
    print(f"{'═'*60}\n")

    # Handle full-campaign by combining tasks
    steps = task["steps"]
    if task_name == "full-campaign":
        steps = TASKS["pull-apart"]["steps"] + TASKS["hero-video"]["steps"]

    # Track outputs by step ID for cross-referencing
    outputs = {}

    for i, step in enumerate(steps, 1):
        step_type = step["type"]
        step_id = step["id"]
        output_path = str(output_base / step["output"])

        print(f"\n▸ Step {i}/{len(steps)}: {step_id} ({step_type})")

        if step_type == "image":
            result = gemini_generate_image(
                prompt=step["prompt"],
                config=config,
                output_path=output_path,
                tracer=tracer,
            )
            outputs[step_id] = result

        elif step_type == "video":
            ref_image = None
            if "reference_image" in step and step["reference_image"] in outputs:
                ref_image = outputs[step["reference_image"]]

            result = veo_generate_video(
                prompt=step["prompt"],
                config=config,
                output_path=output_path,
                tracer=tracer,
                reference_image_path=ref_image,
            )
            outputs[step_id] = result

    # Save trace
    print(f"\n{'─'*60}")
    tracer.save(config.output_dir)
    print(f"{'═'*60}\n")

    # Summary
    print("  Outputs:")
    for step_id, path in outputs.items():
        size = Path(path).stat().st_size if Path(path).exists() else 0
        size_str = f"{size/1024:.0f}KB" if size < 1_000_000 else f"{size/1_000_000:.1f}MB"
        print(f"    {step_id}: {path} ({size_str})")

    return outputs


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cinematic Pipeline v2 — API-first video + image generation"
    )
    parser.add_argument("--task", required=True, choices=list(TASKS.keys()),
                        help="Which generation task to run")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env)")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--video-model", default="veo-3.0-fast-generate-001",
                        help="Veo model to use")
    parser.add_argument("--duration", type=int, default=8,
                        help="Video duration in seconds (4-8)")
    parser.add_argument("--aspect-ratio", default="16:9",
                        choices=["16:9", "9:16"],
                        help="Video aspect ratio")

    args = parser.parse_args()

    config = PipelineConfig(
        gemini_api_key=args.api_key or os.environ.get("GEMINI_API_KEY", ""),
        output_dir=args.output_dir,
        video_model=args.video_model,
        video_duration=args.duration,
        video_aspect_ratio=args.aspect_ratio,
    )

    if not config.gemini_api_key:
        print("Error: No API key. Set GEMINI_API_KEY or pass --api-key")
        sys.exit(1)

    run_task(args.task, config)


if __name__ == "__main__":
    main()
