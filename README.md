# Finch - Autonomous Wealth Assistant

A production-style multi-agent AI system that autonomously retrieves stock market data, answers portfolio questions using RAG, and generates weekly financial insights.

---

## Architecture
**Stack:** Python · FastAPI · Google Gemini · ChromaDB · yfinance · Railway

---

## Agents

| Agent | Responsibility |
|---|---|
| Orchestrator | Classifies intent, routes to specialist agents via tool-calling |
| Stock Market | Fetches real-time price, history, and company info via yfinance |
| Portfolio RAG | Retrieves user holdings from ChromaDB, reasons over portfolio context |
| Weekly Insight | Autonomously generates weekly portfolio report on a schedule |

---

## Key Concepts Demonstrated

- **Multi-agent orchestration** - agents as tools, bounded while-loop for sequential tool calls
- **RAG (Retrieval-Augmented Generation)** - ChromaDB vector store, semantic retrieval, query reformulation
- **Tool use / function calling** - LLM decides when and what to call; Python executes
- **Production patterns** - typed exceptions, input validation, retry/backoff, mocked tests
- **Autonomous scheduling** - Railway cron triggers `/insights/generate` weekly

---

## Project Structure
---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Send a message to the Orchestrator |
| POST | `/api/v1/insights/generate` | Trigger weekly insight generation |
| GET | `/api/v1/insights/latest` | Retrieve the latest insight report |

---

## Running Locally

```bash
# Clone and set up
git clone https://github.com/Shruusharma/Finch.git
cd Finch
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Run
uvicorn main:app --reload
# Visit http://localhost:8000/docs
```

---

## Testing

```bash
pytest tests/ -v
# Runs in under 2 seconds — all LLM calls are mocked
```

---

## Deployment

Deployed on Railway with:
- Environment variables set via Railway dashboard (no `.env` in production)
- `Procfile` defining the production start command
- Railway cron triggering `POST /insights/generate` every Monday at 9 AM UTC

---

## Architecture Decisions

See [`docs/architecture.md`](docs/architecture.md) for documented decisions and known limitations, including embedding model tradeoffs, ephemeral storage constraints, and rate limit mitigations.

---

## Author

Shruti Sharma - B.Tech CS, 2023–2027
