"""
Generate a visual comparison dashboard for Harbor trial results.

Features:
- Per-criterion PASS (green) / FAIL (red) coloring
- Side-by-side model comparison on the same task
- Agent trajectory steps
- Files created by each agent

Usage:
    python scripts/generate_dashboard.py --jobs-dir jobs/all-runs/ --output dashboard.html
"""

import argparse
import json
from pathlib import Path


def load_trial(job_dir: Path) -> dict | None:
    """Load trial data from a job directory."""
    result_file = job_dir / "result.json"
    if not result_file.exists():
        return None

    with open(result_file) as f:
        result = json.load(f)

    # Find trial dir
    trial_dirs = [d for d in job_dir.iterdir() if d.is_dir() and d.name.startswith(("apex-", "eval-"))]
    if not trial_dirs:
        return None

    trial_dir = trial_dirs[0]
    trial = {"name": job_dir.name, "task": trial_dir.name.rsplit("__", 1)[0]}

    # Verifier reward
    reward_file = trial_dir / "verifier" / "reward.json"
    if reward_file.exists():
        with open(reward_file) as f:
            trial["reward"] = json.load(f)
    else:
        trial["reward"] = {"reward": 0, "reason": "no verifier output"}

    # Agent info
    agents = result.get("stats", {}).get("evals", {})
    trial["agent"] = list(agents.keys())[0] if agents else "unknown"

    # Trajectory
    traj_file = trial_dir / "agent" / "trajectory.json"
    if traj_file.exists():
        with open(traj_file) as f:
            traj = json.load(f)
        steps = []
        for step in traj.get("steps", []):
            for msg in step.get("messages", []):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(
                        c.get("text", "") for c in content if isinstance(c, dict) and c.get("text")
                    )
                if content:
                    steps.append({"role": role, "content": content[:500]})
        trial["steps"] = steps
    else:
        trial["steps"] = []

    return trial


def generate_html(trials: list[dict], output_path: Path):
    """Generate comparison dashboard HTML."""

    # Group trials by task
    tasks = {}
    for t in trials:
        task = t.get("task", "unknown")
        if task not in tasks:
            tasks[task] = []
        tasks[task].append(t)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>APEX Harbor — Evaluation Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 24px; }
h1 { color: #f0f6fc; margin-bottom: 8px; font-size: 24px; }
.subtitle { color: #8b949e; margin-bottom: 32px; font-size: 14px; }
.task-section { margin-bottom: 48px; }
.task-header { color: #58a6ff; font-size: 18px; margin-bottom: 16px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }
.comparison { display: flex; gap: 16px; flex-wrap: wrap; }
.model-card { flex: 1; min-width: 400px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
.model-name { font-size: 16px; font-weight: 600; color: #f0f6fc; margin-bottom: 4px; }
.reward-score { font-size: 32px; font-weight: 700; margin: 12px 0; }
.reward-high { color: #3fb950; }
.reward-mid { color: #d29922; }
.reward-low { color: #f85149; }
.criteria-list { margin-top: 16px; }
.criterion { padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-size: 13px; }
.criterion-pass { background: #0d2818; border-left: 3px solid #3fb950; color: #3fb950; }
.criterion-fail { background: #2d1117; border-left: 3px solid #f85149; color: #f85149; }
.criterion-desc { color: #8b949e; font-size: 12px; margin-top: 2px; }
.method-tag { font-size: 11px; padding: 1px 6px; border-radius: 3px; background: #30363d; color: #8b949e; margin-left: 8px; }
.files-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid #21262d; }
.files-header { font-size: 13px; color: #8b949e; margin-bottom: 6px; }
.file-tag { display: inline-block; font-size: 12px; padding: 2px 8px; margin: 2px; border-radius: 3px; background: #1f2937; color: #7ee787; font-family: monospace; }
.steps-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid #21262d; }
.steps-toggle { font-size: 13px; color: #58a6ff; cursor: pointer; border: none; background: none; }
.steps-content { display: none; margin-top: 8px; max-height: 400px; overflow-y: auto; }
.steps-content.open { display: block; }
.step { padding: 6px 10px; margin: 4px 0; border-radius: 4px; font-size: 12px; font-family: monospace; white-space: pre-wrap; word-break: break-all; }
.step-agent { background: #1c2333; border-left: 2px solid #58a6ff; }
.step-user { background: #1c2320; border-left: 2px solid #3fb950; }
.step-tool { background: #2d2318; border-left: 2px solid #d29922; }
.summary-bar { display: flex; gap: 24px; margin: 16px 0; }
.summary-item { text-align: center; }
.summary-label { font-size: 11px; color: #8b949e; text-transform: uppercase; }
.summary-value { font-size: 20px; font-weight: 600; }
</style>
</head>
<body>
<h1>APEX Harbor — Evaluation Dashboard</h1>
<p class="subtitle">Side-by-side model comparison on professional tasks</p>
"""

    for task_name, task_trials in tasks.items():
        html += f'<div class="task-section">\n'
        html += f'<div class="task-header">{task_name}</div>\n'
        html += '<div class="comparison">\n'

        for trial in sorted(task_trials, key=lambda t: t["name"]):
            reward_data = trial.get("reward", {})
            reward = reward_data.get("reward", 0)
            criteria_met = reward_data.get("criteria_met", 0)
            criteria_total = reward_data.get("criteria_total", 0)
            details = reward_data.get("criteria_details", [])
            files = reward_data.get("files_created", [])

            # Reward color
            if reward >= 0.7:
                color_class = "reward-high"
            elif reward >= 0.3:
                color_class = "reward-mid"
            else:
                color_class = "reward-low"

            html += '<div class="model-card">\n'
            html += f'<div class="model-name">{trial["name"]}</div>\n'
            html += f'<div style="font-size:12px;color:#8b949e">{trial["agent"]}</div>\n'
            html += f'<div class="reward-score {color_class}">{reward}</div>\n'

            # Summary bar
            passed = sum(1 for d in details if d.get("passed"))
            failed = len(details) - passed
            html += '<div class="summary-bar">\n'
            html += f'<div class="summary-item"><div class="summary-value" style="color:#3fb950">{passed}</div><div class="summary-label">Passed</div></div>\n'
            html += f'<div class="summary-item"><div class="summary-value" style="color:#f85149">{failed}</div><div class="summary-label">Failed</div></div>\n'
            html += f'<div class="summary-item"><div class="summary-value" style="color:#8b949e">{criteria_total}</div><div class="summary-label">Total</div></div>\n'
            html += '</div>\n'

            # Per-criterion details
            if details:
                html += '<div class="criteria-list">\n'
                for d in details:
                    status = "pass" if d.get("passed") else "fail"
                    label = "PASS" if d.get("passed") else "FAIL"
                    method = d.get("method", "")
                    desc = d.get("description", "")
                    html += f'<div class="criterion criterion-{status}">\n'
                    html += f'[{label}] {d.get("criterion", "")}'
                    if method and method != "failed":
                        html += f'<span class="method-tag">{method}</span>'
                    html += f'\n<div class="criterion-desc">{desc}</div>\n'
                    html += '</div>\n'
                html += '</div>\n'

            # Files created
            if files:
                html += '<div class="files-section">\n'
                html += '<div class="files-header">Files created by agent:</div>\n'
                for f in files:
                    html += f'<span class="file-tag">{f}</span>\n'
                html += '</div>\n'

            # Trajectory steps (collapsible)
            steps = trial.get("steps", [])
            if steps:
                tid = trial["name"].replace("-", "_")
                html += '<div class="steps-section">\n'
                html += f'<button class="steps-toggle" onclick="document.getElementById(\'steps-{tid}\').classList.toggle(\'open\')">Show {len(steps)} trajectory steps ▼</button>\n'
                html += f'<div id="steps-{tid}" class="steps-content">\n'
                for s in steps[:30]:  # cap at 30
                    role = s.get("role", "")
                    content = s.get("content", "")[:300]
                    role_class = "step-agent" if role == "assistant" else "step-user" if role == "user" else "step-tool"
                    html += f'<div class="step {role_class}">[{role}] {content}</div>\n'
                html += '</div>\n</div>\n'

            html += '</div>\n'  # model-card

        html += '</div>\n</div>\n'  # comparison, task-section

    html += "</body></html>"

    output_path.write_text(html)
    print(f"Dashboard written to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs-dir", type=Path, default=Path("jobs/all-runs"))
    parser.add_argument("--output", type=Path, default=Path("dashboard.html"))
    args = parser.parse_args()

    trials = []
    for job_dir in sorted(args.jobs_dir.iterdir()):
        if not job_dir.is_dir():
            continue
        trial = load_trial(job_dir)
        if trial:
            trials.append(trial)

    print(f"Loaded {len(trials)} trials")
    generate_html(trials, args.output)


if __name__ == "__main__":
    main()
