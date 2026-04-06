"""
Asset Generator — Image generation via Gemini API.
Stateless. Each call is a complete, self-contained generation.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Optional

from modules.config import PipelineConfig
from modules.tracer import PipelineTracer


def generate(
    prompt: str,
    config: PipelineConfig,
    output_path: str,
    tracer: PipelineTracer,
    step_name: Optional[str] = None,
) -> str:
    """
    Generate a single image via Gemini.
    Returns the output_path on success.
    Raises on failure — caller decides whether to abort or continue.
    """
    t0 = time.time()
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]
    step = step_name or Path(output_path).stem

    # Skip if file exists and skip_existing is set
    if config.skip_existing and Path(output_path).exists():
        tracer.log(step, "gemini", model=config.image_model,
                   prompt_hash=prompt_hash, status="skipped", output_path=output_path)
        return output_path

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.image_model}:generateContent?key={config.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "temperature": config.image_temperature,
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        img_data: Optional[bytes] = None
        for part in (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        ):
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                break

        if not img_data:
            raise ValueError(f"No image in Gemini response. Keys: {list(data.keys())}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_data)

        tracer.log(step, "gemini",
                   model=config.image_model,
                   prompt_hash=prompt_hash,
                   status="success",
                   duration_ms=int((time.time() - t0) * 1000),
                   output_path=output_path,
                   metadata={"bytes": len(img_data)})
        return output_path

    except Exception as exc:
        tracer.log(step, "gemini",
                   model=config.image_model,
                   prompt_hash=prompt_hash,
                   status="error",
                   duration_ms=int((time.time() - t0) * 1000),
                   error=str(exc))
        raise