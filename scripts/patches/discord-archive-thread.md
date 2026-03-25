# Discord Plugin Patch: archive_thread

**Target:** `~/.claude/plugins/cache/claude-plugins-official/discord/0.0.4/server.ts`
**Purpose:** Adds `archive_thread` tool to archive/lock Discord threads.

## How to Apply

This patch modifies the Discord plugin's `server.ts`. Since it lives in the plugin cache (not our repo), it may get overwritten on plugin updates. Re-apply after updates.

### Tool Definition

Add after the `end_poll` tool definition (before the closing `]` of the tools array):

```typescript
    {
      name: 'archive_thread',
      description: 'Archive a Discord thread. Optionally lock it to prevent new messages.',
      inputSchema: {
        type: 'object',
        properties: {
          thread_id: { type: 'string', description: 'The thread channel ID to archive.' },
          locked: { type: 'boolean', description: 'Lock the thread when archiving (default: false).' },
        },
        required: ['thread_id'],
      },
    },
```

### Case Handler

Add before `default:` in the `CallToolRequestSchema` switch:

```typescript
      case 'archive_thread': {
        const ch = await fetchAllowedChannel(args.thread_id as string)
        if (!ch.isThread()) throw new Error('specified channel is not a thread')
        const locked = (args.locked as boolean) ?? false
        await ch.edit({ archived: true, locked })
        return { content: [{ type: 'text', text: `thread archived (id: ${ch.id}${locked ? ', locked' : ''})` }] }
      }
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | string | yes | The thread channel ID to archive |
| `locked` | boolean | no | Lock the thread (prevent new messages). Default: false |

## Notes

- Uses `fetchAllowedChannel()` for access control — respects the team allowlist
- Validates the channel is actually a thread before archiving
- Discord.js `thread.edit({ archived: true })` maps to `PATCH /channels/{id}`
