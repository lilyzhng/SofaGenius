"""A/B quality harness: pytest entry point.

Runs baseline (anomaly-only) vs candidate (full analysis) code paths
against all synthetic scenarios and asserts quality thresholds.

Run with: python -m pytest tests/test_ab_quality.py -v
"""

import pytest

from tests.ab_harness.code_paths import baseline_code_path, full_analysis_code_path
from tests.ab_harness.report import generate_ab_report, print_report
from tests.ab_harness.runner import run_code_path
from tests.ab_harness.scenarios import ALL_SCENARIOS
from tests.ab_harness.scoring import FLOOR_THRESHOLD, PASS_RATE_THRESHOLD, PASS_THRESHOLD, REGRESSION_TOLERANCE


@pytest.fixture(scope="module")
def ab_reports():
    """Run both code paths once for the entire module."""
    baseline = run_code_path(baseline_code_path, ALL_SCENARIOS, "baseline")
    candidate = run_code_path(full_analysis_code_path, ALL_SCENARIOS, "candidate")
    report = generate_ab_report(baseline, candidate)
    print_report(report)
    return baseline, candidate, report


class TestCandidateQuality:
    """Candidate code path meets absolute quality thresholds."""

    def test_overall_pass_rate(self, ab_reports):
        _, candidate, _ = ab_reports
        assert candidate.pass_rate >= PASS_RATE_THRESHOLD, (
            f"Pass rate {candidate.pass_rate:.1%} < {PASS_RATE_THRESHOLD:.0%}"
        )

    def test_mean_score(self, ab_reports):
        _, candidate, _ = ab_reports
        assert candidate.mean_score >= PASS_THRESHOLD, (
            f"Mean score {candidate.mean_score:.3f} < {PASS_THRESHOLD}"
        )

    def test_no_catastrophic_failures(self, ab_reports):
        _, candidate, _ = ab_reports
        for sr in candidate.scenario_results:
            assert sr.scores.aggregate >= FLOOR_THRESHOLD, (
                f"Scenario '{sr.scenario_name}' scored {sr.scores.aggregate:.3f} < floor {FLOOR_THRESHOLD}"
            )


class TestNoRegressions:
    """Candidate does not regress vs baseline on any scenario."""

    def test_no_scenario_regressions(self, ab_reports):
        _, _, report = ab_reports
        assert not report.regressions, (
            f"Regressions found:\n" + "\n".join(f"  - {r}" for r in report.regressions)
        )

    def test_overall_delta_non_negative(self, ab_reports):
        _, _, report = ab_reports
        assert report.overall_delta >= 0, (
            f"Overall delta {report.overall_delta:+.3f} is negative"
        )


class TestEdgeCaseRobustness:
    """Edge cases (short_run, constant_loss, nan_in_metrics) survive without error."""

    @pytest.mark.parametrize("name", ["short_run", "constant_loss", "nan_in_metrics"])
    def test_robustness_score(self, ab_reports, name):
        _, candidate, _ = ab_reports
        for sr in candidate.scenario_results:
            if sr.scenario_name == name:
                assert sr.scores.robustness == 1.0, (
                    f"Edge case '{name}' robustness={sr.scores.robustness:.3f}, expected 1.0"
                )
                return
        pytest.fail(f"Scenario '{name}' not found in results")


class TestAnomalyDetectionCorrectness:
    """All anomaly-tagged scenarios have correctness >= 0.70."""

    def test_anomaly_scenarios_correctness(self, ab_reports):
        _, candidate, _ = ab_reports
        anomaly_scenarios = [s for s in ALL_SCENARIOS if "anomaly" in s.tags]
        for scenario in anomaly_scenarios:
            for sr in candidate.scenario_results:
                if sr.scenario_name == scenario.name:
                    assert sr.scores.correctness >= 0.70, (
                        f"Anomaly scenario '{scenario.name}' correctness={sr.scores.correctness:.3f} < 0.70"
                    )
                    break
