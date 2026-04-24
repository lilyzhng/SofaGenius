**Reply to Hari @ Agent Computer**

Hi Hari,

Thanks for the quick response! The nohup approach works — with one small tweak. Claude Code needs a PTY, so we wrapped it with `script`:

```bash
nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
```

This survives closing the browser tab and SSH disconnect. Our Discord bot is running in the background now.

We're currently validating if the process stays alive for 16+ hours. Previously (with the tab open), our session died after ~8 hours. We'll report back on the persistence test.

One question: is there anything on your platform side that would kill a long-running background process? (VM maintenance, idle timeout, resource limits, etc.)

Thanks,
Lily
