# Jackie Voice Test Script

Ask these questions in order. Record Jackie's responses to compare across iterations.

---

## Test 1: Greeting (natural, not robotic)
**You say:** (just pick up the phone, don't say anything for 2 seconds)

**What to check:**
- Does Jackie greet naturally? (not too long, not too short)
- Does he sound like a person, not a customer service bot?

**Previous result (2026-04-01):** "Hey Lily, what's up?" (good)

---

## Test 2: Simple tool request (web_search via use_cli)
**You say:** "帮我查一下明天San Mateo的天气"

**What to check:**
- Does Jackie try the tool immediately, or refuse first?
- Does he say "let me check" before the pause?
- Is the answer concise? (temperature + conditions, not a weather essay)

**Previous result (2026-04-01):** Refused first, needed prompting. Then: "High 67, low 48, partly sunny with afternoon rain likely, so bring an umbrella." (good answer once he tried)

---

## Test 3: Follow-up question (not passive)
**You say:** "那后天呢?"

**What to check:**
- Does Jackie understand the context (weather, same location)?
- Does he give a real answer, not just "yes" or "got it"?

**Previous result:** N/A (new test)

---

## Test 4: Listening mode (not too passive, not too verbose)
**You say:** "我跟你说一下今天发生的事情。今天我开了三个会,第一个是跟team讨论product roadmap,第二个是one-on-one,第三个是关于hiring的。"

**What to check:**
- Does Jackie let you finish without interrupting?
- Does he respond with something natural, NOT repeat/summarize what you said?
- Does he ask a question or add something useful?

**Bad response:** "听起来你今天很忙,开了三个会,一个是roadmap,一个是one-on-one,一个是hiring。"
**Good response:** "Which one do you want to talk about?" or "How'd the hiring one go?"

**Previous result (2026-04-01):** Too passive, just said "yes" or "got it"

---

## Test 5: Memory search
**You say:** "你还记得我的career goal是什么吗?"

**What to check:**
- Does Jackie search memory (read_memory) before answering?
- Does he find the right info? (post-training RE role for coding agents)
- Does he say "let me think" or "give me a sec" before searching?

**Previous result:** N/A (new test)

---

## Test 6: Opinion / push back (not a yes-man)
**You say:** "我在想要不要把所有agent都换成用GPT,你觉得呢?"

**What to check:**
- Does Jackie give his own opinion?
- Does he push back or ask a sharp question?
- Is it a real response, not just agreement?

**Bad response:** "好啊,可以试试看。"
**Good response:** "For what reason? Claude's working fine for the heavy lifting. What's GPT doing better right now?"

**Previous result (2026-04-01):** N/A (new test)

---

## Test 7: Barge-in (natural interruption)
**You say:** Wait for Jackie to give a longer response, then interrupt mid-sentence with "等一下"

**What to check:**
- Does Jackie stop immediately?
- Does the audio cut feel natural (trails off) or abrupt?
- Does background noise trigger false interrupts?

**Previous result (2026-04-01):** N/A (new test)

---

## Test 8: "Just listen" mode
**You say:** "你先别说话,听我说就好"

**What to check:**
- Does Jackie keep it to 1-2 words? ("Got it." not "好的,我会安静听你说...")
- When you pause, does he stay quiet or jump in?

**Previous result (2026-04-01):** N/A (new test)

---

## Scoring

For each test, rate 1-5:
- 1 = broken (refused, crashed, nonsensical)
- 2 = bad (verbose, passive, or wrong behavior)
- 3 = acceptable but not great
- 4 = good, natural
- 5 = perfect, exactly what you'd want

| Test | Date: _____ | Date: _____ | Date: _____ |
|------|-------------|-------------|-------------|
| 1. Greeting | | | |
| 2. Weather lookup | | | |
| 3. Follow-up | | | |
| 4. Listening mode | | | |
| 5. Memory search | | | |
| 6. Opinion | | | |
| 7. Barge-in | | | |
| 8. Just listen | | | |
| **Total** | | | |
