# Agent Computer Documentation (Local Reference)

Downloaded: 2026-03-24
Source: https://www.agentcomputer.ai/docs

---

## https://www.agentcomputer.ai/docs (Overview)

**Agent Computer**

"Sub-second cloud agents with a persistent file-systems. Immediately accessible over vnc, ssh and https. Spawn auth gated machines from the CLI, dashboard, or API - connect however you want, publish over HTTPS, and run coding agents on top."

### Start Here

The docs are organized into eight sections:

1. **Overview** - "What Agent Computer is and where to start."
2. **Quickstart** - "Install the CLI, sign in, create a machine, connect, and publish your first app."
3. **Authentication** - "Learn how browser sessions, bearer tokens, and machine auth helpers fit together."
4. **Machines** - "Create, connect, configure, share, and operate your machines from one place."
5. **Agents** - "Run agent sessions on one machine, watch them live, and bridge them through ACP when needed."
6. **Account** - "Manage billing, API keys, SSH keys, and account-level machine defaults."
7. **CLI** - "Every command in the CLI, grouped and scannable."
8. **API overview** - "Read the resource map, auth model, and where to fetch the raw spec."

---

## https://www.agentcomputer.ai/docs/quickstart

### Quick start

This is the fastest path to a working machine. Install the CLI, sign in, create a machine, connect, and publish one app.

### Install

Install the CLI globally with npm. If you use Nix, you can install the CLI from a checkout of this repository.

```
$ npm install -g aicomputer
```

### Sign in

Run `computer login` to open the browser sign-in flow and store a dedicated API key locally for later CLI requests.

```
$ computer login
```

### Create

Create a managed worker when you want the standard terminal, desktop, and agent workflow. Leave the handle blank if you want Agent Computer to generate one for you.

```
$ computer create my-machine
```

### Connect

Use the browser when you want the app surface quickly. Use SSH when you want a terminal-first workflow.

```
$ computer open my-machine
$ computer open my-machine --terminal
$ computer ssh my-machine
```

### Publish

Publish a port when your machine is serving an app you want over HTTPS. If you do not pass a subdomain, Agent Computer uses the port number.

```
$ computer ports publish my-machine 3000
```

That app will be available at `https://3000--my-machine.computer.agentcomputer.ai`.

---

## https://www.agentcomputer.ai/docs/authentication

### Authentication

Agent Computer uses browser sessions for the dashboard and bearer tokens for API and CLI requests. Machine-specific auth helpers build on top of that base account auth.

### Browser sessions

The dashboard uses cookie-backed browser sessions. When you open a machine in the browser from the dashboard or CLI, Agent Computer creates a short-lived access token that is scoped to that machine.

### Bearer tokens

API requests use bearer tokens with the `ac_live_` prefix.

```
Authorization: Bearer ac_live_...
```

### CLI login

Run `computer login` to open the browser flow and create a dedicated local API key for the CLI. If you already have a key, pass it directly instead.

```
computer login
computer login --api-key ac_live_...
```

### Subscription logins

Use these helpers after `computer login` when you want to install local Claude Code or Codex credentials onto a target machine.

```
computer claude-login
computer codex-login
```

`computer claude-login` runs the Claude browser flow and verifies the result on the machine. `computer codex-login` reuses your local Codex login and copies the resulting auth file to the machine.

---

## https://www.agentcomputer.ai/docs/machines

### Machines

Use this page for the full machine lifecycle: creation, connection, image selection, storage mode, sharing, and routine operations.

### Create machines

Users should employ managed workers when they want the platform terminal, desktop, and agent runtime included. For custom solutions, select a custom machine to boot a specific OCI image while controlling the app process independently.

```
$ computer create my-machine
```

The dashboard's new machine flow displays the image source being used, whether the filesystem default is isolated or shared, and an optional workspace name for the canonical `/home/node/workspace-<workspace>` path used by managed workers.

### Connect to machines

Every machine has a primary app URL. Managed workers also expose a platform terminal, a platform desktop, and SSH access when enabled.

```
$ computer open my-machine
$ computer open my-machine --terminal
$ computer open my-machine --vnc
$ computer ssh my-machine
```

Use `computer open` for browser access rather than constructing reserved terminal or desktop URLs manually. Use `computer ssh` to access your machines via SSH.

### Images and filesystem

Managed workers utilize either the platform default image or your saved default machine source. OCI images are the current source format. Only sources in `ready` state qualify as the default for new machines.

```
$ computer image ls
$ computer image save --kind oci-image --requested-ref ghcr.io/acme/worker@sha256:...
$ computer image default <source-id>
$ computer image rebuild <source-id>
```

**Storage Modes:**
- **Isolated mode** assigns each machine its own filesystem.
- **Shared mode** mounts a shared home at `/home/node` and initiates agent sessions in `/home/node/workspace-<workspace>` when shared storage is enabled.

### Share machines

From a machine detail page, you can create an expiring share link or grant browser access by email. Share links are best for quick hand-offs. Email shares are better when you want a named person to open the machine through the normal sign-in flow.

The current UI offers one-hour, twenty-four-hour, and seven-day link expiry windows. You can revoke both link shares and email shares from the same panel.

### Monitor and update

Managed workers expose live CPU, memory, and disk metrics. They also show firmware versions and an update action when a newer managed image is available.

When a machine enters `updating`, Agent Computer rolls the runtime to the latest managed image and refreshes the machine when ready. Status badges and timestamps in the dashboard confirm the machine's lifecycle position.

---

## https://www.agentcomputer.ai/docs/agents

### Agents

Use Agent Computer to run coding agents on one machine, inspect live work on that machine, or expose a remote session through ACP.

### Agent sessions

Start by listing the agents available on a machine, then create or resume a session with the agent, name, and working directory you want to keep stable.

```
$ computer agent agents my-machine

$ computer agent sessions list my-machine

$ computer agent sessions new my-machine --agent codex --name review

$ computer agent prompt my-machine "fix the failing tests" --agent codex --name review

$ computer agent watch my-machine --session <session-id>

$ computer agent status my-machine --session <session-id>
```

If you omit `--cwd`, Agent Computer uses the machine workspace. Managed workers now default to `/home/node/workspace-<workspace>`. Isolated machines may back that path from their private worker data directory. Shared-home machines use the same path inside `/home/node`.

### ACP and skills

Use `computer acp serve` when you want a local ACP client to treat a remote machine agent like a local ACP process.

```
$ computer acp serve my-machine --agent codex --name review

$ npx skills add harivansh-afk/agentcomputer-delegate
```

`computer-acp` is for ACP bridging through `computer acp serve`.

### Runtime (sandbox-agent / Rivet)

**"The agent harness inside every managed worker is built on Rivet's sandbox-agent. It handles process lifecycle, environment setup, and communication between the machine and the Agent Computer control plane."** You do not need to install or configure it yourself -- it ships as part of the managed worker image.

---

## https://www.agentcomputer.ai/docs/account

### Account

Your profile settings control billing, credentials, and the defaults that shape how new managed machines are created.

### Billing

Use the billing section in **Profile** to review your current plan and manage subscription state. If billing is not configured in the current deployment, that section stays informational.

### API Keys

Create API keys when you want scripts, local tools, or external services to call the Agent Computer API directly.

New keys are only shown in full once. Store them when they are created, then use them as bearer tokens for `/v1` requests.

### SSH Keys

Add SSH keys in **Profile** if you want browser-free SSH access or you want multiple devices to connect to the same machines. The CLI can also register a default key for you during `computer ssh`.

### Machine Defaults

Two account-level defaults affect new managed machines: your default machine image source and your filesystem mode. Change them in **Profile** before you create a new machine if you want that machine to inherit a different base image or shared-home behavior.

Disabling shared storage only affects future machines. Existing shared-home machines keep using the shared home until you replace or delete them.

---

## https://www.agentcomputer.ai/docs/cli

### CLI Reference

The CLI command is `computer`. This page provides a grouped, scannable command reference.

### Install and Update

- `npm install -g aicomputer` -- Install the published CLI globally
- `nix profile install 'path:/Users/you/src/agentcomputer/apps/cli#default'` -- Install from local checkout with Nix
- `computer help` -- Read the live command tree on your machine

### Auth Commands

Used for sign in, account inspection, and installing agent credentials on machines:

- `computer login` -- Open browser login flow and store local API key
- `computer login --api-key ac_live_...` -- Direct sign-in with existing API key
- `computer whoami` -- Print current authenticated account
- `computer logout` -- Remove locally stored API key
- `computer claude-login --machine my-machine` -- Run Claude login flow on target machine
- `computer codex-login --machine my-machine` -- Copy local Codex auth state to target machine

### Machine Commands

Create, inspect, list, and delete machines:

- `computer create my-machine` -- Create managed worker with default settings
- `computer create my-machine --use-platform-default` -- Force platform default image
- `computer ls` -- List your machines
- `computer get my-machine` -- Inspect one machine in detail
- `computer rm my-machine` -- Delete one machine

### Image Commands

Manage saved machine sources and default managed-worker image:

- `computer image ls` -- List saved image sources and current default
- `computer image save --kind oci-image --requested-ref ghcr.io/acme/app@sha256:...` -- Save OCI image source
- `computer image default <source-id>` -- Use ready source as default
- `computer image default platform` -- Reset to platform image
- `computer image rebuild <source-id>` -- Start fresh build for source
- `computer image rm <source-id>` -- Delete saved source

### Access Commands

Open browser surfaces, SSH connections, and publish ports:

- `computer open my-machine` -- Open primary app surface
- `computer open my-machine --terminal` -- Open managed terminal
- `computer open my-machine --vnc` -- Open managed desktop
- `computer ssh my-machine` -- Connect over SSH
- `computer ssh --setup` -- Install stable SSH alias
- `computer ports ls my-machine` -- List published ports
- `computer ports publish my-machine 8000 --subdomain api` -- Publish port over HTTPS
- `computer ports rm my-machine 8000` -- Remove published port

### Agent Commands

Inspect installed agents and manage remote sessions:

- `computer agent agents my-machine` -- List installed agents
- `computer agent sessions list my-machine` -- List sessions
- `computer agent sessions new my-machine --agent codex --name review` -- Create/resume named session
- `computer agent prompt my-machine "inspect /home/node/workspace-my-machine" --agent codex --name review` -- Send prompt into session scope
- `computer agent watch my-machine --session <session-id>` -- Stream live session events
- `computer agent status my-machine --session <session-id>` -- Read current session state
- `computer agent cancel my-machine --session <session-id>` -- Cancel active prompt
- `computer agent interrupt my-machine --session <session-id>` -- Interrupt running session without closing
- `computer agent close my-machine --session <session-id>` -- Close one session

### ACP and Tooling

Expose remote agent sessions through local ACP bridge:

- `computer acp serve my-machine --agent codex --name review` -- Bridge remote session to local ACP client
- `computer completion` -- Print shell completion scripts

---

## https://www.agentcomputer.ai/docs/api

### API Reference

The production API is rooted at `https://api.computer.agentcomputer.ai/v1`. All endpoints require bearer auth with an `ac_live_` API key. The raw spec lives at `/openapi.json`.

### Resource Groups

The API is organized into a small set of resource groups that map cleanly to the product.

**Endpoints:**

- `/v1/me`, `/v1/me/filesystem`, and `/v1/me/machine-source` for account defaults.
- `/v1/me/cli-onboarding/*` for first-run CLI setup.
- `/v1/ssh-keys` for SSH credentials.
- `/v1/computers` for machine lifecycle and settings.
- `/v1/computers/{id}/connection`, `/access/*`, `/ports`, and `/shares` for access surfaces.
- `/v1/computers/{id}/agents` and `/agent-sessions/*` for remote agent workflows.
- `/v1/computers/{id}/metrics` and `/firmware/update` for operations.

---

## Key Topics Summary

### Rivet / sandbox-agent
Found on the **Agents** page: "The agent harness inside every managed worker is built on Rivet's sandbox-agent. It handles process lifecycle, environment setup, and communication between the machine and the Agent Computer control plane." It ships pre-installed in the managed worker image.

### Agent Sessions
Sessions are created/resumed via `computer agent sessions new` with `--agent`, `--name`, and optional `--cwd`. You can prompt, watch, check status, cancel, interrupt, and close sessions. Sessions can be bridged to local ACP clients via `computer acp serve`.

### Process Lifecycle
Handled by Rivet's sandbox-agent within managed workers. No explicit auto-restart, daemon mode, keep-alive, or always-on documentation was found in the current docs. The platform manages the agent harness automatically as part of the managed worker image.

### Storage Modes
- **Isolated:** Each machine gets its own filesystem.
- **Shared:** Mounts shared home at `/home/node`, sessions start in `/home/node/workspace-<workspace>`.

### Not Found in Current Docs
The following topics were specifically searched for but **not documented** on the current site:
- Auto-restart / always-on / daemon mode / keep-alive mechanisms
- Detailed sandbox-agent configuration
- Rivet internals beyond the one-sentence mention
