#!/bin/bash
# Harbor verifier: runs reward_scorer.py and writes reward to /logs/verifier/
set -e

mkdir -p /logs/verifier

python3 /tests/reward_scorer.py \
    --workspace /app \
    --rubric /tests/rubric.json \
    --keywords /tests/keywords.json \
    --output /logs/verifier/reward.txt \
    --output-json /logs/verifier/reward.json
