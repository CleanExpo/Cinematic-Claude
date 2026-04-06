"""
Pipeline configuration. Centralised, injectable, no hardcoded values.
"""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class PipelineConfig:
    # ── API credentials ────────────────────────────────────────────────────
    gemini_api_key: str = ""
    kling_access_key: str = ""     # Optional — Kling API fallback
    kling_secret_key: str = ""

    # ── Model selection ────────────────────────────────────────────────────
    image_model: str = "gemini-2.5-flash-image"
    extract_model: str = "gemini-2.5-flash"    # Used for brand extraction reasoning
    video_model: str = "veo-3.0-fast-generate-001"
    video_model_fallback: str = "veo-2.0-generate-001"

    # ── Generation parameters ──────────────────────────────────────────────
    video_duration: int = 8            # Veo range: 4–8
    video_aspect_ratio: str = "16:9"   # 16:9 | 9:16
    image_temperature: float = 0.4

    # ── Pipeline behaviour ─────────────────────────────────────────────────
    output_dir: str = "./runs"
    max_poll_seconds: int = 300        # 5 min ceiling for video polling
    poll_interval: int = 5
    skip_existing: bool = True         # Skip asset if file already exists (resumable runs)
    verbose: bool = False

    def __post_init__(self) -> None:
        """Load from environment if not supplied directly."""
        if not self.gemini_api_key:
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.kling_access_key:
            self.kling_access_key = os.environ.get("KLING_ACCESS_KEY", "")
        if not self.kling_secret_key:
            self.kling_secret_key = os.environ.get("KLING_SECRET_KEY", "")

    def validate(self) -> None:
        """Raise on invalid configuration before any API call is made."""
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required.\n"
                "  Set it in your environment:  export GEMINI_API_KEY=your_key\n"
                "  Or pass it directly:          --api-key your_key"
            )
        if self.video_duration < 4 or self.video_duration > 8:
            raise ValueError(f"video_duration must be 4–8 (got {self.video_duration})")
        if self.video_aspect_ratio not in ("16:9", "9:16"):
            raise ValueError(f"video_aspect_ratio must be 16:9 or 9:16 (got {self.video_aspect_ratio})")