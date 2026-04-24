**To:** team@companion.ai (Agent Computer support)
**Subject:** Running Claude Code with --channels as a persistent agent session

Hi team,

I'm running a Claude Code agent on Agent Computer with the Discord MCP plugin. The agent needs to listen for Discord messages 24/7 using:

```
claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
```

This works great from the web terminal, but the session dies when the terminal tab closes.

I tried using `computer agent sessions` to keep it persistent — creating sessions and sending prompts works fine:

```
computer agent sessions new my-machine --agent claude --name discord-bot
computer agent prompt my-machine "hello" --agent claude --name discord-bot
```

But the agent session system doesn't pass the `--channels` flag, so the Discord plugin's MCP server doesn't start and the agent can't listen for Discord messages.

**My question:** Is there a way to run `claude --channels plugin:discord@claude-plugins-official` as a persistent agent session that survives terminal close? Either through:
- A config option to pass extra flags to agent sessions
- A way to run long-lived background processes on managed workers
- Or another approach I'm missing

I've enabled shared filesystem on my account, so all config/plugins persist. The only missing piece is keeping the process alive.

Thanks,
Lily Zhang
lilyzhng.ai@gmail.com
