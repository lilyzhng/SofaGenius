"""A/B comparison report generation and formatting."""

from __future__ import annotations

from dataclasses import dataclass, field

from .runner import CodePathReport
from .scoring import REGRESSION_TOLERANCE


@dataclass
class ABReport:
    """Comparison report between baseline and candidate code paths."""

    baseline: CodePathReport
    candidate: CodePathReport
    regressions: list[str] = field(default_factory=list)
    overall_delta: float = 0.0
    verdict: str = ""


def generate_ab_report(baseline: CodePathReport, candidate: CodePathReport) -> ABReport:
    """Compare baseline vs candidate and produce a verdict."""
    regressions: list[str] = []

    for br in baseline.scenario_results:
        cr_score = candidate.score_for(br.scenario_name)
        if cr_score is None:
            continue
        delta = cr_score - br.scores.aggregate
        if delta < -REGRESSION_TOLERANCE:
            regressions.append(
                f"{br.scenario_name}: baseline={br.scores.aggregate:.3f} candidate={cr_score:.3f} (delta={delta:+.3f})"
            )

    overall_delta = candidate.mean_score - baseline.mean_score

    if regressions:
        verdict = f"REGRESSIONS DETECTED ({len(regressions)} scenario(s))"
    elif overall_delta >= 0:
        verdict = f"PASS - candidate scores {overall_delta:+.3f} vs baseline"
    else:
        verdict = f"MARGINAL - candidate scores {overall_delta:+.3f} vs baseline (within tolerance)"

    return ABReport(
        baseline=baseline,
        candidate=candidate,
        regressions=regressions,
        overall_delta=overall_delta,
        verdict=verdict,
    )


def print_report(report: ABReport) -> str:
    """Format a human-readable comparison report. Returns the formatted string."""
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("A/B Quality Comparison Report")
    lines.append("=" * 78)
    lines.append("")

    # Header
    lines.append(f"{'Scenario':<30} {'Baseline':>10} {'Candidate':>10} {'Delta':>10}")
    lines.append("-" * 62)

    for br in report.baseline.scenario_results:
        cr_score = report.candidate.score_for(br.scenario_name)
        if cr_score is None:
            continue
        delta = cr_score - br.scores.aggregate
        marker = " <<" if delta < -REGRESSION_TOLERANCE else ""
        lines.append(
            f"{br.scenario_name:<30} {br.scores.aggregate:>10.3f} {cr_score:>10.3f} {delta:>+10.3f}{marker}"
        )

    lines.append("-" * 62)
    lines.append(
        f"{'MEAN':<30} {report.baseline.mean_score:>10.3f} {report.candidate.mean_score:>10.3f} {report.overall_delta:>+10.3f}"
    )
    lines.append(
        f"{'PASS RATE':<30} {report.baseline.pass_rate:>10.1%} {report.candidate.pass_rate:>10.1%}"
    )
    lines.append("")

    if report.regressions:
        lines.append("REGRESSIONS:")
        for r in report.regressions:
            lines.append(f"  - {r}")
        lines.append("")

    lines.append(f"VERDICT: {report.verdict}")
    lines.append("=" * 78)

    output = "\n".join(lines)
    print(output)
    return output
