#!/bin/bash
# Oracle solution — writes gold response directly
cat > /app/answer.txt << 'GOLD_EOF'
{GOLD_RESPONSE}
GOLD_EOF
