#!/bin/bash
# Trigger Jackie to run the morning digest
# Uses Builder's bot token so the @mention comes from a different bot
# Jackie's Discord plugin will pick up the mention and run the digest
BUILDER_BOT_TOKEN="${BUILDER_BOT_TOKEN:?Set BUILDER_BOT_TOKEN env var}"
DAILY_DIGEST_CHANNEL="1485075381613760603"
JACKIE_BOT_ID="1477895765698547844"

curl -sf -H "Content-Type: application/json" \
  -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
  -d "{\"content\": \"<@${JACKIE_BOT_ID}> Run the morning builder digest now. Follow the builder-digest skill in your skills/ directory.\"}" \
  "https://discord.com/api/v10/channels/${DAILY_DIGEST_CHANNEL}/messages"
