---
type: runbook
topic: Setting up a new Claude Code agent on Agent Computer
date: 2026-03-24
author: genius-builder
---

# Agent Computer Setup Guide

How to deploy a Claude Code agent with Discord on Agent Computer. Tested with Jackie on March 24, 2026. Total time: ~20 minutes.

## Prerequisites

- Agent Computer account (sign up at https://www.agentcomputer.ai/login — email-only auth)
- Agent Computer CLI: `npm i -g aicomputer`
- API key (starts with `ac_live_`) from the dashboard
- The agent's Discord bot token
- Claude Code subscription (Claude Max or API key)

## Step 1: Authenticate CLI

```bash
computer login --api-key ac_live_YOUR_KEY
computer whoami  # verify
```

## Step 2: Create the VM

```bash
computer create AGENT_NAME --ssh-enabled --runtime-family managed-worker
```

This creates a managed VM with:
- Ubuntu, Python 3.12, Node 22, Git pre-installed
- Claude Code pre-installed
- Web terminal, VNC desktop, SSH access
- Persistent disk (survives restarts)
- ~15GB RAM, 30GB disk

VM spins up in ~0.3 seconds.

## Step 3: Authenticate Claude Code on the VM

Run from YOUR local machine (opens browser for auth):
```bash
computer claude-login --machine AGENT_NAME
```

Verify:
```bash
ssh -o StrictHostKeyChecking=no -p 443 AGENT_NAME@ssh.agentcomputer.ai 'echo "hello" | claude --print'
```

## Step 4: Install the Discord plugin

From your local machine, install the plugin using Claude Code's plugin installer:

```bash
# SSH into the VM
ssh -o StrictHostKeyChecking=no -p 443 AGENT_NAME@ssh.agentcomputer.ai

# Inside the VM, start claude and install the plugin
claude
# Then in the Claude session:
/plugin install discord@claude-plugins-official
# Exit the session
/exit
```

**Note:** If you need our custom plugin features (create_thread, polls, trustedBots), copy the server.ts from our fork:
```bash
# From local machine — copy our extended server.ts to the VM's plugin cache
# Find the version directory first:
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'ls ~/.claude/plugins/cache/claude-plugins-official/discord/'
# Then copy our version:
cat ~/.claude/plugins/cache/claude-plugins-official/discord/VERSION/server.ts | \
  ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cat > ~/.claude/plugins/cache/claude-plugins-official/discord/VERSION/server.ts'
```

## Step 5: Configure Discord

### Bot token
```bash
# From local machine
ssh -o StrictHostKeyChecking=no -p 443 AGENT_NAME@ssh.agentcomputer.ai 'mkdir -p ~/.claude/channels/discord'
echo "DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN" | \
  ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cat > ~/.claude/channels/discord/.env'
```

### Access control (access.json)

Create locally, then pipe to VM:
```bash
cat > /tmp/access.json << 'EOF'
{
  "dmPolicy": "allowlist",
  "allowFrom": [
    "1413733041842421800",
    "1484459231624302673",
    "1484381532201156658",
    "1485446312798457866"
  ],
  "groups": {
    "*": {
      "requireMention": true,
      "allowFrom": [
        "1413733041842421800",
        "1484459231624302673",
        "1484381532201156658",
        "1485446312798457866"
      ]
    }
  },
  "pending": {},
  "trustedBots": [
    "1484381532201156658",
    "1484459231624302673",
    "1477895765698547844",
    "1485446312798457866"
  ]
}
EOF
cat /tmp/access.json | ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cat > ~/.claude/channels/discord/access.json'
```

Adjust `allowFrom` and `trustedBots` based on which agents should talk to this one.

## Step 6: Set up the agent's workspace

```bash
# SSH into the VM
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai

# Clone the repo
cd /home/node && git clone https://github.com/lilyzhng/SofaGenius.git

# Create agent directory + CLAUDE.md
mkdir -p /home/node/SofaGenius/agents/genius-AGENT_NAME
# Write CLAUDE.md with the agent's identity (see existing agents for format)
```

## Step 7: Create launch script

```bash
cat > /home/node/SofaGenius/agents/genius-AGENT_NAME/launch.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PATH="$HOME/.bun/bin:$PATH"
cd "$SCRIPT_DIR" && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
EOF
chmod +x /home/node/SofaGenius/agents/genius-AGENT_NAME/launch.sh
```

## Step 8: Launch the agent

From the Agent Computer web terminal (https://8788--AGENT_NAME.computer.agentcomputer.ai/):

```bash
bash /home/node/SofaGenius/agents/genius-AGENT_NAME/launch.sh
```

You should see:
```
Listening for channel messages from: plugin:discord@claude-plugins-official
```

Test by @mentioning the agent in Discord.

## Step 9: Set up cron (optional)

```bash
# Install cron on the VM
sudo apt install -y cron
sudo service cron start

# Add cron jobs (times in UTC — PT is UTC-7)
echo "0 14 * * * /path/to/trigger-script.sh >> /tmp/cron.log 2>&1" | crontab -
crontab -l  # verify
```

**Important:** Cron triggers should use a DIFFERENT bot's token to @mention this agent. A bot can't trigger itself via self-mentions.

## Gotchas

1. **SSH quoting** — Complex commands with quotes break over SSH. Write to files locally and pipe: `cat file | ssh ... 'cat > remote_file'`
2. **Plugin auto-update** — On restart, the plugin may auto-update and overwrite custom server.ts. Re-copy our version after restarts.
3. **No SCP** — Agent Computer doesn't support SCP on port 443. Use pipe: `cat local_file | ssh -p 443 ... 'cat > remote_file'`
4. **Process persistence** — The Claude session dies if the web terminal tab closes. Need a process supervisor for true always-on (future improvement).
5. **Self-mention** — Bots ignore their own messages. Cron triggers must use a different bot's token.

## Access

- Dashboard: https://www.agentcomputer.ai/computers
- Web terminal: https://8788--AGENT_NAME.computer.agentcomputer.ai
- SSH: `ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai`
- VNC Desktop: https://6080--AGENT_NAME.computer.agentcomputer.ai

## Cost

$20/mo for 25 VMs. One VM per agent. Current usage: 1/25 (Jackie).
