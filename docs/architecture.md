## Known Limitations

### Embedding Model: Semantic Ranking on Short Queries

**Model:** `all-MiniLM-L6-v2` (ChromaDB default, local, free)

**Issue:** For queries using indirect/colloquial terms (e.g., "my chip stock"
instead of "NVDA"), the model does not reliably rank the correct chunk #1,
even when the relevant keyword ("chip") is present in the chunk text.
Root cause: short queries vs. structurally-uniform long documents — the model
weighs sentence-shape similarity (shared financial boilerplate across all
chunks) over the single differentiating term.

**Impact:** Low. With a small portfolio (10-50 positions), top-K retrieval
(K=3-5) still surfaces the relevant chunk within the result set even if not
ranked first. The agent (Phase 6) receives all top-K chunks as context, so
the LLM can still identify the right position during reasoning.

**Production mitigation paths (not implemented, documented for interview):**
1. Switch to Gemini's embedding API (`text-embedding-004`) — larger model,
   better world-knowledge associations, costs ~$0.0001/1K tokens
2. Add an LLM re-ranking step: retrieve top-10 broadly, have the LLM
   re-rank/filter to top-3 before final generation
3. Hybrid search: combine vector similarity with keyword/BM25 search

**Decision:** Accepted for this project. The free local model is sufficient
given small portfolio size and top-K context injection. Re-ranking would be
the first upgrade if portfolio size grew significantly (100+ positions).

### Gemini Free Tier Rate Limits

`gemini-2.5-flash` has a very low free-tier daily request quota, and every
tool-calling turn consumes 2 requests (decide + final). Mitigated by:
1. Using `gemini-2.5-flash-lite` (higher free quota) for agent calls
2. Exponential backoff retry (3 attempts) via `tenacity` for transient 429s

Production note: a paid tier or self-hosted model would remove this
constraint entirely. This is a prototype-stage cost/quota tradeoff.

### Production Storage Limitations

Railway's filesystem is ephemeral — data written to disk (ChromaDB,
insight JSON) does not survive redeploys. Mitigations:
- ChromaDB: re-seeded from SAMPLE_PORTFOLIO on every startup (acceptable
  for a hardcoded demo portfolio; a real product would use a persistent
  vector DB service like Pinecone or Weaviate Cloud)
- Insight store: lost on redeploy; `/insights/latest` returns 404 until
  the cron fires. A real product would use Railway's Postgres plugin.