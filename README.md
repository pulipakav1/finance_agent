# FinAgent — Multi-Agent Stock Finance Chatbot

<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-4B0082?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-111827?style=flat-square&logo=chainlink&logoColor=white"/>
  <img src="https://img.shields.io/badge/GPT--4o-412991?style=flat-square&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white"/>
</p>

> A production-style multi-agent LLM system that routes
> finance queries to specialist agents via parallel fan-out —
> cutting query resolution time **~60%** vs. a single-agent
> baseline, with fault tolerance so partial agent failure
> never drops the full request.

---

## Demo

![FinAgent — main interface](image.png)

![FinAgent — chat, routing, and detail panels](<image copy.png>)

---

## Why Multi-Agent?

Single LLM agents struggle with complex finance queries —
they either miss context, hallucinate data, or take too long
chaining tool calls sequentially.

FinAgent solves this with a **LangGraph supervisor** that:
- Decomposes the query and routes to specialist agents **in parallel**
- Handles **partial agent failure** without dropping the full request
- Aggregates specialist outputs into a single coherent response
- Maintains **multi-turn memory** via MemorySaver + thread_id

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│           SUPERVISOR NODE               │
│  Decomposes query · Routes to agents   │
│  Extracts ticker symbols · JSON output  │
└────┬──────────┬──────────┬──────────────┘
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌───────────┐
│ ANALYST │ │  NEWS  │ │ PORTFOLIO │
│  NODE   │ │  NODE  │ │   NODE    │
│         │ │        │ │           │
│ create_ │ │create_ │ │  Direct   │
│ agent + │ │agent + │ │ tool use  │
│  tools  │ │  tools │ │           │
└────┬────┘ └───┬────┘ └─────┬─────┘
     │          │             │
     └──────────┴─────────────┘
                │
                ▼
     ┌──────────────────────┐
     │   AGGREGATOR NODE    │
     │  Synthesizes outputs │
     │  into final response │
     └──────────┬───────────┘
                ▼
              END
```

**Step by step:**
1. **Supervisor** — LLM returns structured JSON: routes, symbols, reasoning
2. **Conditional edges** — Fan-out to analyst, news, and/or portfolio nodes in parallel
3. **Analyst / News** — `create_agent` runs a LangGraph tool loop via OpenAI function calling
4. **Portfolio** — Direct tool calls for portfolio calculations
5. **Aggregator** — LLM merges all specialist outputs into one markdown reply
6. **MemorySaver** — Checkpointer + `thread_id` for persistent multi-turn sessions

---

## Key Technical Patterns

| Pattern | Location | Purpose |
|---|---|---|
| `StateGraph(AgentState)` | `graph_builder.py` | Shared typed state across all nodes |
| `add_messages` reducer | `state.py` | Append-only message history |
| Conditional edges (list → parallel) | `graph_builder.py` | Multi-agent fan-out |
| `MemorySaver` | `graph_builder.py` | Persistent conversation state |
| `create_agent` | `analyst_agent.py`, `news_agent.py` | Tool-calling sub-agent graphs |
| `@tool` decorators | `tools/*.py` | LangChain tool definitions |
| `JsonOutputParser` | `supervisor.py` | Structured supervisor routing |
| `thread_id` | `memory/conversation.py` | Session isolation per user |

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph · LangChain |
| LLM | GPT-4o (OpenAI) |
| Market Data | yfinance + deterministic mock fallback |
| UI | Streamlit — Bloomberg-style dark layout |
| Containerization | Docker · Docker Compose |
| Testing / CI | pytest · GitHub Actions |

---

## Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key
- Docker Desktop (optional)

### Local

```bash
git clone https://github.com/pulipakav1/finance_agent.git
cd finance_agent

python -m venv venv
source venv/bin/activate        # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements.txt

cp .env.example .env
# Add your OPENAI_API_KEY to .env

streamlit run app.py
```

Open **http://localhost:8501**

### Docker

```bash
docker compose up --build
```

Open **http://localhost:8501**

Without Compose:

```bash
docker build -t finance-agent .
docker run --rm -p 8501:8501 --env-file .env finance-agent
```

---

## Example Queries

```
"Analyze NVDA — full technical breakdown"
"Compare AAPL and MSFT — which looks stronger?"
"Latest news and sentiment for TSLA"
"Portfolio breakdown: AAPL:10, MSFT:5, NVDA:8, AMZN:12"
"Risk analysis for NVDA:20, AMD:15"
"META — technicals plus recent news"
```

---

## Project Structure

```
finance_agent/
├── app.py                 # Streamlit entrypoint
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── graph/
│   ├── state.py           # AgentState + reducers
│   ├── graph_builder.py   # StateGraph + MemorySaver
│   └── nodes.py           # All node implementations
├── agents/
│   ├── supervisor.py      # Query routing + JSON parsing
│   ├── analyst_agent.py   # create_agent (LangGraph)
│   ├── news_agent.py
│   └── agent_helpers.py
├── tools/                 # @tool functions
├── memory/
│   └── conversation.py    # Thread / session helpers
├── prompts/
│   └── templates.py
└── utils/
    └── mock_data.py       # Deterministic mock market data
```

---

## Testing

```bash
pytest -q
```

CI runs automatically on every push via `.github/workflows/ci.yml`

---

## Notes

- **Mock data** — Prices, news, and indicators use a
  deterministic mock layer by default. Replace
  `utils/mock_data.py` with live `yfinance` or
  Alpha Vantage calls for production use.
- **API costs** — GPT-4o is used by default. Switch
  to `gpt-4o-mini` in agent modules to reduce cost
  during development.
- **Disclaimer** — Educational demo, not investment advice.

---

## License

MIT — use and modify freely.

---

<p align="center">
  Built by <a href="https://linkedin.com/in/vishnurp1">Rohit Pulipaka</a>
  &nbsp;·&nbsp;
  <a href="mailto:pvishnurohit@gmail.com">pvishnurohit@gmail.com</a>
</p>
