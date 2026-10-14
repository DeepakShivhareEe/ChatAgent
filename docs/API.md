# API Reference

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### POST /chat

Process a user query through the RAG pipeline. Returns a streaming SSE response.

**Request Body:**
```json
{
  "query": "What features do you offer?",
  "conversation_id": "optional-uuid"
}
```

When a `conversation_id` is returned in the `meta` event, send it on the next
request. Conversation history is stored server-side; clients must not submit a
transcript.

**Response:** Server-Sent Events (SSE) stream.

| Event | Payload | Description |
|-------|---------|-------------|
| `meta` | `{ "type": "meta", "conversation_id": "uuid" }` | Conversation ID |
| `content` | `{ "type": "content", "content": "text chunk" }` | Streamed text |
| `sources` | `{ "type": "sources", "sources": ["doc.md"] }` | Source documents |
| `done` | `{ "type": "done" }` | Stream complete |
| `error` | `{ "type": "error", "message": "..." }` | Error occurred |

**Example with curl:**
```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the pricing?"}'
```

---

### POST /ingest

Trigger document ingestion from the knowledge directory.

**Headers:**
- `X-Admin-Key: your-admin-key` (required if `ADMIN_API_KEY` is set)

**Request Body:**
```json
{
  "directory": "./knowledge",
  "clear_existing": false
}
```

**Response:**
```json
{
  "status": "completed",
  "documents_processed": 5,
  "chunks_created": 42,
  "errors": []
}
```

---

### POST /search

Search the knowledge base directly (no LLM generation).
This diagnostic endpoint requires `X-Admin-Key`.

**Request Body:**
```json
{
  "query": "pricing plans",
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Pro Plan — $29/month...",
      "source": "pricing.md",
      "score": 0.8742,
      "metadata": { "source": "pricing.md", "chunk_index": 2 }
    }
  ],
  "query": "pricing plans",
  "total": 1
}
```

---

### GET /health

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### GET /status

Detailed system status.
This diagnostic endpoint requires `X-Admin-Key`.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "vector_db": {
    "type": "chromadb",
    "collection": "website_knowledge",
    "document_count": 42
  },
  "knowledge_base": {
    "directory": "./knowledge",
    "file_count": 5
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error description"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid request or injection detected |
| 403 | Missing or invalid admin API key |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | LLM provider error |

### What `detail` contains

On **4xx** responses `detail` is written for the user (validation, injection,
rate limit, auth). On **5xx** responses it is a generic message: upstream
provider text, internal paths and parser errors stay in the server log. The
log keeps the full error with credential-looking text masked (never API keys,
tokens or user message content). The streamed `error` event from `POST /chat`
follows the same rule.
