#!/bin/bash
# Trigger Jackie to run the morning digest.
#
# WHY Builder's token? Jackie's Discord plugin only fires on @mentions from
# OTHER bots/users — if Jackie's own token sent the message, the plugin would
# ignore it (self-trigger). Using Builder's token ensures the @mention arrives
# from a different bot identity, which Jackie's plugin picks up and executes.
#
# Trade-off: if Builder's token rotates, this script breaks. Acceptable for now
# because token rotation is manual and rare. A future alternative is a VM-local
# cron that calls `claude --skill builder-digest` directly, bypassing Discord.
BUILDER_BOT_TOKEN="${BUILDER_BOT_TOKEN:?Set BUILDER_BOT_TOKEN env var}"
DAILY_DIGEST_CHANNEL="1485075381613760603"
JACKIE_BOT_ID="1477895765698547844"

curl -sf -H "Content-Type: application/json" \
  -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
  -d "{\"content\": \"<@${JACKIE_BOT_ID}> Run the morning builder digest now. Follow the builder-digest skill in your skills/ directory.\"}" \
  "https://discord.com/api/v10/channels/${DAILY_DIGEST_CHANNEL}/messages"
