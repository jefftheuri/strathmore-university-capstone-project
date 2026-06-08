# SureRide — AI-Powered Ride Booking Agent

A capstone project for the AIPP programme at Strathmore University.

SureRide is a conversational AI agent that helps users safely book rides — targeting the drunk-driving problem in Kenya. The agent uses **LangGraph** for stateful multi-turn conversation, a **RAG knowledge base** (ChromaDB + Google Gemini) for FAQ answering, and a **Streamlit** WhatsApp-style chat interface.

---

## Project Structure

```
sureride-capstone/
├── langgraph_agent/       # LangGraph agent — state, nodes, graph
│   ├── state.py           # Agent state schema (TypedDict)
│   ├── nodes.py           # Graph nodes (greet, collect, confirm, rag_tool)
│   └── agent.py           # Graph compilation and entry point
├── rag/                   # RAG knowledge base
│   ├── ingest.py          # Chunk, embed, and store FAQ docs in ChromaDB
│   └── retriever.py       # Retriever wrapper used by the agent
├── ui/
│   └── app.py             # Streamlit WhatsApp-style chat UI
├── docs/                  # Written artefacts (governance doc, report)
├── .env                   # API keys (DO NOT COMMIT)
├── .env.example           # Template for .env
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Quick Start

### 1. Set up the environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure your API key
Copy `.env.example` to `.env` and set your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```
Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

### 3. Ingest the FAQ knowledge base
```bash
python rag/ingest.py
```

### 4. Run the Streamlit chat UI
```bash
streamlit run ui/app.py
```


---

## Tech Stack

- **Python 3.10+**
- **LangGraph / LangChain** — stateful agent orchestration
- **Google Gemini 1.5 Flash** — language model and embeddings
- **ChromaDB** — vector store for RAG
- **Streamlit** — WhatsApp-style chat UI + Operations Dashboard
- **PesaPal v3** — payment gateway (M-Pesa / Card)
- **python-dotenv** — environment variable management
