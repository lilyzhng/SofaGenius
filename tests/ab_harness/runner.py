"""Execute a code path against all scenarios and collect timed results."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from .scenarios import Scenario
from .scoring import AnalysisResult, DimensionScores, score_scenario


@dataclass
class ScenarioResult:
    """Result for a single scenario within a code path run."""

    scenario_name: str
    result: AnalysisResult
    scores: DimensionScores


@dataclass
class CodePathReport:
    """Aggregated report for running one code path against all scenarios."""

    label: str
    scenario_results: list[ScenarioResult] = field(default_factory=list)

    @property
    def mean_score(self) -> float:
        if not self.scenario_results:
            return 0.0
        return sum(r.scores.aggregate for r in self.scenario_results) / len(self.scenario_results)

    @property
    def pass_rate(self) -> float:
        if not self.scenario_results:
            return 0.0
        from .scoring import PASS_THRESHOLD
        passed = sum(1 for r in self.scenario_results if r.scores.aggregate >= PASS_THRESHOLD)
        return passed / len(self.scenario_results)

    def score_for(self, scenario_name: str) -> float | None:
        for r in self.scenario_results:
            if r.scenario_name == scenario_name:
                return r.scores.aggregate
        return None


def run_code_path(
    path_fn: Callable[[Scenario], AnalysisResult],
    scenarios: list[Scenario],
    label: str,
) -> CodePathReport:
    """Execute a code path against all scenarios, timing each run."""
    report = CodePathReport(label=label)

    for scenario in scenarios:
        start = time.perf_counter()
        try:
            result = path_fn(scenario)
        except Exception as e:
            from backend.models import RunInsights
            result = AnalysisResult(
                anomaly_types=[],
                anomaly_count=0,
                insights=RunInsights(
                    trend_summary="",
                    metric_stats=[],
                    phases=[],
                    convergence=None,
                    lr_analysis=None,
                ),
                elapsed_ms=0.0,
                error=str(e),
            )
        elapsed = (time.perf_counter() - start) * 1000
        result.elapsed_ms = elapsed

        scores = score_scenario(scenario, result)
        report.scenario_results.append(ScenarioResult(
            scenario_name=scenario.name,
            result=result,
            scores=scores,
        ))

    return report
