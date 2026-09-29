"""Render the six-panel Day 13 dashboard from structured JSONL logs.

Usage: python scripts/render_dashboard.py
The generated HTML is self-contained and can be opened locally for evidence.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = ROOT / "submission" / "evidence" / "11-dashboard-overview.html"


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_records() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def dashboard_values(records: list[dict]) -> list[tuple[str, str, str, str]]:
    requests = [record for record in records if record.get("event") == "request_received"]
    responses = [record for record in records if record.get("event") == "response_sent"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latency = [float(record["latency_ms"]) for record in responses if "latency_ms" in record]
    ttft = [float(record["ttft_ms"]) for record in responses if "ttft_ms" in record]
    costs = [float(record.get("cost_usd", 0)) for record in responses]
    tokens_in = sum(int(record.get("tokens_in", 0)) for record in responses)
    tokens_out = sum(int(record.get("tokens_out", 0)) for record in responses)
    quality = [float(record["quality_score"]) for record in responses if "quality_score" in record]
    retrieval = [record["tool_success"] for record in responses if "tool_success" in record]
    error_rate = 100 * len(failures) / len(requests) if requests else 0
    retrieval_rate = 100 * sum(retrieval) / len(retrieval) if retrieval else 0
    return [
        ("Latency percentiles and TTFT", f"P50 {percentile(latency, 50):.0f} · P95 {percentile(latency, 95):.0f} · P99 {percentile(latency, 99):.0f} ms; TTFT P95 {percentile(ttft, 95):.0f} ms", "Threshold: P95 ≤ 3000 ms", "ms"),
        ("Request traffic", f"{len(requests)} requests in the selected 60-minute window", "Threshold: ≥ 1 request/min", "requests/minute"),
        ("Error rate and retrieval success", f"Error rate {error_rate:.1f}% · Retrieval success {retrieval_rate:.1f}%", "Threshold: errors ≤ 2% · retrieval ≥ 90%", "percent"),
        ("Cost over time", f"Total ${sum(costs):.4f} across {len(responses)} responses", "Threshold: total ≤ $2.50", "USD"),
        ("Input and output tokens", f"Input {tokens_in:,} · Output {tokens_out:,}", "Threshold: total ≤ 50,000", "tokens"),
        ("Quality proxy", f"Mean quality {mean(quality):.2f}" if quality else "No response quality data", "Threshold: mean ≥ 0.75", "score 0–1"),
    ]


def main() -> None:
    cards = "".join(
        f"<section><h2>{html.escape(title)}</h2><p class='value'>{html.escape(value)}</p><p>{html.escape(threshold)}</p><small>Unit: {html.escape(unit)}</small></section>"
        for title, value, threshold, unit in dashboard_values(load_records())
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "<!doctype html><meta charset='utf-8'><title>Day 13 Dashboard</title>"
        "<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;margin:32px}"
        "main{max-width:1100px;margin:auto}.meta{color:#94a3b8}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}"
        "section{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px}h2{margin-top:0;font-size:1.05rem}.value{font-size:1.3rem;color:#f8fafc}small{color:#94a3b8}</style>"
        "<main><h1>K4-L3A Monitoring & LLMOps</h1><p class='meta'>Time range: last 60 minutes · Refresh target: 30 seconds · Source: data/logs.jsonl</p>"
        f"<div class='grid'>{cards}</div></main>",
        encoding="utf-8",
    )
    print(f"Dashboard written to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
