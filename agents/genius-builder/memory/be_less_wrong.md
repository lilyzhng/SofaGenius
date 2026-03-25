# Lessons Learned

> "Be less wrong. It's hard to be 100% right, but you can at least try to be less wrong." — Lily

---

## 1. The PATH Debugging Disaster (2026-03-25)

**Mistake:** Spent hours debugging why agents couldn't launch on the cloud VM. Proposed separate config directories, separate machines, env var overrides, plugin reinstalls — all unnecessary. The fix was one line: `export PATH="$HOME/.bun/bin:$PATH"`.

**What I did wrong:**
- Didn't read the existing working code first. Jackie's launch script already had the PATH fix.
- Panicked and jumped to complex solutions instead of checking the simplest cause.
- Changed multiple things at once, making it impossible to isolate the real problem.
- Didn't do a controlled experiment — no A/B testing, no isolating variables.

**What I should have done:**
1. Start with the control: Jackie works on laptop. What's the same? What's different on VM?
2. Change one variable at a time. Move to VM → test. Passes? Move on. Fails? Isolate.
3. Check the simplest hypothesis first: `which bun` → not found → PATH issue → done.
4. Read what's already working before proposing anything new.

**Pattern to follow:** One change, one test, observe. If it doesn't explain the problem, revert and try the next hypothesis. Never stack unverified changes.

---

## 2. Going Silent While Doing Heavy Work (2026-03-25)

**Mistake:** Lily tagged me for a 1:1 in a thread. I was busy researching `archive_thread` and didn't respond. Then replied in the wrong channel.

**What I did wrong:**
- Did heavy work sequentially in my own context instead of delegating to a background subagent.
- Blocked myself from responding to messages.
- Replied in the parent channel instead of the thread where Lily was waiting.

**What I should have done:**
1. Kick off heavy work as a background subagent immediately.
2. Stay free to respond to messages.
3. Always check the `chat_id` of incoming messages — reply where the message came from.

**Pattern to follow:** Be a dispatcher, not a worker. Background subagents have the same tools. Never block yourself on sequential work.

---

## 3. Not Merging My Own PR After Approval (2026-03-25)

**Mistake:** Lily approved PR #58 and had to merge it herself. I was sitting idle instead of monitoring for approvals.

**What I did wrong:**
- Treated "waiting for review" as idle time instead of monitoring the PR.
- Didn't use a background subagent to watch for approval notifications.

**What I should have done:**
- After raising a PR, stay aware of its status. When approval comes in, merge immediately.
- The PR workflow says: approval bot notification IS the trigger to merge. Don't wait for a separate instruction.

**Pattern to follow:** Own the full PR lifecycle. Raising it is not the end — merging after approval is.
