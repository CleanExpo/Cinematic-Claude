"""
Video Generator — Video generation via Google Veo API.

Supports:
  - Text-to-video (no reference image)
  - Image-to-video (reference_image_path supplied)

Polling is handled internally. Caller gets back a local MP4 path.
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import time
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from modules.config import PipelineConfig
from modules.tracer import PipelineTracer


def generate(
    prompt: str,
    config: PipelineConfig,
    output_path: str,
    tracer: PipelineTracer,
    reference_image_path: Optional[str] = None,
    step_name: Optional[str] = None,
) -> str:
    """
    Generate a video via Veo API.
    Returns output_path on success. Raises on failure.
    """
    t0 = time.time()
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]
    step = step_name or Path(output_path).stem
    mode = "image-to-video" if (reference_image_path and Path(reference_image_path).exists()) else "text-to-video"

    if config.skip_existing and Path(output_path).exists():
        tracer.log(f"{step}-{mode}", "veo", model=config.video_model,
                   prompt_hash=prompt_hash, status="skipped", output_path=output_path)
        return output_path

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.video_model}:predictLongRunning?key={config.gemini_api_key}"
    )

    instance: dict = {"prompt": prompt}

    if mode == "image-to-video":
        with open(reference_image_path, "rb") as f:  # type: ignore[arg-type]
            img_b64 = base64.b64encode(f.read()).decode()
        ext = Path(reference_image_path).suffix.lower().lstrip(".")  # type: ignore[union-attr]
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
        instance["image"] = {"bytesBase64Encoded": img_b64, "mimeType": mime}

    payload = {
        "instances": [instance],
        "parameters": {
            "sampleCount": 1,
            "durationSeconds": config.video_duration,
            "aspectRatio": config.video_aspect_ratio,
        },
    }

    try:
        # ── Submit ────────────────────────────────────────────────────────
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            submit_data = json.loads(resp.read())

        operation = submit_data.get("name")
        if not operation:
            raise ValueError(f"No operation name returned: {submit_data}")

        tracer.log(f"{step}-submit", "veo",
                   model=config.video_model,
                   prompt_hash=prompt_hash,
                   status="submitted",
                   metadata={"operation": operation, "mode": mode})

        # ── Poll ──────────────────────────────────────────────────────────
        poll_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"{operation}?key={config.gemini_api_key}"
        )
        elapsed = 0
        while elapsed < config.max_poll_seconds:
            time.sleep(config.poll_interval)
            elapsed += config.poll_interval

            poll_req = urllib.request.Request(poll_url)
            with urllib.request.urlopen(poll_req, timeout=30) as resp:
                poll_data = json.loads(resp.read())

            if "error" in poll_data:
                raise ValueError(f"Veo reported error: {poll_data['error']}")

            if poll_data.get("done"):
                video_uri = (
                    poll_data.get("response", {})
                    .get("generateVideoResponse", {})
                    .get("generatedSamples", [{}])[0]
                    .get("video", {})
                    .get("uri", "")
                )
                if not video_uri:
                    raise ValueError(f"No video URI in completed response: {poll_data}")

                # ── Download (follow redirects) ───────────────────────────
                video_bytes = _download_with_redirect(
                    f"{video_uri}&key={config.gemini_api_key}"
                )

                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                tracer.log(f"{step}-complete", "veo",
                           model=config.video_model,
                           prompt_hash=prompt_hash,
                           status="success",
                           duration_ms=int((time.time() - t0) * 1000),
                           output_path=output_path,
                           metadata={"bytes": len(video_bytes), "mode": mode})
                return output_path

            pct = min(95, int(elapsed / config.max_poll_seconds * 100))
            print(f"    ⟳ Generating video... {pct}% ({elapsed}s elapsed)", end="\r")

        raise TimeoutError(f"Video generation timed out after {config.max_poll_seconds}s")

    except Exception as exc:
        tracer.log(f"{step}-error", "veo",
                   model=config.video_model,
                   prompt_hash=prompt_hash,
                   status="error",
                   duration_ms=int((time.time() - t0) * 1000),
                   error=str(exc))
        raise


def _download_with_redirect(url: str) -> bytes:
    """
    Download a URL, manually following a single redirect if needed.
    urllib.request follows most redirects, but Veo's signed GCS URLs
    sometimes return a 302 with a body instead of an automatic redirect.
    """
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    # If the response looks like a small JSON error body, try manual redirect
    if len(data) < 1024:
        try:
            err = json.loads(data)
            if "error" in err:
                parsed = urlparse(url)
                conn = http.client.HTTPSConnection(parsed.hostname)  # type: ignore[arg-type]
                conn.request("GET", f"{parsed.path}?{parsed.query}")
                resp2 = conn.getresponse()
                if resp2.status in (301, 302, 307, 308):
                    location = resp2.getheader("Location", "")
                    if location:
                        redirect_req = urllib.request.Request(location)
                        with urllib.request.urlopen(redirect_req, timeout=120) as r:
                            return r.read()
        except (json.JSONDecodeError, Exception):
            pass  # Not a JSON body — return as-is

    return data