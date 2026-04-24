# VS Code Terminal Colors Deep Dive - 2026-04-01

**Participants:** Lily + Jackie
**Topic:** Getting Claude Code's terminal colors to match agent computer

---

## Round 1: The Problem

**Lily:** The diff highlight in Claude Code shows mint green (#dcffdc) locally in VS Code. On the agent computer it's a nice dark forest green. I want them to match.

**Jackie:** Tried changing `terminal.ansiGreen` and `terminal.ansiBrightGreen` in VS Code settings.json. Didn't work because Claude Code uses 24-bit truecolor RGB values that bypass the ANSI color palette.

## Round 2: The Wrong Rabbit Holes

**Lily:** Kept trying VS Code terminal settings. Nothing worked.

**Jackie:** Tried multiple approaches that all failed:
- Setting `terminal.ansiGreen` / `terminal.ansiBrightGreen` in Solarized Light/Dark blocks
- Setting `terminal.ansiBlack` / `terminal.ansiBrightBlack` for user input highlight
- Setting `COLORTERM=256color` via VS Code's `terminal.integrated.env.osx` (VS Code overrides it)
- Setting `FORCE_COLOR=2` in .zshrc (didn't affect Claude Code's rendering)
- Switching to "Dark mode (ANSI colors only)" in Claude Code /config (lost the background highlights entirely)

All of these failed because we didn't understand the root cause yet.

## Round 3: Diagnosing from the Agent Computer

**Lily:** Let me just check what the agent computer actually has.

**Jackie:** Ran diagnostics on both machines:

Local VS Code:
- `$COLORTERM` = `truecolor`
- `$TERM` = `xterm-256color`
- `tput colors` = 256

Agent Computer:
- `$COLORTERM` = (empty/unset)
- `$TERM` = `xterm-256color`
- `tput colors` = 256
- `$FORCE_COLOR` = (not set)

**Key finding:** The ONLY difference is `COLORTERM`. When it's `truecolor`, Claude Code's chalk library sends hardcoded 24-bit RGB colors. When it's unset, chalk falls back to 256-color palette, which gives the nicer green.

## Round 4: Two Separate Issues, Two Fixes

**Lily:** I also want the user input line to have a dark background with white text, like the agent computer.

**Jackie:** That turned out to be a separate issue. The user input highlight is controlled by Claude Code's theme setting, not terminal colors.

### Fix 1: User Input Dark Background
Run `/config` in Claude Code, select "Dark mode" (option 1). This gives the dark background on user input with white text.

### Fix 2: Diff Highlight Green Color
Add to `~/.zshrc`:
```bash
# Unset COLORTERM in VS Code so Claude Code uses 256-color palette (matches agent computer)
[[ "$TERM_PROGRAM" == "vscode" ]] && unset COLORTERM
```

**Critical detail:** `unset COLORTERM` works. Setting `COLORTERM=256color` does NOT work. It must be completely unset to match the agent computer behavior.

## Round 5: What We Learned

**Lily:** This took way too long but I'm glad we figured it out.

**Jackie:** Key learnings:
1. Claude Code uses chalk (Node.js library) for terminal colors
2. Chalk checks `COLORTERM` env var. If `truecolor`, it sends 24-bit RGB codes that can't be remapped by VS Code terminal settings
3. VS Code's terminal always sets `COLORTERM=truecolor` for child processes
4. The agent computer's terminal doesn't set `COLORTERM` at all, so chalk defaults to 256-color palette
5. `/config` in Claude Code controls theme (dark/light) independently of the color palette
6. VS Code's `terminal.integrated.env.osx` setting does NOT successfully override `COLORTERM` because VS Code sets it after the env
7. The `.zshrc` `unset` approach works because it runs after VS Code sets the variable

**Also created:** https://github.com/lilyzhng/vscode-settings repo to track VS Code settings (touch_grass theme).
