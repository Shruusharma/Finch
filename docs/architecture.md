# Finch Autonomous Wealth Assistant — Architecture Document

**Version:** 1.0  
**Last Updated:** June 2026  
**Status:** Deployed (prototype stage)  
**Live URL:** https://finch-production-95c79.up.railway.app

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Responsibilities](#component-responsibilities)
4. [Data Flow](#data-flow)
5. [Technology Decisions](#technology-decisions)
6. [Portfolio Data Architecture](#portfolio-data-architecture)
7. [Agent Design Patterns](#agent-design-patterns)
8. [API Reference](#api-reference)
9. [Known Limitations](#known-limitations)
10. [Future Improvements](#future-improvements)

---

## System Overview

Finch is a multi-agent autonomous wealth assistant. A user sends a natural-language
message to a FastAPI backend, which routes it through an Orchestrator agent. The
Orchestrator uses LLM-driven tool-calling to decide which specialist agent handles
the request — the Stock Market Agent (real-time market data via yfinance) or the
Portfolio RAG Agent (semantic retrieval over portfolio positions via ChromaDB).

A Weekly Insight Agent runs autonomously on a Railway cron schedule, generating
structured portfolio summary reports without any user prompt.

The system is intentionally designed to demonstrate:

- Multi-agent orchestration with LLM-based routing
- Tool use / function calling from first principles (no framework abstraction)
- Retrieval-Augmented Generation (RAG) for private, structured portfolio data
- Autonomous agent behavior (scheduled, non-request-driven execution)
- Production-grade backend patterns (versioned API, typed errors, retry logic, tests)

---

## Architecture Diagram

```
Client (HTTP)
      │
      ▼
┌─────────────────────────────────┐
│  FastAPI Gateway                │
│  /api/v1/chat                   │
│  /api/v1/insights/*             │
│  /health                        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Orchestrator Agent             │
│  (LLM-based intent routing)     │
│  Tools: ask_stock_agent,        │
│          ask_portfolio_agent    │
└──────┬───────────────┬──────────┘
       │               │
       ▼               ▼
┌────────────┐  ┌───────────────────┐
│  Stock     │  │  Portfolio RAG    │
│  Market    │  │  Agent            │
│  Agent     │  │  Tool:            │
│  Tools:    │  │  search_portfolio │
│  price,    │  │  (ChromaDB)       │
│  history,  │  └────────┬──────────┘
│  company   │           │
└─────┬──────┘           ▼
      │         ┌─────────────────┐
      ▼         │  ChromaDB       │
┌──────────┐    │  Vector Store   │
│ yfinance │    │  (portfolio     │
│ (market  │    │   embeddings)   │
│  data)   │    └─────────────────┘
└──────────┘

Railway Cron (Monday 9AM UTC)
      │
      ▼
┌─────────────────────────────────┐
│  Weekly Insight Agent           │
│  (autonomous, no user input)    │
│  Reuses: ask_stock_agent,       │
│           ask_portfolio_agent   │
│  Output: data/latest_insight    │
└─────────────────────────────────┘
```

---

## Component Responsibilities

### FastAPI Gateway (`main.py`, `api/`)

Handles all HTTP concerns: routing, request validation (Pydantic), versioning
(`/api/v1`), and error translation. The gateway knows about agents but has no
knowledge of LLMs, tools, or schemas — it is a thin pass-through layer.

Registers a startup event (`@app.on_event("startup")`) to seed ChromaDB with
portfolio data before accepting traffic.

### Orchestrator Agent (`agents/orchestrator.py`)

The top-level routing agent. Receives every user message and uses LLM tool-calling
to decide which specialist agent(s) to invoke. Runs a bounded multi-tool loop
(`MAX_TOOL_ITERATIONS = 5`) allowing sequential calls to multiple agents before
producing a final answer.

The Orchestrator's tools are other agents (`ask_stock_agent`, `ask_portfolio_agent`)
— they are registered in `core/tool_executor.py` exactly like any other tool. The
Orchestrator does not know whether a "tool" calls an external API or another LLM
agent internally.

### Stock Market Agent (`agents/stock_agent.py`)

Specialist agent scoped to publicly-available market data. Has three tools:

- `get_stock_price` — current price, currency, company name
- `get_stock_history` — price trend over N days (start/end date range)
- `get_company_info` — sector, industry, market cap, business summary

All three are backed by `yfinance`. System prompt explicitly guards against
answering non-market questions to prevent incorrect routing causing silent failures.

### Portfolio RAG Agent (`agents/portfolio_agent.py`)

Specialist agent scoped to the user's portfolio holdings. Has one tool:

- `search_portfolio` — semantic similarity search over ChromaDB-stored portfolio chunks

The tool's description instructs the LLM to reformulate vague queries into richer
search terms before querying (e.g., "my chip stocks" → "semiconductor AI chip
positions"), compensating for the local embedding model's limited world-knowledge
associations. See [Portfolio Data Architecture](#portfolio-data-architecture) for
full detail on the current implementation scope and limitations.

### Weekly Insight Agent (`agents/insight_agent.py`)

Autonomous agent triggered by Railway's cron scheduler, not by user requests.
Constructs its own prompt from `SAMPLE_PORTFOLIO` tickers, reuses the Orchestrator's
toolset (`ORCHESTRATOR_TOOLS`), and generates a structured weekly report covering
portfolio positions and 7-day performance for each holding.

Output is persisted to `data/latest_insight.json` and served via
`GET /api/v1/insights/latest`. The generate and read endpoints are intentionally
separated to avoid paying LLM generation costs on every read.

### Core LLM Client (`core/llm_client.py`)

Wraps the `google.genai` SDK. All agents call `call_llm()` — no agent imports the
SDK directly. This abstraction layer was validated during development when Google
deprecated `google-generativeai` in favour of `google.genai`; the migration was
contained entirely to this one file.

Key behaviours:

- Bounded `for` loop over `MAX_TOOL_ITERATIONS` (not `while True`) — safety and cost guard
- Exponential backoff retry via `tenacity` on `ClientError` (covers 429 rate limits)
- Raises typed `LLMQuotaError` after all retries are exhausted

### Tool Executor (`core/tool_executor.py`)

Registry pattern mapping tool name strings to Python callables. Agents and the
Orchestrator call `execute_tool(name, args)` without importing tool functions
directly. Adding a new tool requires one dict entry here — no other files change.

Agent-wrapper tools (`ask_stock_agent`, `ask_portfolio_agent`) use lazy imports
inside the function body to avoid a module-level circular dependency:
`llm_client → tool_executor → agent_tools → stock_agent → llm_client`.

---

## Data Flow

### Standard single-agent request ("What is AAPL trading at?")

```
1. POST /api/v1/chat  { message: "What is AAPL trading at?" }
2. orchestrator.handle(message)
3. call_llm(messages, tools=[ORCHESTRATOR_TOOLS])          — LLM call 1
4. LLM returns: function_call { name: "ask_stock_agent", args: {query: "..."} }
5. execute_tool("ask_stock_agent", {query: "..."})
     → stock_agent.handle(query)
     → call_llm(messages, tools=[STOCK_TOOLS])              — LLM call 2
     → LLM returns: function_call { get_stock_price, {ticker: "AAPL"} }
     → execute_tool("get_stock_price", {ticker: "AAPL"})
     → yfinance returns { price: 229.50, ... }
     → call_llm(messages + tool_result)                     — LLM call 3
     → LLM returns: "AAPL is trading at $229.50"
6. Orchestrator receives { response: "AAPL is trading at $229.50" }
7. call_llm(messages + agent_result)                        — LLM call 4
8. LLM returns final response text
9. HTTP 200 { response: "...", agent_used: "orchestrator" }
```

**Total LLM calls: 4**

### Multi-agent request ("Should I buy more NVDA given my current position?")

```
Iter 1: Orchestrator → ask_portfolio_agent
            Portfolio Agent → search_portfolio (ChromaDB)
            Portfolio Agent → final answer text
Iter 2: Orchestrator → ask_stock_agent
            Stock Agent → get_stock_price / get_stock_history
            Stock Agent → final answer text
Iter 3: Orchestrator → no tool call → final synthesised answer
```

**Total LLM calls: up to 6**

### Autonomous weekly insight generation

```
Railway Cron (Monday 09:00 UTC)
      → POST /api/v1/insights/generate
      → insight_agent.generate_weekly_insight()
      → Constructs prompt from SAMPLE_PORTFOLIO tickers
      → call_llm loop (up to MAX_TOOL_ITERATIONS):
            ask_portfolio_agent (retrieves all positions)
            ask_stock_agent × N (one per holding, 7-day history)
      → save_insight(report)  →  data/latest_insight.json
```

---

## Technology Decisions

### FastAPI over Flask or Django

FastAPI provides automatic OpenAPI/Swagger documentation, Pydantic-native request
validation, and async support out of the box. For an agent backend where every
endpoint is a pass-through to LLM calls, async is the correct model — the server
should not block a thread during multi-second LLM round-trips.

### Google Gemini (`gemini-2.5-flash-lite`) over Anthropic Claude

The project was initially designed with the Anthropic SDK. Switched to Gemini at
Phase 2 due to cost: Anthropic has no free tier; Gemini's free tier provides 20
requests/day per model. `gemini-2.5-flash-lite` was chosen over `gemini-2.5-flash`
because it has a higher free-tier daily request quota, which matters given that
tool-calling multi-agent requests consume 4–6 LLM calls each.

The `core/llm_client.py` abstraction layer means this decision is reversible — a
model or vendor switch is a one-file change.

### ChromaDB over Pinecone or Weaviate

ChromaDB runs locally with no external service dependency, has no API key
requirement, and bundles `all-MiniLM-L6-v2` as a default embedding model. For a
prototype demonstrating RAG architecture, this keeps the system entirely self-
contained. The `PersistentClient` mode writes to `./chroma_data/` on disk, so
embeddings survive process restarts (though not Railway redeploys — see Known
Limitations).

### yfinance over a paid market data API

Free, no API key, adequate data quality for demonstration purposes. Sufficient for
current price, historical OHLCV, and company metadata. For production use, a
regulated financial data provider (e.g., Polygon.io, Alpha Vantage, or a brokerage
API) would be required.

### Railway over AWS, GCP, or Heroku

Railway provides Git-based deployment, environment variable management, and a
built-in cron scheduler — all three are required by this project. The cron
scheduler specifically allows the Weekly Insight Agent to be triggered as an
external HTTP call (the correct architectural pattern) without a third-party
service. Setup time is significantly lower than AWS/GCP for a single-service
deployment.

### RAG as a tool (Pattern B) over always-retrieve (Pattern A)

Two RAG wiring patterns were considered:

- **Pattern A:** Always retrieve portfolio context before every LLM call
- **Pattern B:** Expose retrieval as a tool the LLM decides to call

Pattern B was chosen because: (1) it avoids wasting retrieval calls on queries
that don't require portfolio context (greetings, general market questions); (2) it
lets the LLM reformulate the query into better search terms before querying the
vector store; (3) it reuses the identical tool-calling infrastructure already built
for yfinance — no new code paths. The retrieval quality improvement from LLM query
reformulation also directly mitigates the local embedding model's limited world-
knowledge associations.

---

## Portfolio Data Architecture

### Current Implementation

The Portfolio RAG Agent currently operates on a **sample/demo portfolio** consisting
of three hardcoded positions:

| Ticker | Shares | Cost Basis | Sector |
|--------|--------|------------|--------|
| NVDA   | 50     | $120.00    | Technology — Semiconductors, AI chips, GPUs |
| AAPL   | 30     | $175.00    | Technology — Consumer electronics, smartphones |
| TSLA   | 15     | $250.00    | Automotive — Electric vehicles, energy storage |

These positions are defined in `memory/portfolio_data.py` and loaded into ChromaDB
at server startup via `@app.on_event("startup")` in `main.py`. Each position is
stored as a single text chunk (the unit of RAG retrieval) containing ticker,
shares, cost basis, sector, industry, and personal notes.

### What the Current Implementation Demonstrates

The sample portfolio was intentionally chosen to showcase the agent architecture
and RAG workflow, not to simulate real user portfolio management. Specifically, it
demonstrates:

- **Semantic retrieval over private structured data** — the core RAG pattern,
  applied to portfolio positions rather than documents
- **Agent reasoning over retrieved context** — the Portfolio RAG Agent uses
  retrieved chunks to answer portfolio questions, cross-referencing with live
  market data from the Stock Agent when needed
- **RAG pipeline mechanics** — chunking strategy, embedding, upsert idempotency,
  top-K retrieval, query reformulation
- **Multi-agent synthesis** — the Orchestrator combining portfolio context and
  live market data to answer compound questions (e.g., buy/sell analysis)

The three tickers were selected to cover distinct sectors (technology/semiconductors,
consumer tech, automotive/EV) to demonstrate semantic differentiation in retrieval.
Personal notes per position (e.g., "considering trimming if it rallies above 300"
for TSLA) demonstrate that the agent reasons over unstructured qualitative context,
not just numerical data.

### What the Current Implementation Does Not Support

The current system does **not** include:

- **User authentication** — there is no login, session management, or user identity
- **Portfolio creation or editing** — users cannot add, update, or remove positions
  via the API or any interface
- **Multi-user portfolio isolation** — all requests share the same single sample
  portfolio; there is no per-user data separation
- **Persistent user data storage** — no database (relational or otherwise) stores
  user-owned portfolio data beyond the seeded sample
- **Brokerage or open banking integration** — portfolio data is not sourced from
  any live financial account

Any query answered by the Portfolio RAG Agent reflects the sample portfolio data
only. This is clearly the intended scope for the current prototype stage.

### Chunking Strategy

Each portfolio position is stored as one ChromaDB document (one embedding vector).
This "one chunk per position" strategy was chosen because:

1. Each position is a self-contained semantic unit — ticker, quantity, cost basis,
   and notes belong together
2. The natural query granularity is the position — users ask "what's my NVDA
   position?", not "what's in half of my NVDA position notes?"
3. Chunking more finely (per sentence) would fragment context; chunking more
   coarsely (whole portfolio as one chunk) would defeat retrieval entirely

### Embedding Model and Retrieval Limitations

ChromaDB's default embedding model (`all-MiniLM-L6-v2`, 22M parameters) is used
for both ingestion and query embedding. This model provides good semantic
paraphrase matching but has limited world-knowledge associations for short queries
against structurally-uniform documents.

**Known gap:** The query "How is my chip stock doing?" does not reliably rank the
NVDA chunk first, even with "AI chips" present in the chunk text. The model weighs
structural similarity (all chunks share the same financial boilerplate format)
over the single differentiating keyword.

**Mitigation in place:** The `search_portfolio` tool's description explicitly
instructs the LLM to reformulate vague queries into richer search terms before
querying (e.g., "chip stock" → "semiconductor AI chip positions"). Because the
Orchestrator and Portfolio Agent are themselves LLMs with world knowledge, they
can bridge the association gap that the embedding model cannot.

**Production mitigation paths** (not implemented):
1. Switch to Gemini's `text-embedding-004` API — larger model, stronger world-
   knowledge associations, ~$0.0001/1K tokens
2. Add an LLM re-ranking step: retrieve top-10 broadly, LLM filters to top-3
3. Hybrid search: combine vector similarity with BM25 keyword scoring

---

## Agent Design Patterns

### Uniform Agent Interface

Every specialist agent exposes a single public function:

```python
def handle(message: str) -> str
```

The Orchestrator calls `stock_agent.handle(query)` and `portfolio_agent.handle(query)`
identically. Agents are interchangeable from the Orchestrator's perspective.

Exception: `insight_agent.generate_weekly_insight()` deliberately does not follow
this signature — it has no `message` parameter because it is autonomously triggered,
not responding to user input. Interface shape reflects invocation method.

### Tool Registry Pattern

`core/tool_executor.py` maintains a dict mapping tool name strings to Python
callables. `execute_tool(name, args)` performs a dict lookup and calls the function.

Benefits over `if/elif` chains: O(1) lookup, adding a tool is one dict entry,
agent-wrapper tools and API-wrapper tools are indistinguishable at the registry
level.

### Bounded Tool Loop

`call_llm` iterates `for iteration in range(MAX_TOOL_ITERATIONS)` rather than
`while True`. On each iteration, if the LLM returns plain text (no function call),
the loop exits and returns the text. If `MAX_TOOL_ITERATIONS` is reached without
a text response, a user-facing fallback message is returned.

This is a safety and cost bound: a confused LLM or buggy tool cannot create an
infinite loop. Each iteration is a paid API call.

### Lazy Imports for Circular Dependency

`agents/agent_tools.py` imports `stock_agent` and `portfolio_agent` inside the
function body rather than at module level. This resolves the circular import:
`llm_client → tool_executor → agent_tools → stock_agent → llm_client`.

At function call time, all modules are fully initialised and cached in `sys.modules`.
The import statement resolves instantly against the cache — no re-execution occurs.

### Error Handling Architecture

Domain exceptions (`AgentError`, `LLMQuotaError`, `InsightNotFoundError`) extend
`FinchError`. Business logic raises typed domain exceptions; a single FastAPI
exception handler in `main.py` translates them to HTTP responses with a consistent
JSON shape: `{"error": "ExceptionClassName", "detail": "..."}`.

This separates concerns: agents and tools have no knowledge of HTTP status codes.
The translation layer maps `LLMQuotaError` to 429, `AgentError` to 502, and
`InsightNotFoundError` to 404 — matching the semantic intent of each HTTP code.

---

## API Reference

### `GET /health`

Returns server status. Does not require API key. Used by Railway for health checks.

```json
{ "status": "ok", "app": "Finch", "env": "production" }
```

### `POST /api/v1/chat`

Main conversational endpoint. Routes through the Orchestrator.

**Request:**
```json
{ "message": "What is AAPL trading at?", "session_id": "optional-string" }
```

Validation: `message` must be non-empty and ≤ 2000 characters.

**Response:**
```json
{ "response": "AAPL is currently trading at $229.50.", "session_id": "...", "agent_used": "orchestrator" }
```

**Error responses:**
- `422` — Pydantic validation failure (empty message, too long)
- `429` — Gemini API quota exhausted
- `500` / `502` — Agent or unexpected error

### `POST /api/v1/insights/generate`

Triggers a new weekly insight report. Intended to be called by Railway's cron
scheduler. Can be called manually for testing. This endpoint is expensive — it
triggers multiple LLM calls.

**Response:**
```json
{ "status": "generated", "report": "..." }
```

### `GET /api/v1/insights/latest`

Returns the most recently generated insight report. Cheap — reads from
`data/latest_insight.json`. Returns `404` if no report has been generated yet.

```json
{ "generated_at": "2026-06-16T09:00:00+00:00", "report": "..." }
```

### `GET /docs`

Auto-generated Swagger UI (FastAPI). Interactive — requests can be sent directly
from the browser.

---

## Known Limitations

### 1. Gemini Free Tier Rate Limits

**Model:** `gemini-2.5-flash-lite`  
**Limit:** 20 requests/day (free tier)  
**Impact:** Tool-calling requests consume 2 LLM calls per turn; multi-agent
requests consume 4–6. Heavy development or testing sessions can exhaust the daily
quota.

**Mitigations in place:**
- `gemini-2.5-flash-lite` chosen over `gemini-2.5-flash` for higher free quota
- Exponential backoff retry (3 attempts, 2–60s wait) via `tenacity`
- Test suite mocks `call_llm` — zero quota cost per test run

**Production path:** Paid Gemini tier removes this constraint entirely. The model
string is a single constant in `core/llm_client.py`.

---

### 2. Embedding Model Semantic Ranking

**Model:** `all-MiniLM-L6-v2` (ChromaDB default, local, 22M parameters)  
**Issue:** Short queries using indirect language ("chip stock", "EV position") do
not reliably rank the correct portfolio chunk first against structurally-uniform
documents.  
**Root cause:** The model weights sentence-shape similarity (shared financial
boilerplate across all chunks) over a single differentiating semantic keyword.

**Mitigation in place:** LLM query reformulation via tool description instructions.  
**Production paths:** Gemini embedding API, LLM re-ranking, hybrid BM25 + vector.

---

### 3. Ephemeral Railway Filesystem

Railway's container filesystem is ephemeral — data written to disk is lost on
redeploy or restart.

**ChromaDB (`./chroma_data/`):** Mitigated by re-seeding from `SAMPLE_PORTFOLIO`
on every startup. Acceptable because the sample portfolio is source-controlled —
the data source is the code, not the database. Adds ~1–2 seconds to cold start.

**Insight store (`./data/latest_insight.json`):** Lost on redeploy. `GET
/api/v1/insights/latest` returns 404 until the next cron trigger.

**Production path:** Railway's managed Postgres plugin for the insight store;
a managed vector DB service (Pinecone, Weaviate Cloud) for ChromaDB.

---

### 4. Sample Portfolio Only — No User Portfolio Management

As detailed in [Portfolio Data Architecture](#portfolio-data-architecture), the
current implementation uses a hardcoded three-position sample portfolio. There is
no user authentication, portfolio CRUD, or multi-user data isolation.

This is an intentional prototype-stage scope decision, not an oversight. The system
demonstrates agent orchestration, RAG retrieval, and portfolio reasoning workflows
at full architectural depth — user management is a separate engineering concern
orthogonal to the agent architecture being showcased.

**Production path:** See [Future Improvements](#future-improvements).

---

### 5. No Conversation Memory Across Turns

Each request to `POST /api/v1/chat` is stateless — the LLM receives only the
current message, not conversation history. Follow-up questions that depend on prior
context ("what about TSLA?" after discussing NVDA) are not supported.

`session_id` is accepted in the request schema and stored in the response but is
not yet wired to a session memory store.

**Production path:** Store conversation history per `session_id` in Redis or
Postgres; prepend the last N turns to each `call_llm` invocation.

---

## Future Improvements

The following improvements represent the natural next evolution of this system
toward a production-ready, multi-user wealth assistant. They are listed in
approximate implementation priority order.

### 1. User Authentication and Session Management

Introduce user identity as a first-class concern:

- JWT-based authentication (FastAPI's `python-jose` + `passlib`)
- User registration and login endpoints
- Session tokens tied to `session_id` for conversation continuity
- All portfolio data scoped to authenticated user identity

This is a prerequisite for every other improvement below.

### 2. Portfolio Creation and Management

Replace the hardcoded `SAMPLE_PORTFOLIO` with a user-owned, mutable data store:

- `POST /api/v1/portfolio/positions` — add a position
- `PUT /api/v1/portfolio/positions/{ticker}` — update shares, cost basis, notes
- `DELETE /api/v1/portfolio/positions/{ticker}` — remove a position
- `GET /api/v1/portfolio` — retrieve the full portfolio

When a user modifies a position, the corresponding ChromaDB chunk is re-embedded
and upserted automatically (the `upsert` idempotency built in Phase 5 supports
this with no changes to the vector store layer).

### 3. Persistent Database Storage

Replace file-based and in-memory storage with a managed relational database:

- **Portfolio positions:** Postgres table (`user_id`, `ticker`, `shares`,
  `cost_basis`, `notes`, `updated_at`)
- **Insight reports:** Postgres table (`user_id`, `generated_at`, `report`) —
  enables insight history, not just latest
- **Conversation history:** Postgres or Redis, keyed by `session_id`

Railway's managed Postgres plugin can be added with no application infrastructure
changes — only `config.py` and the storage modules require updating.

### 4. Multi-User Portfolio Isolation

Extend ChromaDB to support per-user collection namespacing:

```python
collection = client.get_or_create_collection(name=f"portfolio_{user_id}")
```

Each user's portfolio embeddings are stored in a separate collection, ensuring
semantic search is scoped to the authenticated user's data only.

### 5. Conversation Memory

Wire `session_id` to a conversation history store:

- Each `POST /api/v1/chat` call appends the user message and assistant response
  to the session history
- The last N turns are prepended to the `messages` list in `call_llm`
- Sessions expire after a configurable TTL (e.g., 24 hours)

This transforms the system from a single-turn Q&A interface into a genuinely
conversational assistant.

### 6. Brokerage and Open Banking Integration

Enable automatic portfolio ingestion from live financial accounts:

- **Open banking APIs** (e.g., Plaid, TrueLayer, Salt Edge) for bank account
  and investment account data across European and US markets
- **Brokerage APIs** (e.g., Interactive Brokers, Alpaca, Robinhood) for direct
  position and transaction data
- **Automatic re-embedding** on portfolio sync — positions added or changed
  trigger ChromaDB upsert automatically

This is the integration that moves the system from "demo portfolio" to "live
personal finance assistant" and is the core of Finch's stated product vision
(open banking + intelligent AI for total wealth tracking).

### 7. Stronger Embedding Model

Replace `all-MiniLM-L6-v2` with Gemini's `text-embedding-004` model via the
`google.genai` SDK. The same `memory/vector_store.py` interface is maintained;
only the ChromaDB collection initialisation changes (swap the default embedding
function for a Gemini-backed one).

This resolves the semantic ranking limitation documented in Known Limitations §2
and improves retrieval quality for colloquial portfolio queries.

### 8. Observability and Cost Tracking

Add structured logging and metrics:

- Per-request LLM call count and token usage (track `MAX_TOOL_ITERATIONS` hit rate)
- Agent routing distribution (what % of requests go to Stock vs Portfolio Agent)
- Latency per agent and per tool call
- Daily quota consumption tracking with proactive alerting before exhaustion

Tools: Railway's built-in log drain, or a lightweight integration with
Langfuse or Helicone for LLM-specific observability.

---

*This document is maintained alongside the codebase and updated as architectural
decisions are made or revised. For implementation details, see inline comments in
the referenced source files.*
