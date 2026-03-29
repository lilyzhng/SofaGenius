#!/bin/bash
# Trigger Genius Product (Jackie) to run the morning digest.
#
# Uses Jackie's own bot token. Note: self-mentions may not trigger the Discord
# plugin. If that happens, Lily will @mention Jackie manually instead.
JACKIE_BOT_TOKEN="${JACKIE_BOT_TOKEN:?Set JACKIE_BOT_TOKEN env var}"
DAILY_DIGEST_CHANNEL="1485075381613760603"
JACKIE_BOT_ID="1477895765698547844"

curl -sf -H "Content-Type: application/json" \
  -H "Authorization: Bot ${JACKIE_BOT_TOKEN}" \
  -d "{\"content\": \"<@${JACKIE_BOT_ID}> Run the morning builder digest now. Follow the builder-digest skill in your skills/ directory.\"}" \
  "https://discord.com/api/v10/channels/${DAILY_DIGEST_CHANNEL}/messages"
