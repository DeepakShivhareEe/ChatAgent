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

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or for production with multiple workers:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

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

### SSL/TLS

Use Let's Encrypt with certbot or deploy behind a cloud load balancer with managed certificates.

### Environment Variables

In production, always set:
- `CORS_ORIGINS` to your specific domain(s)
- `ADMIN_API_KEY` to a strong, unique value
- `VITE_API_URL` to the public HTTPS URL of the backend before `docker compose up --build`
- `DEBUG=false`
- `RATE_LIMIT` to an appropriate value

The built browser bundle cannot use an internal Docker hostname such as
`http://backend:8000`; it must use a URL reachable from visitors' browsers.

### Scaling

- **Horizontal scaling**: Run multiple backend instances behind a load balancer. ChromaDB data must be shared (use a network volume or switch to a managed vector DB).
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
