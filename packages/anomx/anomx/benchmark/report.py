"""Markdown and JSON report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from anomx.benchmark.models import BenchmarkResult


def write_reports(result: BenchmarkResult, output_dir: Path, prefix: str) -> BenchmarkResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{timestamp}.json"
    markdown_path = output_dir / f"{prefix}_{timestamp}.md"

    final = result.model_copy(
        update={"report_json": json_path, "report_markdown": markdown_path},
    )
    json_path.write_text(json.dumps(final.to_dict(), indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(final), encoding="utf-8")
    return final


def _render_markdown(result: BenchmarkResult) -> str:
    lines = [
        "# AnomX Benchmark Report",
        "",
        f"- Generated at: {result.generated_at}",
        f"- Seed: `{result.seed}`",
        f"- Dataset: `{result.dataset_type}`",
        f"- Samples: {result.n_samples} ({result.n_anomalies} injected anomalies)",
        f"- Fit window: {result.fit_samples} samples",
        f"- Duration: {result.duration_hours:.2f} hours",
        "",
        "## Detector Results",
        "",
        "| Detector | Precision | Recall | F1 | FP/h | Fit (ms) | Predict (ms) | ms/sample |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for detector in result.detectors:
        lines.append(
            f"| {detector.name} | {detector.precision:.3f} | {detector.recall:.3f} | "
            f"{detector.f1:.3f} | {detector.false_positives_per_hour:.2f} | "
            f"{detector.latency.fit_ms:.1f} | {detector.latency.predict_ms:.1f} | "
            f"{detector.latency.predict_ms_per_sample:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Protocol Notes",
            "",
            "- Point-level metrics (no event-level tolerance window in MVP).",
            "- Detectors are fit on the first `fit_ratio` fraction, evaluated on the full series.",
            "- Re-run with the same seed to verify reproducibility.",
            "",
        ]
    )
    return "\n".join(lines)
