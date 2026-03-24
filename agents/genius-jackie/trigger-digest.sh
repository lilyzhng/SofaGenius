#!/bin/bash
# Trigger Jackie to run the morning digest.
#
# WHY Lily's token? Jackie's Discord plugin only fires on @mentions from
# OTHER bots/users — if Jackie's own token sent the message, the plugin would
# ignore it (self-trigger). Using Lily's bot token means the @mention arrives
# from Lily's bot identity, which is natural ("Lily asks Jackie to do the
# digest") and avoids coupling this cron to another agent's token.
LILY_BOT_TOKEN="${LILY_BOT_TOKEN:?Set LILY_BOT_TOKEN env var}"
DAILY_DIGEST_CHANNEL="1485075381613760603"
JACKIE_BOT_ID="1477895765698547844"

curl -sf -H "Content-Type: application/json" \
  -H "Authorization: Bot ${LILY_BOT_TOKEN}" \
  -d "{\"content\": \"<@${JACKIE_BOT_ID}> Run the morning builder digest now. Follow the builder-digest skill in your skills/ directory.\"}" \
  "https://discord.com/api/v10/channels/${DAILY_DIGEST_CHANNEL}/messages"
