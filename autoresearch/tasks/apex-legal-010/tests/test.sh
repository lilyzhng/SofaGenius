#!/bin/bash
set -Eeuo pipefail

echo "=== APEX-Agents Task Verification ==="

mkdir -p /logs/verifier

# Check answer file exists
if [ ! -f /app/answer.txt ]; then
    echo "Error: /app/answer.txt not found"
    echo '{"reward": 0, "reason": "no answer file"}' > /logs/verifier/reward.json
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi

ANSWER=$(cat /app/answer.txt)
ANSWER_LEN=${#ANSWER}

echo "Answer length: $ANSWER_LEN chars"

# Length check
if [ "$ANSWER_LEN" -lt 50 ]; then
    echo "Answer too short (<50 chars)"
    echo '{"reward": 0, "reason": "answer too short"}' > /logs/verifier/reward.json
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi

# Keyword matching from rubric
KEYWORDS_FILE="/tests/keywords.json"
if [ ! -f "$KEYWORDS_FILE" ]; then
    echo "No keywords file, giving partial credit for non-empty answer"
    echo '{"reward": 0.3, "reason": "no keywords to check, partial credit"}' > /logs/verifier/reward.json
    echo 0.3 > /logs/verifier/reward.txt
    exit 0
fi

# Score keyword coverage with Python
python3 - "$ANSWER" "$KEYWORDS_FILE" <<'PYTHON_EOF'
import json
import sys

answer = sys.argv[1].lower()
keywords = json.load(open(sys.argv[2]))

if not keywords:
    reward = 0.3
    reason = "no keywords extracted from rubric"
else:
    matched = [kw for kw in keywords if kw.lower() in answer]
    coverage = len(matched) / len(keywords)

    # Reward: 0.3 base (for trying) + 0.7 * keyword coverage
    reward = round(0.3 + 0.7 * coverage, 3)
    reason = f"{len(matched)}/{len(keywords)} keywords matched ({coverage:.0%})"

    print(f"Keywords matched: {len(matched)}/{len(keywords)}")
    for kw in matched[:10]:
        print(f"  + {kw}")
    unmatched = [kw for kw in keywords if kw.lower() not in answer]
    for kw in unmatched[:5]:
        print(f"  - {kw}")

result = {"reward": reward, "reason": reason}
print(f"\nReward: {reward}")

with open("/logs/verifier/reward.json", "w") as f:
    json.dump(result, f)
with open("/logs/verifier/reward.txt", "w") as f:
    f.write(str(reward))
PYTHON_EOF

echo "Verification complete."
exit 0
