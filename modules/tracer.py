"""
Pipeline tracer — structured, per-run observability.

Every generation step emits a TraceEntry. Entries accumulate in PipelineTracer
and are flushed to a JSON log at the end of each run. The review-dashboard.html
can ingest these files directly.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass
class TraceEntry:
    timestamp: str
    run_id: str
    step: str
    provider: str          # gemini | veo | claude | kling | system
    model: str = ""
    prompt_hash: str = ""  # First 12 chars of SHA-256(prompt)
    status: str = ""       # submitted | success | error | skipped
    duration_ms: int = 0
    output_path: str = ""
    cost_estimate: str = ""
    error: str = ""
    metadata: dict = field(default_factory=dict)


class PipelineTracer:
    """
    Accumulates trace entries for a single run.
    Thread-safe enough for sequential pipeline use.
    """

    ICONS = {"success": "✓", "error": "✗", "skipped": "⊘", "submitted": "→"}

    def __init__(self, run_id: str, verbose: bool = False) -> None:
        self.run_id = run_id
        self.verbose = verbose
        self.entries: List[TraceEntry] = []
        self._start = time.time()

    def log(self, step: str, provider: str, **kwargs) -> TraceEntry:
        entry = TraceEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            run_id=self.run_id,
            step=step,
            provider=provider,
            **kwargs,
        )
        self.entries.append(entry)

        icon = self.ICONS.get(entry.status, "⟳")
        path_part = f" → {entry.output_path}" if entry.output_path else ""
        dur_part = f" ({entry.duration_ms}ms)" if entry.duration_ms and self.verbose else ""
        print(f"    {icon} [{provider}] {step}{path_part}{dur_part}")
        if entry.error:
            print(f"      ⚠  {entry.error}")

        return entry

    def save(self, output_dir: str) -> Path:
        log_dir = Path(output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{self.run_id}-trace.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)

        elapsed = time.time() - self._start
        successes = sum(1 for e in self.entries if e.status == "success")
        errors = sum(1 for e in self.entries if e.status == "error")
        skipped = sum(1 for e in self.entries if e.status == "skipped")

        print(f"\n  ─── Run Summary ──────────────────────────────────")
        print(f"  Steps:    {len(self.entries)}  "
              f"(✓ {successes}  ✗ {errors}  ⊘ {skipped})")
        print(f"  Elapsed:  {elapsed:.1f}s")
        print(f"  Trace:    {log_path}")
        print(f"  ─────────────────────────────────────────────────\n")

        return log_path

    @property
    def elapsed(self) -> float:
        return time.time() - self._start