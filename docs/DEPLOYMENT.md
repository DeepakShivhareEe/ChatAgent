# Deployment Guide

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env with your API key, a strong ADMIN_API_KEY, and the exact
# comma-separated CORS_ORIGINS that will host the widget.

# Set the browser-visible URL of the backend before building the demo container.
# Example (PowerShell): $env:VITE_API_URL = 'https://api.example.com'

# Build and start
docker-compose up -d --build

# Check health
curl http://localhost:8000/health

# Ingest knowledge base
curl -X POST http://localhost:8000/ingest
```

### Backend Only (Docker)

```bash
cd backend

# Build
docker build -t awa-backend .

# Run
docker run -d \
  --name awa-backend \
  -p 8000:8000 \
  -v $(pwd)/knowledge:/app/knowledge \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  awa-backend
```

---

## Manual Deployment

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env

# Run with uvicorn — run a SINGLE worker (see warning below)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> **Warning: run a single worker.** Rate limiting and conversation history are
> stored **in memory inside the process** (`app/security/rate_limiter.py`,
> `app/conversation/store.py`). With `--workers > 1`, each worker keeps its own
> counters and conversation state, so rate limiting becomes ineffective and
> users lose chat context whenever a request is handled by a different worker.
> To run more than one worker, first move rate limiting and conversation
> storage to a shared store such as Redis.

### Widget

```bash
cd widget

npm install
npm run build

# Serve the dist/ directory with any static file server
npx serve dist
```

---

## Production Considerations

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.yoursite.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

If (and only if) the backend runs behind that proxy, also set
`TRUST_PROXY_HEADERS=true` so the rate limiter can use the real client IP from
`X-Forwarded-For`. The proxy must overwrite that header (the nginx config above
does, via `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`).
With the default `false` the direct socket address is used and client-supplied
values are ignored — never enable it while the backend is reachable directly,
because any client can forge the header and slip past the per-IP limit.

### SSL/TLS

Use Let's Encrypt with certbot or deploy behind a cloud load balancer with managed certificates.

### Environment Variables

In production, always set:
- `CORS_ORIGINS` to your specific domain(s)
- `SITE_TOKENS` to one credential per embedding site — `site:token` or, preferably, `site:token:https://your-site.com|https://www.your-site.com` (this enforces `X-Site-Key` on `POST /chat`; leave empty only for local development)
- `DEBUG=true` **only** for local development — with `DEBUG=false` the backend refuses to start while `SITE_TOKENS` is empty, so `/chat` cannot be left open by accident
- `ADMIN_API_KEY` to a strong, unique value
- `VITE_API_URL` to the public HTTPS URL of the backend before `docker compose up --build`
- `EXPOSE_API_DOCS=false` (this hides `/docs`, `/redoc` and `/openapi.json`)
- `DEBUG=false`
- `RATE_LIMIT` to an appropriate value — it is enforced per site **and** client IP, so one busy site cannot consume another site's allowance
- `TRUST_PROXY_HEADERS=true` only when a trusted reverse proxy overwrites `X-Forwarded-For` (default `false`)

The built browser bundle cannot use an internal Docker hostname such as
`http://backend:8000`; it must use a URL reachable from visitors' browsers.

### Site keys and origin binding

The widget's key is delivered in the browser bundle, so anyone can read and
copy it. `SITE_TOKENS` therefore supports binding a token to the origins allowed
to use it:

```
# site:token                    — accepted from any origin (backward compatible)
# site:token:origin1|origin2    — accepted only from those origins
SITE_TOKENS=acme:key1:https://acme.com|https://shop.acme.com,beta:key2
```

A bound token requires a matching `Origin` header: a request from any other
origin, or with no `Origin` header at all, is refused with `403`. Tokens must not
contain `:` (the second colon starts the origin list). Origins are listed with
`|` and a trailing slash is ignored. Because `Origin` can be forged by a
non-browser client, origin binding protects against a copied key being reused
from someone else's website — it is not a substitute for a real secret.

### Scaling

- **Horizontal scaling**: Run multiple backend instances behind a load balancer. ChromaDB data must be shared (use a network volume or switch to a managed vector DB). **This also requires moving rate limiting and conversation history out of process memory into a shared store such as Redis** — otherwise each instance enforces its own limits and users lose chat context. Do not run multiple workers or instances until that shared store exists.
- **Managed vector DB**: For production at scale, replace ChromaDB with Pinecone, Qdrant, or Weaviate by implementing the same interface in `app/vectordb/`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated and dependencies installed |
| `chromadb` errors | Delete `data/chromadb/` and re-ingest |
| SSE not streaming | Ensure no buffering in your reverse proxy (see Nginx config above) |
| Rate limit issues | Increase `RATE_LIMIT` in `.env` or whitelist IPs |
| Provider errors | Verify `API_KEY` and `MODEL_NAME` are correct for your provider |
