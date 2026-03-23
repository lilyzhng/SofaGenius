"""
Reward scorer for APEX Harbor tasks.

Simplified reward design (from brainstorm 2026-03-22):
  - Correctness: did agent get the right answer? (fuzzy number match + keyword)
  - Tool engagement: did agent use bash tools or just talk?
  - Curiosity bonus: computed at SkyRL training loop level, NOT here

test.sh outputs: correctness score + tool_engaged flag.
SkyRL adds curiosity bonus on top.
"""

import argparse
import json
import re
from pathlib import Path

READABLE_SUFFIXES = {".txt", ".md", ".csv", ".json", ".py", ".sh", ".html", ".xml", ".log"}


# ---------------------------------------------------------------------------
# Text collection
# ---------------------------------------------------------------------------

def collect_workspace_text(workspace: Path) -> str:
    """Read all readable files in workspace into one string."""
    texts = []
    for f in workspace.rglob("*"):
        if f.is_file() and f.suffix in READABLE_SUFFIXES:
            try:
                texts.append(f.read_text(errors="ignore"))
            except Exception:
                pass
    return "\n".join(texts)


def collect_created_files(workspace: Path) -> list[Path]:
    """Find files created by the agent (not in data/)."""
    created = []
    data_dir = workspace / "data"
    for f in workspace.rglob("*"):
        if f.is_file() and not str(f).startswith(str(data_dir)):
            if f.stat().st_size > 50:
                created.append(f)
    return created


# ---------------------------------------------------------------------------
# Criterion checking
# ---------------------------------------------------------------------------

def extract_numbers(text: str) -> list[float]:
    """Extract all numeric values from text."""
    patterns = [
        r'\$[\d,]+\.?\d*',
        r'[\d,]+\.?\d*%',
        r'[\d,]+\.?\d*\s*(?:MM|M|K|B|bn|mn)',
        r'\d+\.\d+',
        r'\d{2,}',
    ]
    numbers = []
    for pat in patterns:
        for match in re.findall(pat, text, re.IGNORECASE):
            cleaned = re.sub(r'[,$%MKBbmn\s]', '', match)
            try:
                numbers.append(float(cleaned))
            except ValueError:
                pass
    return numbers


def fuzzy_number_match(criterion_text: str, agent_text: str,
                       rel_tol: float = 0.05, abs_tol: float = 0.15) -> bool:
    """Check if numbers in criterion appear in agent text within tolerance."""
    criterion_nums = extract_numbers(criterion_text)
    if not criterion_nums:
        return False

    agent_nums = extract_numbers(agent_text)
    if not agent_nums:
        return False

    matched = 0
    for cn in criterion_nums:
        for an in agent_nums:
            if cn == 0 and an == 0:
                matched += 1
                break
            elif cn != 0:
                if abs(an - cn) / abs(cn) <= rel_tol:
                    matched += 1
                    break
            elif abs(an - cn) <= abs_tol:
                matched += 1
                break

    return matched >= len(criterion_nums) * 0.5


def keyword_match(keywords: list[str], agent_text: str) -> float:
    """Fraction of keywords found in agent text."""
    if not keywords:
        return 0.0
    agent_lower = agent_text.lower()
    matched = sum(1 for kw in keywords if kw.lower() in agent_lower)
    return matched / len(keywords)


def check_criteria(rubric: dict, agent_text: str) -> tuple[int, int, list[dict]]:
    """Check how many rubric criteria are met.

    Returns (met, total, details) where details is a list of per-criterion results.
    """
    total = len(rubric)
    met = 0
    details = []

    for key, criterion in rubric.items():
        desc = criterion.get("description", "") if isinstance(criterion, dict) else str(criterion)

        result = {"criterion": key, "description": desc[:200], "passed": False, "method": "none"}

        # Extract expected numbers for analysis
        expected_nums = extract_numbers(desc)
        agent_nums_nearby = []

        # Try fuzzy number match first
        if fuzzy_number_match(desc, agent_text):
            met += 1
            result["passed"] = True
            result["method"] = "number_match"
            details.append(result)
            continue

        # Fallback: keyword match
        terms = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', desc)
        terms += re.findall(r'"([^"]+)"', desc)
        terms += re.findall(r'\b[A-Z]{2,6}\b', desc)
        if terms and keyword_match(terms, agent_text) >= 0.5:
            met += 1
            result["passed"] = True
            result["method"] = "keyword_match"
        else:
            result["method"] = "failed"
            # Analyze WHY it failed
            if expected_nums:
                all_agent_nums = extract_numbers(agent_text)
                # Find closest agent number to expected
                for en in expected_nums[:3]:
                    closest = None
                    closest_diff = float("inf")
                    for an in all_agent_nums:
                        diff = abs(an - en) / max(abs(en), 0.01)
                        if diff < closest_diff:
                            closest = an
                            closest_diff = diff
                    if closest is not None:
                        agent_nums_nearby.append({"expected": en, "agent_got": closest, "diff_pct": round(closest_diff * 100, 1)})
                if agent_nums_nearby:
                    result["analysis"] = f"Expected {expected_nums[0]}, closest agent value: {agent_nums_nearby[0]['agent_got']} ({agent_nums_nearby[0]['diff_pct']}% off)"
                else:
                    result["analysis"] = f"Expected numbers like {expected_nums[0]}, but none found in agent output"
            else:
                matched_terms = [t for t in terms if t.lower() in agent_text.lower()] if terms else []
                result["analysis"] = f"Matched {len(matched_terms)}/{len(terms)} keywords" if terms else "No matching signals found"

        details.append(result)

    return met, total, details


# ---------------------------------------------------------------------------
# Main scoring
# ---------------------------------------------------------------------------

def compute_reward(workspace: Path, rubric: dict, keywords: list[str]) -> dict:
    """Compute reward for a Harbor task.

    Simple design:
      - Correctness: criteria_met / criteria_total (gated by file existence)
      - Tool engaged: did agent create any output files?

    Curiosity bonus is added at the SkyRL training loop level.
    """
    agent_text = collect_workspace_text(workspace)

    # File existence gate — agent must create output
    created = collect_created_files(workspace)
    file_exists = len(created) > 0

    if not file_exists:
        return {
            "reward": 0.0,
            "reason": "No output files created",
            "file_exists": False,
            "correctness": 0.0,
            "criteria_met": 0,
            "criteria_total": len(rubric),
            "tool_engaged": False,
        }

    # Correctness: what fraction of criteria did agent meet?
    criteria_met, criteria_total, criteria_details = check_criteria(rubric, agent_text)
    correctness = criteria_met / max(criteria_total, 1)

    # Tool engaged: agent created files (not just talked)
    tool_engaged = True  # if we got here, file_exists = True

    # Files created by agent
    created_names = [f.name for f in created]

    reward = correctness

    return {
        "reward": round(reward, 4),
        "reason": f"criteria {criteria_met}/{criteria_total}",
        "file_exists": True,
        "correctness": round(correctness, 4),
        "criteria_met": criteria_met,
        "criteria_total": criteria_total,
        "tool_engaged": tool_engaged,
        "files_created": created_names,
        "criteria_details": criteria_details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--keywords", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    with open(args.rubric) as f:
        rubric = json.load(f)

    with open(args.keywords) as f:
        keywords = json.load(f)

    result = compute_reward(args.workspace, rubric, keywords)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(str(result["reward"]))

    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

    # Print detailed breakdown to stdout (shows in Harbor Verifier Logs tab)
    print(f"Reward: {result['reward']} — {result['reason']}")
    print()
    if result.get("files_created"):
        print(f"Files created: {', '.join(result['files_created'])}")
        print()
    if result.get("criteria_details"):
        print("Per-criterion breakdown:")
        for c in result["criteria_details"]:
            status = "PASS" if c["passed"] else "FAIL"
            print(f"  [{status}] {c['criterion']} ({c['method']})")
            print(f"         {c['description']}")
            if c.get("analysis"):
                print(f"         → {c['analysis']}")
        print()
        passed = sum(1 for c in result["criteria_details"] if c["passed"])
        failed = sum(1 for c in result["criteria_details"] if not c["passed"])
        print(f"Summary: {passed} passed, {failed} failed")


if __name__ == "__main__":
    main()
