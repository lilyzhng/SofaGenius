# Data + Eval Agent — Design Doc

**Status:** Draft skeleton — pending Lily's debrief from Cortex Code event
**Date:** 2026-03-27
**Authors:** Researcher (research section), Builder (architecture section), Jackie (UX section)

---

## 1. Vision

A standalone data agent product that explores, queries, and analyzes data — with built-in self-verification. The agent doesn't just give answers; it checks if they're correct. This is the trust layer enterprise customers are missing.

**Differentiator:** Every existing data agent (Snowflake Cortex, Defog, Vanna, ThoughtSpot) generates answers but does NOT verify them. Eval platforms (Braintrust, Galileo) verify but are separate products. We merge them into one.

---

## 2. Research Section (Researcher)

### 2.1 Competitive Landscape

| Product | What it does | Pricing | Eval layer? | Lock-in |
|---------|-------------|---------|-------------|---------|
| Snowflake Cortex Code | AI coding agent for Snowflake (SQL, dbt, Streamlit) | $20/mo + tokens | No | Snowflake |
| Defog.ai | Fine-tuned text-to-SQL (SQLCoder) | From $599/mo | Dev-time only | None |
| Vanna.ai | Open-source text-to-SQL via RAG | Open-core | No | None |
| Databricks Genie | Multi-step analytics + data engineering | Consumption-based | Building it (acquired Quotient AI) | Databricks |
| ThoughtSpot Spotter | AI analytics agents suite | $25-50/user/mo | No | ThoughtSpot |
| Wren AI | Open-source Generative BI with semantic layer | Open-core | No | None |

**Key finding:** Only Databricks is merging eval into their data agent (via Quotient AI acquisition, March 2026). Everyone else leaves verification to the user.

### 2.2 Market Size

- Data Analytics: $104B (2026), growing to $786B by 2035 (28% CAGR)
- AI Agents: $10.9B (2026), growing to $183B by 2033 (49.6% CAGR)
- Eval ecosystem is hot: Braintrust ($80M Series B), Galileo (acquired by Alphabet), Quotient AI (acquired by Databricks)

### 2.3 Customer Pain Points (ranked)

1. **Data trust is #1 blocker to AI adoption** — cited 2x more than any other concern
2. Data quality — 64% cite as top integrity challenge
3. Tool stack complexity — orgs manage 5-7+ tools
4. AI hallucinations — growing concern
5. Data silos

### 2.4 Vertical Recommendation

| Vertical | Demand | Why |
|----------|--------|-----|
| **Finance/Banking** | Highest | 85% using AI, compliance makes verification critical |
| **Healthcare** | High | Clinical accuracy is life-or-death, eval is regulatory necessity |
| **Government** | Growing | Compliance and auditability requirements |

**Post-event update (3/26):** Cortex Code is hyper-optimized for Snowflake (custom Rust dbt parser, Horizon catalog search, SQL/dbt verification via internal APIs). Their moat is Snowflake-specific tooling. Our opportunity: database-agnostic verification that works across Postgres, Snowflake, BigQuery. Finance/banking is the strongest v1 vertical — 85% AI adoption + compliance makes verification non-negotiable.

### 2.5 Pricing Strategy

- Self-serve: $200-500/mo for mid-market teams
- Enterprise: $50K-150K/yr
- Undercuts ThoughtSpot ($25-50/user/mo adds up fast), competes with Defog ($599/mo), adds eval layer neither has

### 2.6 Claude Agent SDK — Technical Foundation

The Agent SDK provides the right primitives for building this product:

**Core capabilities:**
- `query()` function with streaming responses, cost tracking, turn limits
- Custom tool definitions via `@tool` decorator — we define `query_db`, `inspect_schema`, `validate_result`
- Subagent patterns — specialist agents for analysis, verification, forecasting
- MCP integration — connect to Postgres, Snowflake, BigQuery via existing MCP servers
- Session management — multi-turn conversations with state persistence
- Permission model — restrict agent to read-only queries, block destructive operations

**Recommended architecture pattern:**
```
User query
  → Main Agent (orchestrator)
    → Subagent: Schema Inspector (understand the data)
    → Subagent: Query Builder (write SQL)
    → Subagent: Validator (re-read question, check query logic, verify results)
  → Return verified answer with confidence score
```

**Custom tools we'd build:**
| Tool | Purpose |
|------|---------|
| `query_db` | Execute SQL against connected database |
| `inspect_schema` | List tables, columns, types, sample data |
| `validate_result` | Re-run query with sanity checks, cross-reference |
| `explain_answer` | Generate human-readable explanation of how answer was derived |

**Database support in v1:**
- **PostgreSQL** (v1 target — broadest adoption, best MCP server, no vendor lock-in)
- Snowflake (v2 — enterprise demand confirmed at Cortex Code event, but they own that surface)
- BigQuery (v2 — GCP shops)
- Use existing MCP servers where available (`@modelcontextprotocol/server-postgres`)

### 2.7 Existing Data Agent Architectures

**Common pattern (LangChain SQL Agent, Defog):**
1. User asks question in natural language
2. Agent inspects database schema
3. Agent writes SQL query
4. Agent executes query
5. Agent formats results
6. Return to user

**What's missing:** Step 5.5 — verify the results are correct. Nobody does this.

**Our pattern adds verification:**
1. User asks question
2. Agent inspects schema
3. Agent writes SQL
4. Agent executes query
5. **Validator subagent re-reads the original question, checks if the SQL actually answers it, runs sanity checks (row counts, value ranges, null checks)**
6. If validation fails → retry with corrected query
7. Agent formats results with confidence score + explanation
8. Return to user

---

## 3. Architecture Section (Builder)

**[Builder to fill — Agent SDK integration, orchestration flow, tool definitions, eval/verification layer design]**

---

## 4. UX Section (Jackie)

**[Jackie to fill — chat-first interface, result presentation, confidence indicators, verified vs unverified states]**

---

## 5. Open Questions (pending event debrief)

1. **Which database to support first?** (Informed by: what do Cortex Code attendees use?)
2. **Visible or invisible verification?** (Informed by: what builds trust with users?)
3. **Who's the v1 customer?** (Informed by: who's at the event, what teams, what size?)
4. **Chat-first or API-first?**
5. **Pricing model — per query, per seat, or usage-based?**
6. **Open-source core or fully proprietary?**

---

## 6. MVP Scope (to be defined after debrief)

**What v1 does:**
- Connect to one database type
- Natural language → SQL → verified results
- Self-verification with confidence scores
- Chat interface

**What v1 does NOT do:**
- Multi-database joins
- Dashboard/visualization
- Scheduled reports
- Write operations (read-only in v1)
