# AI Website Assistant Platform

A **production-ready, provider-agnostic AI chatbot platform** that integrates into any live website. Built with FastAPI, RAG pipeline, ChromaDB, and a React/TypeScript chat widget.

```text
Live Website
      │
      ▼
Reusable Chat Widget (React component + script-tag Web Component)
      │
      ▼
FastAPI Backend (REST API + SSE Streaming)
      │
      ▼
RAG Engine (Retrieve → Build Context → Generate)
      │
      ▼
Vector Database (ChromaDB)
      │
      ▼
LLM Provider Layer
      ├── OpenAI
      ├── Anthropic Claude
      ├── Google Gemini
      ├── Groq
      ├── OpenRouter
      └── (Extensible)
```

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API key and provider

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Ingest Knowledge Base

Place your website documents (`.md`, `.html`, `.pdf`, `.docx`, `.json`, `.txt`) in the `backend/knowledge/` directory, then:

```bash
curl -X POST http://localhost:8000/ingest
```

### 3. Widget Setup

```bash
cd widget

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` to see the demo page with the chat widget.

### Embed in Any Website

Build a framework-independent widget bundle:

```bash
cd widget
npm run build
```

Host `dist/ai-website-assistant.iife.js`, then add this to any modern website:

```html
<script src="https://cdn.example.com/ai-website-assistant.iife.js" defer></script>
<ai-website-assistant api-url="https://api.example.com"></ai-website-assistant>
```

See the [Integration Guide](docs/INTEGRATION.md) for configuration attributes.

---

## Features

### Backend
- **Multi-provider LLM support** — OpenAI, Anthropic, Gemini, Groq, OpenRouter
- **RAG pipeline** — retrieval-augmented generation with anti-hallucination guardrails
- **Document ingestion** — Markdown, HTML, PDF, DOCX, JSON, TXT
- **Vector search** — ChromaDB with cosine similarity
- **Streaming responses** — Server-Sent Events (SSE)
- **Security** — prompt injection detection, input sanitization, rate limiting
- **Clean REST API** — `/chat`, `/ingest`, `/search`, `/health`, `/status`

### Widget
- **Floating chat button** with pulse animation
- **Dark and light mode** with system preference detection
- **Streaming markdown** rendering
- **Code blocks** with syntax highlighting and copy button
- **Suggested prompts** for easy onboarding
- **Multi-turn conversations** with history
- **Responsive design** (desktop + mobile)
- **Framework-independent embed** — HTML, CMS, React, Vue, Angular, and no-code sites
- **Micro-animations** using Motion

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API.md) | Full REST API documentation |
| [Deployment Guide](docs/DEPLOYMENT.md) | Docker, production deployment |
| [Integration Guide](docs/INTEGRATION.md) | Adding the widget to your website |

---

## Project Structure

```
chatbot/
├── backend/              # FastAPI backend service
│   ├── app/
│   │   ├── main.py       # App entry point
│   │   ├── config.py     # Environment configuration
│   │   ├── api/          # REST API routes
│   │   ├── providers/    # LLM provider abstraction
│   │   ├── rag/          # RAG pipeline
│   │   ├── ingestion/    # Document ingestion
│   │   ├── vectordb/     # ChromaDB wrapper
│   │   ├── security/     # Sanitization, injection detection
│   │   └── models/       # Pydantic schemas
│   ├── tests/            # Unit tests
│   ├── knowledge/        # Knowledge base documents
│   └── requirements.txt
├── widget/               # React chat widget
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── hooks/        # React hooks
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript types
│   │   └── styles/       # CSS
│   └── package.json
├── docs/                 # Documentation
└── docker-compose.yml
```

---

## Switching AI Providers

Update your `.env` file:

```bash
# OpenAI
AI_PROVIDER=openai
API_KEY=sk-...
MODEL_NAME=gpt-4o-mini

# Anthropic
AI_PROVIDER=anthropic
API_KEY=sk-ant-...
MODEL_NAME=claude-3-5-sonnet-20241022

# Google Gemini
AI_PROVIDER=gemini
API_KEY=AIza...
MODEL_NAME=gemini-2.0-flash

# Groq
AI_PROVIDER=groq
API_KEY=gsk_...
MODEL_NAME=llama-3.1-70b-versatile

# OpenRouter
AI_PROVIDER=openrouter
API_KEY=sk-or-...
MODEL_NAME=anthropic/claude-3.5-sonnet
```

Restart the backend. No code changes required.

---

## License

MIT
